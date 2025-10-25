import traceback
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep, time
from typing import Tuple

from controllers.k8s import K8sController
from controllers.model import ModelController
from controllers.model_instance_log import (
    ModelInstanceLogController,
    ModelInstanceLogEvent,
)
from controllers.model_integration import ModelIntegrationController
from objects.k8s import K8sPod
from objects.model import ModelExecutionMode
from objects.model_integration import JobResult, JobStatus
from objects.work_request import WorkRequest, WorkRequestStatus
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel
from python_framework.time import (
    utc_now,
)

from src.controllers.work_request import WorkRequestController


class JobSubmissionTask(Thread):
    _logger_key: str
    _kill_event: Event

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
        work_request: WorkRequest,
        pod: K8sPod,
        retry_count: int = 1,
        non_cached_inputs: list[str] | None = None,
    ):
        Thread.__init__(self)

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

    # TODO: [instance v2 - job] move this to instance handler
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
            log_event=ModelInstanceLogEvent.INSTANCE_POD_READY,
            k8s_pod=_pod,
        )

        updated_work_request: WorkRequest = self.work_request.copy()

        try:
            updated_work_request.pod_ready_timestamp = utc_now()
            _updated_work_request = WorkRequestController.instance().update_request(
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
        updated_work_request = WorkRequestController.instance().update_request(
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
        updated_work_request = WorkRequestController.instance().update_request(
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
