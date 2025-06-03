from json import dumps
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep, time
import traceback
from typing import Dict, List, Set, Tuple, Union
from python_framework.thread_safe_list import ThreadSafeList
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from string import ascii_lowercase
from random import choices
from python_framework.time import utc_now_datetime, datetime_delta, string_from_date

from controllers.k8s import K8sController

from threading import Thread

from objects.work_request import WorkRequest, WorkRequestStatus
from python_framework.time import is_date_in_range_from_now

from controllers.scaling_manager import ScalingManager
from controllers.model_integration import ModelIntegrationController
from objects.k8s import K8sPod
from objects.model_integration import JobResult, JobStatus
from controllers.s3_integration import S3IntegrationController
from objects.s3_integration import S3ResultObject


class WorkRequestControllerStub:

    @staticmethod
    def instance() -> "WorkRequestControllerStub":
        pass

    def update_request(
        self, work_request: WorkRequest, retry_count: int = 0
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
        limit: int = 200,
    ) -> List[WorkRequest]:
        pass


class WorkRequestWorker(Thread):

    PROCESSING_WAIT_TIME = 10
    POD_READY_TIMEOUT = 30

    _logger_key: str = None
    _kill_event: Event

    _controller: WorkRequestControllerStub

    id: str
    model_ids: ThreadSafeList[str]

    def __init__(self, controller: WorkRequestControllerStub):
        Thread.__init__(self)

        self._controller = controller

        self.id = "".join(choices(ascii_lowercase, k=6))
        self.model_ids = ThreadSafeList

        self._logger_key = "WorkRequestWorker[%s]" % self.id
        self._kill_event = Event()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_WorkRequestWorker", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def update_model_ids(self, model_ids: List[str]):
        self.model_ids = ThreadSafeList(model_ids)

    def _upload_result_to_s3(self, work_request: WorkRequest, result: JobResult):
        result_obj = S3ResultObject(
            model_id=work_request.model_id,
            request_id=str(work_request.id),
            result=dumps(result),
        )

        return S3IntegrationController.instance().upload_result(result_obj)

    def _process_completed_job(self, work_request: WorkRequest, pod: K8sPod):
        result_content = ModelIntegrationController.instance().get_job_result(
            work_request.model_id,
            str(work_request.id),
            pod.ip,
            work_request.model_job_id,
        )

        if result_content is None:
            # NOTE: this should never happen, but checking anyway
            ContextLogger.error(
                self._logger_key,
                "Job Result is None for workrequest [%d], jobid [%s]"
                % (work_request.id, work_request.model_job_id),
            )
            return self._controller.mark_workrequest_failed(work_request)

        if not self._upload_result_to_s3(work_request, result_content):
            sleep(30)

            if not self._upload_result_to_s3(work_request, result_content):
                raise Exception("Failed to upload result to S3, twice")

        work_request.request_status = WorkRequestStatus.COMPLETED
        updated_work_request = self._controller.update_request(
            work_request, retry_count=1
        )

        if updated_work_request is None:
            raise Exception("Failed to update WorkRequest [%d]" % work_request.id)

        if (
            K8sController.instance().clear_work_request(work_request.model_id, pod.name)
            is None
        ):
            sleep(10)

            if (
                K8sController.instance().clear_work_request(
                    work_request.model_id, pod.name
                )
                is None
            ):
                raise Exception(
                    "Failed to clear workrequest [%d] from pod [%s]"
                    % (work_request.id, pod.name)
                )

    def _handle_processing_work_request(self, work_request: WorkRequest, pod: K8sPod):
        try:
            status_response = ModelIntegrationController.instance().get_job_status(
                work_request.model_id,
                str(work_request.id),
                pod.ip,
                work_request.model_job_id,
            )

            if status_response.status == JobStatus.COMPLETED:
                return self._process_completed_job(work_request, pod)
            elif status_response.status == JobStatus.FAILED:
                return self._controller.mark_workrequest_failed(work_request)
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

                # flag the workload as new, for handling scenarios below
                potentially_new_workload = is_date_in_range_from_now(
                    work_request.last_updated, "-5m"
                )

                pod = K8sController.instance().get_pod_by_request(
                    work_request.model_id, str(work_request.id)
                )

                if pod is None:
                    ContextLogger.warn(
                        self._logger_key,
                        "Failed to find pod for request_id = [%d]" % work_request.id,
                    )

                    # TODO: potentially "self-heal" by getting a new pod

                    if not potentially_new_workload:
                        # NOTE: if work request "disappeared", we set it to FAILED and can rerun it from there
                        ContextLogger.warn(
                            self._logger_key,
                            "WorkRequest [%d] older than [5m] but missing, assuming [FAILED]"
                            % work_request.id,
                        )

                        updated_work_request = self._controller.mark_workrequest_failed(
                            work_request
                        )

                    continue

                updated_work_request = work_request

                # if no job_id, but we have a pod, job submission might have failed
                if (
                    work_request.model_job_id is None
                    or len(work_request.model_job_id) == 0
                ):
                    if potentially_new_workload:
                        # might still be submitting the job
                        ContextLogger.warn(
                            self._logger_key,
                            "No JobId found for workrequest [%d], skipping due to age within [5]m"
                            % work_request.id,
                        )
                        continue
                    else:
                        try:
                            updated_work_request = self._submit_job(work_request, pod)
                        except:
                            ContextLogger.error(
                                self._logger_key,
                                "Failed to submit job, error = [%s]" % repr(exc_info()),
                            )
                            traceback.print_exc(file=stdout)

                            updated_work_request = (
                                self._controller.mark_workrequest_failed(work_request)
                            )
                            continue

                self._handle_processing_work_request(updated_work_request, pod)
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

                if is_date_in_range_from_now(work_request.last_updated, "-2m"):
                    continue

                pod = K8sController.instance().get_pod_by_request(
                    work_request.model_id, str(work_request.id)
                )

                if pod is None:
                    ContextLogger.warn(
                        self._logger_key,
                        "Failed to find pod for request_id = [%d]. Assuming process failed, moving back to [QUEUED]"
                        % work_request.id,
                    )

                    work_request.request_status = WorkRequestStatus.QUEUED
                    work_request.request_status_reason = (
                        "FAILED TO FIND REQUESTED INSTANCE"
                    )
                else:
                    ContextLogger.debug(
                        self._logger_key,
                        "Found pod for [SCHEDULING] work request [%d], setting status to [PROCESSING]"
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

    def _submit_job(
        self, work_request: WorkRequest, pod: K8sPod, retry_count=1
    ) -> WorkRequest:
        ContextLogger.debug(
            self._logger_key,
            "Submitting job to model [%s] for workrequest [%d]..."
            % (work_request.model_id, work_request.id),
        )
        start_time = time()

        _pod = pod

        # wait for the model to become available
        while not _pod.state.ready:
            current_time = time()

            if current_time - start_time > WorkRequestWorker.POD_READY_TIMEOUT:
                raise Exception(
                    "Instance [%s] took longer than [%d]s to start - workrequest [%d]"
                    % (_pod.name, WorkRequestWorker.POD_READY_TIMEOUT, work_request.id)
                )

            sleep(5)

            _pod = K8sController.instance().get_pod(_pod.name)

        attempt_count = 0
        job_id = None

        while attempt_count <= retry_count:
            try:
                job_submission_response = (
                    ModelIntegrationController.instance().submit_job(
                        work_request.model_id,
                        str(work_request.id),
                        _pod.ip,
                        work_request.request_payload.entries,
                    )
                )
                job_id = job_submission_response.job_id

                break
            except:
                error_str = (
                    "Failed to submit job for instance [%s], workrequest [%d], error [%s]"
                    % (_pod.name, work_request.id, repr(exc_info()))
                )

                if attempt_count < retry_count:
                    ContextLogger.warn(self._logger_key, error_str)
                else:
                    raise Exception(error_str)

            attempt_count += 1

        if job_id is None:
            raise Exception(
                "Failed to submit job for instance [%s], workrequest [%d] after [%d] attempts"
                % (_pod.name, work_request.id, attempt_count)
            )

        work_request.request_status = WorkRequestStatus.PROCESSING
        work_request.model_job_id = job_id
        work_request.request_status_reason = "JOB SUBMITTED"
        updated_work_request = self._controller.update_request(
            work_request, retry_count=1
        )

        if updated_work_request is None:
            raise Exception(
                "Failed to update workrequest [%d] with new job_id" % work_request.id
            )

        return updated_work_request

    def _handle_queued_requests(self, work_requests: List[WorkRequest]):
        ContextLogger.debug(self._logger_key, "Handling [QUEUED] requests...")

        # skip list based on failed pod scaling, NOT due to job submit failures
        skipped_model_ids: Set[str] = set()

        for work_request in work_requests:
            if work_request.model_id in skipped_model_ids:
                ContextLogger.warn(
                    self._logger_key,
                    "Skipping WorkRequest [%d] with model id = [%s]"
                    % (work_request.id, work_request.model_id),
                )
                continue

            updated_work_request: WorkRequest = None

            try:
                work_request.request_status = WorkRequestStatus.SCHEDULING
                updated_work_request = self._controller.update_request(
                    work_request, retry_count=0
                )

                if updated_work_request is None:
                    raise Exception("Failed to persist updated WorkRequest")

                pod = ScalingManager.instance().acquire_instance(
                    work_request.model_id, str(work_request.id), 5
                )

                if pod is None:
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

                # throws exception on failure, which will be caught
                updated_work_request = self._submit_job(updated_work_request, pod)
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
        )

        ContextLogger.debug(self._logger_key, "Failed WorkRequests loaded from DB.")

        for work_request in work_requests:
            try:
                ContextLogger.debug(
                    self._logger_key,
                    "Handling [FAILED] WorkRequest with id [%d]..." % work_request.id,
                )

                ScalingManager.instance().release_instance(
                    work_request.model_id, str(work_request.id)
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
            if self._wait_or_kill(WorkRequestWorker.PROCESSING_WAIT_TIME):
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
