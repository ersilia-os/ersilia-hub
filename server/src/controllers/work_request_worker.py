import traceback
from json import dumps
from random import choices
from string import ascii_lowercase
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep
from typing import Dict, List, Set, Union

from controllers.job_submission_process import JobSubmissionProcess
from controllers.model import ModelController
from controllers.model_input_cache import ModelInputCache
from controllers.model_instance_handler import (
    ModelInstanceController,
    ModelInstanceHandler,
)
from controllers.model_integration import ModelIntegrationController
from controllers.s3_integration import S3IntegrationController
from controllers.server import ServerController
from objects.model_integration import JobResult, JobStatus
from objects.s3_integration import S3ResultObject
from objects.work_request import WorkRequest, WorkRequestStatus
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel
from python_framework.thread_safe_list import ThreadSafeList
from python_framework.time import (
    datetime_delta,
    is_date_in_range_from_now,
    string_from_date,
    utc_now,
    utc_now_datetime,
)


class WorkRequestControllerStub:
    @staticmethod
    def instance() -> "WorkRequestControllerStub":
        pass

    def update_request(
        self,
        work_request: WorkRequest,
        enforce_same_server_id: bool = True,
        expect_null_server_id: bool = False,  # for first time update
        retry_count: int = 0,
    ) -> Union[WorkRequest, None]:
        pass

    def mark_workrequest_failed(
        self, work_request: WorkRequest, reason: Union[str, None] = None
    ) -> WorkRequest:
        pass

    def get_requests(
        self,
        id: str = None,
        model_ids: List[str] = None,
        user_id: str = None,
        request_date_from: str = None,
        request_date_to: str = None,
        request_statuses: List[str] = None,
        server_ids: List[str] | None = None,
        limit: int = 200,
    ) -> List[WorkRequest]:
        pass


