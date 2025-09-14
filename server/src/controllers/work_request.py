from math import floor
from random import shuffle
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep
import traceback
from typing import Any, Dict, List, Tuple, Union

from controllers.model import ModelController
from controllers.work_request_worker import WorkRequestWorker
from library.process_lock import ProcessLock
from objects.work_request import WorkRequest, WorkRequestStatus
from python_framework.graceful_killer import GracefulKiller, KillInstance

from python_framework.thread_safe_list import ThreadSafeList
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from config.application_config import ApplicationConfig
from db.daos.work_request import WorkRequestDAO, WorkRequestQuery, WorkRequestRecord
from python_framework.time import utc_now, now_delta

from db.daos.work_request_stats import (
    WorkRequestStatsDAO,
    WorkRequestStatsQuery,
    WorkRequestStatsRecord,
)
from objects.work_request_stats import (
    WorkRequestStatsFilterData,
    WorkRequestStatsModel,
)
from controllers.server import ServerController


class WorkRequestControllerKillInstance(KillInstance):
    def kill(self):
        WorkRequestController.instance().kill()


class WorkRequestController(Thread):

    WORKER_LOADBALANCE_WAIT_TIME = 20
    NUM_WORKERS = 4

    _instance: "WorkRequestController" = None

    _logger_key: str = None
    _kill_event: Event

    _process_lock: ProcessLock

    _workers: ThreadSafeList[WorkRequestWorker]

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "WorkRequestController"
        self._kill_event = Event()

        self._process_lock = ProcessLock()
        self._workers = ThreadSafeList()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "WorkRequestController":
        if WorkRequestController._instance is not None:
            return WorkRequestController._instance

        WorkRequestController._instance = WorkRequestController()
        GracefulKiller.instance().register_kill_instance(
            WorkRequestControllerKillInstance()
        )

        return WorkRequestController._instance

    @staticmethod
    def instance() -> "WorkRequestController":
        return WorkRequestController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def create_request(self, work_request: WorkRequest) -> Union[WorkRequest, None]:
        ContextLogger.debug(self._logger_key, "Inserting new WorkRequest...")

        try:
            work_request.request_status = WorkRequestStatus.QUEUED
            work_request.request_date = utc_now()
            results: List[WorkRequestRecord] = WorkRequestDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **work_request.to_record().generate_insert_query_args(),
            )

            if results is None or len(results) == 0:
                raise Exception("Insert returned zero records")

            new_work_request = WorkRequest.init_from_record(results[0])

            ContextLogger.debug(
                self._logger_key,
                "WorkRequest inserted, new id = [%s]" % new_work_request.id,
            )

            return new_work_request
        except:
            error_str = "Failed to insert WorkRequest, error = [%s]" % (
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return None

    def _update_request(self, work_request: WorkRequest, expected_server_id: str | None = None) -> Union[WorkRequest, None]:
        ContextLogger.debug(
            self._logger_key,
            "Persisting WorkRequest update with id [%s]..." % work_request.id,
        )

        results: List[WorkRequestRecord] = WorkRequestDAO.execute_update(
            ApplicationConfig.instance().database_config,
            **work_request.to_record().generate_update_query_args(),
            expected_server_id=expected_server_id
        )

        if results is None or len(results) == 0:
            raise Exception("Update returned zero records")

        new_work_request = WorkRequest.init_from_record(results[0])

        ContextLogger.debug(
            self._logger_key,
            "WorkRequest update persisted with id = [%s]" % work_request.id,
        )

        return new_work_request

    def update_request(
        self,
        work_request: WorkRequest,
        enforce_same_session_id: bool = False,
        enforce_same_server_id: bool = True,
        expect_null_server_id: bool = False, # for first time update
        retry_count: int = 0,
    ) -> Union[WorkRequest, None]:
        _attempts = 0
        _retry_count = 0 if retry_count <= 0 else retry_count

        if enforce_same_session_id:
            # we first load the request to ensure it belongs to the session
            existing_work_request = self.get_requests(
                id=work_request.id, session_id=work_request.metadata.session_id
            )

            if existing_work_request is None or len(existing_work_request) == 0:
                ContextLogger.warn(
                    self._logger_key,
                    f"WorkRequest [{work_request.id}] with session_id [{work_request.metadata.session_id}] not found",
                )

                return None

        while _attempts <= _retry_count:
            if _attempts > 0:
                sleep(3)

            ContextLogger.debug(
                self._logger_key,
                "Updating WorkRequest with id [%s]%s"
                % (
                    work_request.id,
                    ("" if _attempts <= 0 else ", attempt number [%d]" % _attempts),
                ),
            )

            _attempts += 1

            try:
                expected_server_id = None

                if expect_null_server_id:
                    expected_server_id = 'NULL'
                elif enforce_same_server_id:
                    expected_server_id = ServerController.instance().server_id

                new_work_request = self._update_request(work_request, expected_server_id=expected_server_id)

                return new_work_request
            except:
                error_str = (
                    "Failed to update WorkRequest with id [%s], error = [%s]"
                    % (
                        work_request.id,
                        repr(exc_info()),
                    )
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

        ContextLogger.warn(
            self._logger_key,
            "Failed to update WorkRequest with id [%s], all attempts failed"
            % work_request.id,
        )

        return None

    def get_requests(
        self,
        id: str = None,
        model_ids: List[str] = None,
        user_id: str = None,
        session_id: str = None,
        request_date_from: str = None,
        request_date_to: str = None,
        request_statuses: List[str] = None,
        server_ids: List[str] | None = None,
        limit: int = 200,
    ) -> List[WorkRequest]:
        try:
            results: List[WorkRequestRecord] = WorkRequestDAO.execute_query(
                WorkRequestQuery.SELECT_FILTERED,
                ApplicationConfig.instance().database_config,
                query_kwargs={
                    "id": id,
                    "model_ids": model_ids,
                    "user_id": user_id,
                    "request_date_from": request_date_from,
                    "request_date_to": request_date_to,
                    "request_statuses": request_statuses,
                    "session_id": session_id,
                    "server_ids": server_ids,
                    "limit": limit,
                },
            )

            if results is None or len(results) == 0:
                return []

            return list(map(lambda x: WorkRequest.init_from_record(x), results))
        except:
            error_str = "Failed to load WorkRequests, error = [%s]" % (
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return []

    def _initialize_workers(self):
        # TODO: change this to monitor current workers vs config and update worker models
        # TODO: check for disabled models (remove if ALL scaled down)
        # TODO: randomize order of models and round-robin between workers
        if len(self._workers) == WorkRequestController.NUM_WORKERS:
            return

        models = ModelController.instance().get_models()
        active_model_ids: List[str] = list(
            map(lambda m: m.id, filter(lambda fm: fm.enabled, models))
        )
        shuffle(active_model_ids)
        models_per_worker: List[List[str]] = []

        for x in range(len(active_model_ids)):
            worker_index = x % WorkRequestController.NUM_WORKERS

            if len(models_per_worker) < worker_index + 1:
                models_per_worker.append([])

            models_per_worker[worker_index].append(active_model_ids[x])

        workers: List[WorkRequestWorker] = []

        for worker_models in models_per_worker:
            worker = WorkRequestWorker(self)
            worker.update_model_ids(worker_models)
            worker.start()
            workers.append(worker)

        self._workers = ThreadSafeList(workers)

    def _update_worker_models(self):
        current_worker_models: List[str] = []
        models_per_worker: List[List[Any]] = []

        for worker in list(self._workers):
            models_per_worker.append([worker, list(worker.model_ids), False])
            current_worker_models.extend(list(worker.model_ids))

        models = ModelController.instance().get_models()
        active_model_ids: List[str] = list(
            map(lambda m: m.id, filter(lambda fm: fm.enabled, models))
        )

        for model_id in current_worker_models:
            if model_id in active_model_ids:
                continue

            for worker_tuple in models_per_worker:
                if model_id not in worker_tuple[1]:
                    continue

                worker_tuple[1].remove(model_id)
                worker_tuple[2] = True  # mark changed
                break

        for model_id in active_model_ids:
            if model_id in current_worker_models:
                continue

            best_matched_worker = models_per_worker[0]

            for worker_tuple in models_per_worker[1:]:
                if len(worker_tuple[1]) < len(best_matched_worker[1]):
                    best_matched_worker = worker_tuple

            best_matched_worker[1].append(model_id)
            best_matched_worker[2] = True  # mark changed

        for updated_worker in filter(lambda w: w[2], models_per_worker):
            updated_worker[0].update_model_ids(updated_worker[1])

    def _stop_workers(self):
        for worker in self._workers:
            if worker.is_alive():
                worker.kill()

        for worker in self._workers:
            worker.join()

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        # initial wait for models cache to be populated
        if self._wait_or_kill(20):
            return

        self._initialize_workers()

        while True:
            if self._wait_or_kill(WorkRequestController.WORKER_LOADBALANCE_WAIT_TIME):
                break

            try:
                self._update_worker_models()
            except:
                error_str = "Failed to load balance workers, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

        self._stop_workers()

        ContextLogger.info(self._logger_key, "Controller stopped")

    def mark_workrequest_failed(
        self, work_request: WorkRequest, enforce_same_server_id: bool = True, reason: Union[str, None] = None
    ) -> WorkRequest:
        work_request.request_status = WorkRequestStatus.FAILED
        work_request.request_status_reason = reason if reason is not None else "ERROR"
        updated_work_request = self.update_request(work_request, enforce_same_server_id=enforce_same_server_id, retry_count=1)

        if updated_work_request is None:
            raise Exception("Failed to update WorkRequest [%s]" % work_request.id)

        return updated_work_request

    def load_stats(
        self,
        model_ids: List[str] = None,
        user_id: str = None,
        session_id: str = None,
        request_date_from: str = None,
        request_date_to: str = None,
        request_statuses: List[str] = None,
        input_size_ge: int | None = None,
        input_size_le: int | None = None,
        group_by: List[str] = None,
    ) -> List[WorkRequestStatsModel]:
        try:
            _request_date_from = (
                request_date_from
                if request_date_from is not None
                else now_delta("-21d")
            )

            results: List[WorkRequestStatsRecord] = WorkRequestStatsDAO.execute_query(
                WorkRequestStatsQuery.FILTERED_STATS,
                ApplicationConfig.instance().database_config,
                query_kwargs={
                    "model_ids": model_ids,
                    "user_id": user_id,
                    "session_id": session_id,
                    "request_date_from": _request_date_from,
                    "request_date_to": request_date_to,
                    "request_statuses": request_statuses,
                    "input_size_ge": input_size_ge,
                    "input_size_le": input_size_le,
                    "group_by": group_by,
                },
            )

            if results is None or len(results) == 0:
                return []

            return list(
                map(lambda x: WorkRequestStatsModel.init_from_record(x), results)
            )
        except:
            error_str = "Failed to load WorkRequestStats, error = [%s]" % (
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return []

    def load_stats_filter_data(self) -> WorkRequestStatsFilterData:
        return WorkRequestStatsFilterData(
            model_ids=list(map(lambda x: x.id, ModelController.instance().get_models()))
        )
