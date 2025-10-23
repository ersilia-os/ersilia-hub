import traceback
from json import dumps
from random import choices
from string import ascii_lowercase
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep, time
from typing import Dict, List, Set, Tuple, Union

from controllers.k8s import K8sController
from controllers.model import ModelController
from controllers.model_input_cache import ModelInputCache
from controllers.model_instance_handler import ModelInstanceController
from controllers.model_instance_log import (
    ModelInstanceLogController,
    ModelInstanceLogEvent,
)
from controllers.model_integration import ModelIntegrationController
from controllers.s3_integration import S3IntegrationController
from controllers.scaling_manager import ScalingManager
from controllers.server import ServerController
from objects.k8s import K8sPod
from objects.model import ModelExecutionMode
from objects.model_integration import JobResult, JobStatus
from objects.s3_integration import S3ResultObject
from objects.work_request import WorkRequest, WorkRequestStatus
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel
from python_framework.thread_safe_cache import ThreadSafeCache
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


class JobSubmissionTask(Thread):
    _logger_key: str
    _kill_event: Event

    _controller: WorkRequestControllerStub

    work_request: WorkRequest
    model_execution_mode: ModelExecutionMode
    job_result: JobResult | None
    job_status: JobStatus
    job_status_reason: str | None
    pod: K8sPod
    retry_count: int
    id: str

    non_cached_inputs: list[str] | None

    _pod_ready_timeout: int

    def __init__(
        self,
        controller: WorkRequestControllerStub,
        work_request: WorkRequest,
        pod: K8sPod,
        retry_count: int = 1,
        non_cached_inputs: list[str] | None = None,
    ):
        Thread.__init__(self)

        self._controller = controller
        self.work_request = work_request
        self.pod = pod
        self.retry_count = retry_count
        self.id = JobSubmissionTask.infer_id(work_request)
        self.non_cached_inputs = non_cached_inputs

        self._logger_key = "JobSubmissionTask[%s]" % self.id
        self._kill_event = Event()

        self._pod_ready_timeout = int(
            load_environment_variable(
                "WORK_REQUEST_WORKER_POD_READY_TIMEOUT",
                default=WorkRequestWorker.DEFAULT_POD_READY_TIMEOUT,
            )
        )

        self.model_execution_mode = (
            ModelController.instance()
            .get_model(work_request.model_id)
            .details.execution_mode
        )
        self.job_result = None
        self.job_status = JobStatus.PENDING
        self.job_status_reason = None

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    "LOG_LEVEL_JobSubmissionTask", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def infer_id(work_request: WorkRequest) -> str:
        return f"{work_request.model_id}_{work_request.id}"

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _wait_for_pod(self) -> Tuple[WorkRequest, K8sPod]:
        ContextLogger.debug(
            self._logger_key,
            "Waiting for pod [%s] to be ready for workrequest [%d]..."
            % (self.pod.name, self.work_request.id),
        )

        start_time = time()
        _pod = self.pod

        # wait for the model to become available
        while not _pod.state.ready:
            current_time = time()

            if current_time - start_time > self._pod_ready_timeout:
                ModelInstanceLogController.instance().log_instance(
                    log_event=ModelInstanceLogEvent.INSTANCE_READINESS_FAILED,
                    k8s_pod=_pod,
                )

                raise Exception(
                    "Instance [%s] took longer than [%d]s to start - workrequest [%d]"
                    % (_pod.name, self._pod_ready_timeout, self.work_request.id)
                )

            sleep(8)

            _pod = K8sController.instance().get_pod(_pod.name)

        ContextLogger.debug(
            self._logger_key,
            "pod [%s] is ready for workrequest [%d]..."
            % (self.pod.name, self.work_request.id),
        )

        ModelInstanceLogController.instance().log_instance(
            log_event=ModelInstanceLogEvent.INSTANCE_READY,
            k8s_pod=_pod,
        )

        updated_work_request: WorkRequest = self.work_request.copy()

        try:
            updated_work_request.pod_ready_timestamp = utc_now()
            _updated_work_request = self._controller.update_request(
                updated_work_request, retry_count=1
            )

            if _updated_work_request is None:
                raise Exception("Update returned null")

            return _updated_work_request, _pod
        except:
            ContextLogger.warn(
                self._logger_key,
                "Failed to persist podreadytimestamp for workrequest id = [%s], error = [%s]"
                % (updated_work_request.id, repr(exc_info())),
            )

        return updated_work_request, _pod

    def _submit_job(self) -> WorkRequest:
        job_inputs = (
            self.work_request.request_payload.entries
            if self.non_cached_inputs is None
            else self.non_cached_inputs
        )

        ContextLogger.debug(
            self._logger_key,
            "Submitting job to model [%s] for workrequest [%d] with inputs [%d]..."
            % (self.work_request.model_id, self.work_request.id, len(job_inputs)),
        )

        attempt_count = 0
        job_id = None

        while attempt_count <= self.retry_count:
            try:
                job_submission_response = (
                    ModelIntegrationController.instance().submit_job(
                        self.work_request.model_id,
                        str(self.work_request.id),
                        self.pod.ip,
                        job_inputs,
                    )
                )
                job_id = job_submission_response.job_id

                break
            except:
                error_str = (
                    "Failed to submit job for instance [%s], workrequest [%d], error [%s]"
                    % (self.pod.name, self.work_request.id, repr(exc_info()))
                )

                if attempt_count < self.retry_count:
                    ContextLogger.warn(self._logger_key, error_str)
                else:
                    raise Exception(error_str)

            attempt_count += 1

        if job_id is None:
            raise Exception(
                "Failed to submit job for instance [%s], workrequest [%d] after [%d] attempts"
                % (self.pod.name, self.work_request.id, attempt_count)
            )

        updated_work_request: WorkRequest = self.work_request.copy()
        updated_work_request.request_status = WorkRequestStatus.PROCESSING
        updated_work_request.model_job_id = job_id
        updated_work_request.request_status_reason = "JOB SUBMITTED"
        updated_work_request.job_submission_timestamp = utc_now()
        updated_work_request = self._controller.update_request(
            updated_work_request, retry_count=1
        )

        if updated_work_request is None:
            raise Exception(
                "Failed to update workrequest [%d] with new job_id"
                % self.work_request.id
            )

        ModelInstanceLogController.instance().log_instance(
            log_event=ModelInstanceLogEvent.INSTANCE_JOB_SUBMITTED,
            k8s_pod=self.pod,
        )

        return updated_work_request

    def _monitor_async_job(self):
        if self.model_execution_mode == ModelExecutionMode.SYNC:
            return

        while True:
            status_response = ModelIntegrationController.instance().get_job_status(
                self.work_request.model_id,
                str(self.work_request.id),
                self.pod.ip,
                self.work_request.model_job_id,
            )

            if status_response.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
                ContextLogger.debug(
                    self._logger_key,
                    "Job still processing for workrequest [%d]..."
                    % self.work_request.id,
                )
                sleep(15)

                continue

            self.job_status = status_response.status

            if status_response.status == JobStatus.COMPLETED:
                ContextLogger.debug(self._logger_key, "Job COMPLETED")

                self.job_result = ModelIntegrationController.instance().get_job_result(
                    self.work_request.model_id,
                    str(self.work_request.id),
                    self.pod.ip,
                    self.work_request.model_job_id,
                )
                break
            elif status_response.status == JobStatus.FAILED:
                ContextLogger.debug(self._logger_key, "Job FAILED")

                break

    def _submit_job_sync(self) -> WorkRequest:
        job_inputs = (
            self.work_request.request_payload.entries
            if self.non_cached_inputs is None
            else self.non_cached_inputs
        )

        ContextLogger.debug(
            self._logger_key,
            "Submitting SYNC job to model [%s] for workrequest [%d] with inputs [%d] ..."
            % (self.work_request.model_id, self.work_request.id, len(job_inputs)),
        )

        attempt_count = 0

        while attempt_count <= self.retry_count:
            try:
                (
                    self.job_status,
                    self.job_status_reason,
                    self.job_result,
                ) = ModelIntegrationController.instance().submit_job_sync(
                    self.work_request.model_id,
                    str(self.work_request.id),
                    self.pod.ip,
                    job_inputs,
                )

                break
            except:
                error_str = (
                    "Failed to submit SYNC job for instance [%s], workrequest [%d], error [%s]"
                    % (self.pod.name, self.work_request.id, repr(exc_info()))
                )

                if attempt_count < self.retry_count:
                    ContextLogger.warn(self._logger_key, error_str)
                else:
                    raise Exception(error_str)

            attempt_count += 1

        if self.job_result is None or self.job_status == JobStatus.FAILED:
            raise Exception(
                "Failed to submit SYNC job for instance [%s], workrequest [%d] after [%d] attempts"
                % (self.pod.name, self.work_request.id, attempt_count)
            )

        updated_work_request: WorkRequest = self.work_request.copy()
        updated_work_request.model_job_id = "SYNC"
        updated_work_request.request_status = WorkRequestStatus.PROCESSING
        updated_work_request.request_status_reason = "SYNC JOB SUBMITTED"
        updated_work_request.job_submission_timestamp = utc_now()
        updated_work_request = self._controller.update_request(
            updated_work_request, retry_count=1
        )

        if updated_work_request is None:
            raise Exception("Failed to update workrequest [%d]" % self.work_request.id)

        ModelInstanceLogController.instance().log_instance(
            log_event=ModelInstanceLogEvent.INSTANCE_JOB_SUBMITTED,
            k8s_pod=self.pod,
        )

        return updated_work_request

    def run(self):
        try:
            updated_work_request, updated_pod = self._wait_for_pod()
            self.work_request = (
                updated_work_request
                if updated_work_request is not None
                else self.work_request
            )
            self.pod = updated_pod if updated_pod is not None else self.pod

            if self.model_execution_mode == ModelExecutionMode.ASYNC:
                updated_work_request = self._submit_job()
                self.work_request = (
                    updated_work_request
                    if updated_work_request is not None
                    else self.work_request
                )
                self._monitor_async_job()
            else:
                updated_work_request = self._submit_job_sync()
                self.work_request = (
                    updated_work_request
                    if updated_work_request is not None
                    else self.work_request
                )
        except:
            ContextLogger.error(
                self._logger_key,
                "Job submision failed for workrequest [%d] on pod [%s], error = [%s]"
                % (self.work_request.id, self.pod.name, repr(exc_info())),
            )
            traceback.print_exc(file=stdout)

        # NOTE: this is a bit dodge and we should update the ContextLogger to remove loggers
        del ContextLogger.instance().context_logger_map[self._logger_key]


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

    _job_submission_tasks: ThreadSafeCache[str, JobSubmissionTask]

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
        self._job_submission_tasks = ThreadSafeCache()

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

    def has_job_submission_task(self, work_request: WorkRequest) -> bool:
        return JobSubmissionTask.infer_id(work_request) in self._job_submission_tasks

    def get_job_submission_task(
        self, work_request: WorkRequest
    ) -> JobSubmissionTask | None:
        id = JobSubmissionTask.infer_id(work_request)

        if id not in self._job_submission_tasks:
            return None

        return self._job_submission_tasks[id]

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
    ):
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
        pod: K8sPod,
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

        _result_content: JobResult | None = result_content
        job_result_content = result_content

        # if not defined. we assume ASYNC mode
        if _result_content is None:
            _result_content = ModelIntegrationController.instance().get_job_result(
                work_request.model_id,
                str(work_request.id),
                pod.ip,
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
            return self._process_failed_job(work_request, reason="Job Result is empty")

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
        self, work_request: WorkRequest, pod: K8sPod
    ) -> WorkRequest:
        ContextLogger.trace(
            self._logger_key,
            "Handling [PROCESSING] workrequest [%d]..." % work_request.id,
        )

        # assume ASYNC if no job_submission_task present
        job_execution_mode: ModelExecutionMode = ModelExecutionMode.ASYNC
        job_status: JobStatus | None = None
        job_result: JobResult | None = None
        job_has_cached_results: bool = False
        job_non_cached_inputs: list[str] = work_request.request_payload.entries

        if self.has_job_submission_task(work_request):
            task = self._job_submission_tasks[JobSubmissionTask.infer_id(work_request)]

            if task.is_alive():
                ContextLogger.debug(
                    self._logger_key,
                    "JobSubmissionTask still in progress for workrequest [%d], ignoring PROCESSING state"
                    % work_request.id,
                )
                return work_request

            job_execution_mode = task.model_execution_mode
            job_status = task.job_status
            job_result = task.job_result
            job_has_cached_results = task.non_cached_inputs is None or len(
                task.non_cached_inputs
            ) != len(work_request.request_payload.entries)
            job_non_cached_inputs = task.non_cached_inputs

            # clear task
            del self._job_submission_tasks[task.id]

        try:
            updated_work_request: WorkRequest = None

            if job_status == JobStatus.COMPLETED:
                updated_work_request = self._process_completed_job(
                    work_request,
                    pod,
                    job_result,
                    has_cached_results=job_has_cached_results,
                    non_cached_inputs=job_non_cached_inputs,
                )
            elif job_status == JobStatus.FAILED:
                updated_work_request = self._process_failed_job(
                    work_request, has_cached_results=job_has_cached_results
                )
            else:
                ContextLogger.error(
                    self._logger_key,
                    "Job has non-completed state, but the JobSubmissionTask is completed - workrequest [%d], status [%s]"
                    % (work_request.id, job_status),
                )

            model_instance_handler = ModelInstanceController.instance().get_instance(
                work_request.model_id, str(work_request.id)
            )

            if model_instance_handler is None:
                ContextLogger.warn(
                    self._logger_key,
                    "Failed to terminate ModelInstanceHandler for workrequest [%d], model [%s] - reason = [Missing instance]"
                    % (work_request.id, work_request.model_id),
                )

                return updated_work_request

            model_instance_handler.kill()

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

                # flag the workload as new, for handling scenarios below
                potentially_new_workload = is_date_in_range_from_now(
                    work_request.last_updated, "-5m"
                )

                # TODO: [instances v2] change this to check if ModelInstance exists - WR is same server, so SHOULD have an instance
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
                    if self.has_job_submission_task(work_request):
                        ContextLogger.debug(
                            self._logger_key,
                            "Active JobSubmissionTask found for workrequest [%d], skipping"
                            % work_request.id,
                        )
                        continue
                    elif potentially_new_workload:
                        # might still be submitting the job
                        ContextLogger.warn(
                            self._logger_key,
                            "No JobId found for workrequest [%d], skipping due to age within [5]m"
                            % work_request.id,
                        )
                        continue
                    else:
                        ContextLogger.warn(
                            self._logger_key,
                            "WorkRequest [%d] in processing state, but does not have a JobId, assuming [FAILED]"
                            % work_request.id,
                        )

                        updated_work_request = self._controller.mark_workrequest_failed(
                            work_request
                        )

                        continue

                        # TODO: we should self-heal before this happens, this will be handled better with model-integration v2

                        # try:
                        #    updated_work_request = self._submit_job(work_request, pod)
                        # except:
                        #    ContextLogger.error(
                        #        self._logger_key,
                        #        "Failed to submit job, error = [%s]" % repr(exc_info()),
                        #    )
                        #    traceback.print_exc(file=stdout)

                        #    updated_work_request = (
                        #        self._controller.mark_workrequest_failed(work_request)
                        #    )
                        #    continue

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

                # TODO: [instances v2] check for model instance
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
        self,
        work_request: WorkRequest,
        pod: K8sPod,
        retry_count=1,
        non_cached_inputs: list[str] = None,
    ) -> WorkRequest:
        ContextLogger.debug(
            self._logger_key,
            "Submitting job to model [%s] for workrequest [%d]..."
            % (work_request.model_id, work_request.id),
        )

        if self.has_job_submission_task(work_request):
            ContextLogger.debug(
                self._logger_key,
                "Existing JobSubmissionTask for workrequest [%d], skipping."
                % work_request.id,
            )
            return work_request

        task = JobSubmissionTask(
            self._controller, work_request.copy(), pod, retry_count, non_cached_inputs
        )
        self._job_submission_tasks[task.id] = task
        task.start()

        return work_request

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

                # TODO: [instances v2] replace with ModelInstance creation + wait on pod created ??
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

                # TODO: [instances v2] can remove this once above pod creation is replaced
                ModelInstanceController.instance().request_instance(
                    work_request.model_id,
                    str(work_request.id),
                    ignore_max_concurrent_limit=True,
                )

                if updated_work_request is None:
                    raise Exception("Failed to persist updated WorkRequest")

                # throws exception on failure, which will be caught
                updated_work_request = self._submit_job(
                    updated_work_request, pod, non_cached_inputs=non_cached_inputs
                )
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

                # TODO: [instances v2] replace this with ModelInstanceController.ensure_instance_terminated(model_id, wr_id OR instance_name)
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