class WorkRequestWorker(Thread):
    DEFAULT_PROCESSING_WAIT_TIME = 10
    DEFAULT_POD_READY_TIMEOUT = 600

    _logger_key: str = None
    _kill_event: Event

    _controller: WorkRequestControllerStub

    id: str
    model_ids: ThreadSafeList[str]
    _pod_ready_timeout: int
    _processing_wait_time: int

    def __init__(self, controller: WorkRequestControllerStub):
        Thread.__init__(self)

        self._controller = controller

        self.id = "".join(choices(ascii_lowercase, k=6))
        self.model_ids = ThreadSafeList()

        self._logger_key = "WorkRequestWorker[%s]" % self.id
        self._kill_event = Event()
        self._pod_ready_timeout = int(
            load_environment_variable(
                "WORK_REQUEST_WORKER_POD_READY_TIMEOUT",
                default=WorkRequestWorker.DEFAULT_POD_READY_TIMEOUT,
            )
        )
        self._processing_wait_time = int(
            load_environment_variable(
                "WORK_REQUEST_WORKER_PROCESSING_WAIT_TIME",
                default=WorkRequestWorker.DEFAULT_PROCESSING_WAIT_TIME,
            )
        )

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    "LOG_LEVEL_WorkRequestWorker", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def update_model_ids(self, model_ids: List[str]):
        ContextLogger.info(
            self._logger_key, f"Updating model_ids list with: {model_ids}"
        )
        self.model_ids = ThreadSafeList(model_ids)

    def _upload_result_to_s3(self, work_request: WorkRequest, result: JobResult):
        result_obj = S3ResultObject(
            model_id=work_request.model_id,
            request_id=str(work_request.id),
            result=dumps(result),
        )

        return S3IntegrationController.instance().upload_result(result_obj)

    def _process_failed_job(
        self,
        work_request: WorkRequest,
        reason: str = "Job Failed",
        has_cached_results: bool = False,
        instance: ModelInstanceHandler | None = None,
    ):
        if instance is not None:
            instance.kill()

        work_request.request_status = WorkRequestStatus.FAILED
        work_request.request_status_reason = reason
        work_request.processed_timestamp = utc_now()
        updated_work_request = self._controller.update_request(
            work_request, retry_count=1
        )

        if has_cached_results:
            try:
                ModelInputCache.instance().clear_work_request_cached_results(
                    work_request.id
                )
            except:
                ContextLogger.warn(self._logger_key, repr(exc_info()))

        if updated_work_request is None:
            raise Exception("Failed to update WorkRequest [%s]" % work_request.id)

        return updated_work_request

    def _process_completed_job(
        self,
        work_request: WorkRequest,
        instance: ModelInstanceHandler,
        result_content: JobResult = None,
        has_cached_results: bool = False,
        non_cached_inputs: list[str] | None = None,
    ):
        ContextLogger.debug(
            self._logger_key,
            "Processing COMPLETED job for workrequest [%d], has_cached_results = [%s], non_cached_inputs = [%d]..."
            % (
                work_request.id,
                has_cached_results,
                0 if non_cached_inputs is None else len(non_cached_inputs),
            ),
        )

        instance.kill()

        if instance.k8s_pod is None:
            return self._process_failed_job(
                work_request,
                reason="Instance pod is null",
                has_cached_results=has_cached_results,
                instance=instance,
            )

        _result_content: JobResult | None = result_content
        job_result_content = result_content

        # if not defined. we assume ASYNC mode
        # TODO: in the future, we can move this result_content handling into the jobsubmissionprocess as well
        if _result_content is None:
            _result_content = ModelIntegrationController.instance().get_job_result(
                work_request.model_id,
                str(work_request.id),
                instance.k8s_pod.ip,
                work_request.model_job_id,
            )
            job_result_content = _result_content

        if _result_content is None:
            # NOTE: this should never happen, but checking anyway
            ContextLogger.error(
                self._logger_key,
                "Job Result is None for workrequest [%d], jobid [%s]"
                % (work_request.id, work_request.model_job_id),
            )
            return self._process_failed_job(
                work_request,
                reason="Job Result is empty",
                has_cached_results=has_cached_results,
                instance=instance,
            )

        if has_cached_results:
            _result_content = (
                ModelInputCache.instance().hydrate_job_result_with_cached_results(
                    work_request.id,
                    work_request.request_payload.entries,
                    non_cached_inputs,
                    _result_content,
                )
            )

            try:
                ModelInputCache.instance().clear_work_request_cached_results(
                    work_request.id
                )
            except:
                ContextLogger.warn(self._logger_key, repr(exc_info()))

        if len(_result_content) != len(work_request.request_payload.entries):
            return self._process_failed_job(
                work_request,
                reason="Model result count not the same as model input count",
            )

        if not self._upload_result_to_s3(work_request, _result_content):
            sleep(30)

            if not self._upload_result_to_s3(work_request, _result_content):
                raise Exception("Failed to upload result to S3, twice")

        work_request.request_status = WorkRequestStatus.COMPLETED
        work_request.processed_timestamp = utc_now()
        updated_work_request = self._controller.update_request(
            work_request, retry_count=1
        )

        if updated_work_request is None:
            raise Exception("Failed to update WorkRequest [%d]" % work_request.id)

        if work_request.request_payload.cache_opt_in:
            ModelInputCache.instance().cache_model_results(
                work_request.model_id,
                non_cached_inputs,
                job_result_content,
                work_request.user_id,
            )

    def _handle_processing_work_request(
        self, work_request: WorkRequest, instance: ModelInstanceHandler
    ) -> WorkRequest:
        ContextLogger.trace(
            self._logger_key,
            "Handling [PROCESSING] workrequest [%d]..." % work_request.id,
        )

        if not instance.is_job_completed():
            ContextLogger.debug(
                self._logger_key,
                "Still waiting for jobprocess to complete for workrequest [%s]"
                % str(work_request.id),
            )

            return work_request

        job_submission_process: JobSubmissionProcess = instance.job_submission_process
        job_status: JobStatus = job_submission_process.job_status
        job_result: JobResult = job_submission_process.job_result
        job_submission_timestamp: str | None = (
            job_submission_process.job_submission_timestamp
        )
        job_completion_timestamp: str | None = (
            job_submission_process.job_completion_timestamp
        )
        job_status_reason: str | None = job_submission_process.job_status_reason
        job_has_cached_results: bool = len(work_request.request_payload.entries) != len(
            instance.job_submission_entries
        )
        job_non_cached_inputs: list[str] | None = (
            job_submission_process.job_entries if job_has_cached_results else None
        )

        try:
            updated_work_request: WorkRequest = work_request.copy()
            updated_work_request.job_submission_timestamp = job_submission_timestamp
            updated_work_request.pod_ready_timestamp = instance.pod_ready_timestamp

            if job_status == JobStatus.COMPLETED:
                updated_work_request = self._process_completed_job(
                    updated_work_request,
                    instance,
                    job_result,
                    has_cached_results=job_has_cached_results,
                    non_cached_inputs=job_non_cached_inputs,
                )
            elif job_status == JobStatus.FAILED:
                updated_work_request = self._process_failed_job(
                    updated_work_request,
                    has_cached_results=job_has_cached_results,
                    reason=job_status_reason,
                    instance=instance,
                )
            else:
                ContextLogger.error(
                    self._logger_key,
                    "Job has non-completed state, but the JobSubmissionProcess is completed - workrequest [%d], status [%s]"
                    % (work_request.id, job_status),
                )

            instance.kill()

            return updated_work_request
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to handle [PROCESSING] request [%d], error = [%s]"
                % (work_request.id, repr(exc_info())),
            )

            try:
                return self._controller.mark_workrequest_failed(
                    work_request, repr(exc_info())
                )
            except:
                pass

            return None

    def _handle_processing_work_requests(self, work_requests: List[WorkRequest]):
        ContextLogger.debug(self._logger_key, "Handling [PROCESSING] requests...")

        for work_request in work_requests:
            try:
                ContextLogger.debug(
                    self._logger_key,
                    "Handling [PROCESSING] WorkRequest with id [%d]..."
                    % work_request.id,
                )

                instance = ModelInstanceController.instance().get_instance(
                    work_request.model_id, work_request.id
                )

                if instance is None:
                    ContextLogger.warn(
                        self._logger_key,
                        "Failed to find instance for request_id = [%d]"
                        % work_request.id,
                    )

                    ContextLogger.warn(
                        self._logger_key,
                        "WorkRequest [%d] in [PROCESSING] state but instance is missing, assuming [FAILED]"
                        % work_request.id,
                    )

                    updated_work_request = self._controller.mark_workrequest_failed(
                        work_request
                    )

                    continue

                self._handle_processing_work_request(work_request, instance)
            except:
                ContextLogger.error(
                    self._logger_key,
                    "Failed to handle [PROCESSING] WorkRequest with id [%d], error = [%s]"
                    % (
                        work_request.id,
                        repr(exc_info()),
                    ),
                )
                traceback.print_exc(file=stdout)

    def _handle_scheduling_requests(self, work_requests: List[WorkRequest]):
        ContextLogger.debug(self._logger_key, "Handling [SCHEDULING] requests...")

        for work_request in work_requests:
            try:
                ContextLogger.debug(
                    self._logger_key,
                    "Handling [SCHEDULING] WorkRequest with id [%d]..."
                    % work_request.id,
                )

                # ignore recently created requests
                if is_date_in_range_from_now(work_request.last_updated, "-2m"):
                    continue

                instance = ModelInstanceController.instance().get_instance(
                    work_request.model_id, work_request.id
                )

                if instance is None:
                    ContextLogger.warn(
                        self._logger_key,
                        "Failed to find instance for request_id = [%d]. Assuming process failed, moving back to [QUEUED]"
                        % work_request.id,
                    )

                    work_request.request_status = WorkRequestStatus.QUEUED
                    work_request.request_status_reason = (
                        "FAILED TO FIND REQUESTED INSTANCE"
                    )
                elif not instance.is_active():
                    ContextLogger.warn(
                        self._logger_key,
                        "Instance for request_id = [%d] in in-active state. Assuming process failed, moving back to [QUEUED]"
                        % work_request.id,
                    )

                    work_request.request_status = WorkRequestStatus.QUEUED
                    work_request.request_status_reason = (
                        "INSTANCE UNEXPECTED IN-ACTIVE STATE"
                    )
                else:
                    ContextLogger.debug(
                        self._logger_key,
                        "Found instance for [SCHEDULING] work request [%d], setting status to [PROCESSING]"
                        % work_request.id,
                    )
                    work_request.request_status = WorkRequestStatus.PROCESSING

                updated_work_request = self._controller.update_request(
                    work_request, retry_count=1
                )

                if updated_work_request is None:
                    raise Exception(
                        "Failed to update WorkRequest [%d]" % work_request.id
                    )
            except:
                ContextLogger.error(
                    self._logger_key,
                    "Failed to handle [SCHEDULING] WorkRequest with id [%d], error = [%s]"
                    % (
                        work_request.id,
                        repr(exc_info()),
                    ),
                )
                traceback.print_exc(file=stdout)

    def _handle_work_request_cache(self, work_request: WorkRequest) -> list[str]:
        if (
            not ModelController.instance()
            .get_model(work_request.model_id)
            .details.cache_enabled
        ):
            return work_request.request_payload.entries

        try:
            cached_results = ModelInputCache.instance().lookup_model_results(
                work_request.model_id, work_request.request_payload.entries
            )

            if len(cached_results) == 0:
                return work_request.request_payload.entries

            non_cached_entries = list(
                filter(
                    lambda input: not any(
                        map(
                            lambda cached_result: input == cached_result.input,
                            cached_results,
                        )
                    ),
                    work_request.request_payload.entries,
                )
            )

            if len(non_cached_entries) > 0:
                if not ModelInputCache.instance().persist_cached_workrequest_results(
                    work_request.id, cached_results
                ):
                    raise Exception(
                        "Failed to persist cached WorkRequest [%d] results, ignoring cache"
                        % work_request.id,
                    )

                return non_cached_entries

            job_result = ModelInputCache.instance().consolidate_results(
                work_request.request_payload.entries, [], [], cached_results
            )

            if not self._upload_result_to_s3(work_request, job_result):
                sleep(20)

                if not self._upload_result_to_s3(work_request, job_result):
                    raise Exception("Failed to upload result to S3, twice")

            return []
        except:
            ContextLogger.warn(
                self._logger_key,
                f"Failed to handle WorkRequest from cached results for workrequest = [{work_request.id}], error = [{exc_info()!r}]",
            )
            traceback.print_exc(file=stdout)

            return work_request.request_payload.entries

    def _handle_queued_requests(self, work_requests: List[WorkRequest]):
        ContextLogger.debug(self._logger_key, "Handling [QUEUED] requests...")

        # skip list based on failed instance creation, NOT due to job submit failures
        skipped_model_ids: Set[str] = set()

        for work_request in work_requests:
            if work_request.model_id in skipped_model_ids:
                ContextLogger.warn(
                    self._logger_key,
                    "Skipping WorkRequest [%d] with model id = [%s]"
                    % (work_request.id, work_request.model_id),
                )
                continue

            if ModelInstanceController.instance().max_instances_limit_reached():
                ContextLogger.warn(
                    self._logger_key,
                    "Max Concurrent Model Instances reached, skipping queued WorkRequests",
                )
                return

            updated_work_request: WorkRequest = None

            try:
                work_request.request_status = WorkRequestStatus.SCHEDULING
                work_request.server_id = ServerController.instance().server_id
                updated_work_request = self._controller.update_request(
                    work_request, expect_null_server_id=True, retry_count=0
                )

                if updated_work_request is None:
                    raise Exception(
                        "Failed to persist updated WorkRequest [%d]" % work_request.id
                    )

                non_cached_inputs = self._handle_work_request_cache(
                    updated_work_request
                )

                if len(non_cached_inputs) == 0:
                    updated_work_request.request_status = WorkRequestStatus.COMPLETED
                    updated_work_request.processed_timestamp = utc_now()
                    updated_work_request = self._controller.update_request(
                        updated_work_request, retry_count=1
                    )

                    if updated_work_request is None:
                        raise Exception(
                            "Failed to update WorkRequest [%d]" % work_request.id
                        )

                    ContextLogger.info(
                        self._logger_key,
                        "Request completed by cached results [%d]" % work_request.id,
                    )

                    continue

                instance = ModelInstanceController.instance().request_instance(
                    work_request.model_id,
                    str(work_request.id),
                    ignore_max_concurrent_limit=True,
                    job_submission_entries=(
                        work_request.request_payload.entries
                        if non_cached_inputs is None or len(non_cached_inputs) == 0
                        else non_cached_inputs
                    ),
                )

                if instance is None:
                    ContextLogger.warn(
                        self._logger_key,
                        "Failed to acquire instance for WorkRequest [%d]. Setting status to [QUEUED] and adding model id [%s] to skip list"
                        % (work_request.id, work_request.model_id),
                    )
                    skipped_model_ids.add(work_request.model_id)

                    updated_work_request.request_status = WorkRequestStatus.QUEUED
                    updated_work_request.request_status_reason = (
                        "FAILED TO ACQUIRE MODEL INSTANCE"
                    )
                    updated_work_request = self._controller.update_request(
                        updated_work_request, retry_count=1
                    )

                    if updated_work_request is None:
                        raise Exception("Failed to persist updated WorkRequest")

                    continue

                updated_work_request.request_status = WorkRequestStatus.PROCESSING
                updated_work_request = self._controller.update_request(
                    updated_work_request, retry_count=0
                )

                if updated_work_request is None:
                    raise Exception("Failed to persist updated WorkRequest")

                if not instance.wait_for_pod_created(timeout=30):
                    raise Exception("Pod failed to create within [30]s")
            except:
                ContextLogger.error(
                    self._logger_key,
                    "Failed to handle [QUEUED] WorkRequest with id [%d], error = [%s]"
                    % (
                        work_request.id,
                        repr(exc_info()),
                    ),
                )
                traceback.print_exc(file=stdout)

                # set request status to FAILED if job submission failed
                if updated_work_request is not None and (
                    updated_work_request.request_status == WorkRequestStatus.SCHEDULING
                    or updated_work_request.request_status
                    == WorkRequestStatus.PROCESSING
                ):
                    try:
                        self._controller.mark_workrequest_failed(
                            updated_work_request, repr(exc_info())
                        )
                    except:
                        ContextLogger.error(
                            self._logger_key,
                            "Failed to mark WorkRequest [%s] failed, error = [%s]"
                            % (str(updated_work_request.id), repr(exc_info())),
                        )

    def _handle_work_requests(self):
        ContextLogger.debug(self._logger_key, "Loading WorkRequests from DB...")
        results: List[WorkRequest] = self._controller.get_requests(
            model_ids=self.model_ids,
            request_statuses=[
                WorkRequestStatus.QUEUED.value,
                WorkRequestStatus.SCHEDULING.value,
                WorkRequestStatus.PROCESSING.value,
            ],
            server_ids=[
                "NULL",
                ServerController.instance().server_id,
            ],
        )
        ContextLogger.debug(self._logger_key, "WorkRequests loaded from DB.")

        work_requests_by_status: Dict[str, List[WorkRequest]] = {}

        for request in results:
            if request.request_status not in work_requests_by_status:
                work_requests_by_status[request.request_status] = []

            work_requests_by_status[request.request_status].append(request)

        for status, requests in work_requests_by_status.items():
            if status == WorkRequestStatus.PROCESSING:
                self._handle_processing_work_requests(requests)
            elif status == WorkRequestStatus.SCHEDULING:
                self._handle_scheduling_requests(requests)
            elif status == WorkRequestStatus.QUEUED:
                self._handle_queued_requests(requests)

    def _handle_failed_work_requests(self):
        ContextLogger.debug(self._logger_key, "Loading failed WorkRequests from DB...")

        current_time = utc_now_datetime()
        start_time = string_from_date(datetime_delta(current_time, "-10m"))
        end_time = string_from_date(datetime_delta(current_time, "-1m"))
        work_requests: List[WorkRequest] = self._controller.get_requests(
            model_ids=self.model_ids,
            request_statuses=[
                WorkRequestStatus.FAILED.value,
            ],
            request_date_from=start_time,
            request_date_to=end_time,
            server_ids=[ServerController.instance().server_id],
        )

        ContextLogger.debug(self._logger_key, "Failed WorkRequests loaded from DB.")

        for work_request in work_requests:
            try:
                ContextLogger.debug(
                    self._logger_key,
                    "Handling [FAILED] WorkRequest with id [%d]..." % work_request.id,
                )

                ModelInstanceController.instance().ensure_instance_terminated(
                    work_request.model_id, work_request.id
                )
            except:
                ContextLogger.error(
                    self._logger_key,
                    "Failed to handle [FAILED] WorkRequest with id [%d], error = [%s]"
                    % (
                        work_request.id,
                        repr(exc_info()),
                    ),
                )
                traceback.print_exc(file=stdout)

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        while True:
            if self._wait_or_kill(self._processing_wait_time):
                break

            try:
                self._handle_work_requests()
                self._handle_failed_work_requests()
            except:
                error_str = "Failed to handle work requests, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

        ContextLogger.info(self._logger_key, "Controller stopped")
