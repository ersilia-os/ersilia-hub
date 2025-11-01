import traceback
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep

from controllers.model import ModelController
from controllers.model_integration import ModelIntegrationController
from objects.k8s import K8sPod
from objects.model import ModelExecutionMode
from objects.model_integration import JobResult, JobStatus
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel


class JobSubmissionProcess(Thread):
    _logger_key: str
    _kill_event: Event

    model_id: str
    work_request_id: str
    id: str
    pod: K8sPod
    job_entries: list[str]
    retry_count: int
    model_execution_mode: ModelExecutionMode
    job_result: JobResult | None
    job_id: str | None
    job_status: JobStatus
    job_status_reason: str | None

    def __init__(
        self,
        model_id: str,
        work_request_id: str,
        job_entries: list[str],
        pod: K8sPod,
        retry_count: int = 1,
    ):
        Thread.__init__(self)

        self.model_id = model_id
        self.work_request_id = work_request_id
        self.id = f"{model_id}_{work_request_id}"
        self.job_entries = job_entries
        self.pod = pod
        self.retry_count = retry_count

        self._logger_key = "JobSubmissionProcess[%s]" % self.id
        self._kill_event = Event()

        self.model_execution_mode = (
            ModelController.instance().get_model(model_id).details.execution_mode
        )
        self.job_result = None
        self.job_id = None
        self.job_status = JobStatus.PENDING
        self.job_status_reason = None

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    "LOG_LEVEL_JobSubmissionProcess", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _submit_job(self) -> bool:
        ContextLogger.debug(
            self._logger_key,
            "Submitting job to model [%s] for workrequest [%s] with inputs [%d]..."
            % (self.model_id, self.work_request_id, len(self.job_entries)),
        )

        attempt_count = 0
        job_submission_response: JobSubmissionProcess | None = None

        while attempt_count <= self.retry_count:
            try:
                job_submission_response = (
                    ModelIntegrationController.instance().submit_job(
                        self.model_id,
                        str(self.work_request_id),
                        self.pod.ip,
                        self.job_entries,
                    )
                )

                break
            except:
                error_str = (
                    "Failed to submit job for instance [%s], workrequest [%s], error [%s]"
                    % (self.pod.name, self.work_request_id, repr(exc_info()))
                )

                if attempt_count < self.retry_count:
                    ContextLogger.warn(self._logger_key, error_str)
                else:
                    ContextLogger.error(self._logger_key, error_str)
                    return False

            attempt_count += 1

        if job_submission_response is None:
            ContextLogger.error(
                self._logger_key,
                "Failed to submit job for instance [%s], workrequest [%s] after [%d] attempts"
                % (self.pod.name, self.work_request_id, attempt_count),
            )

            return False

        self.job_id = job_submission_response.job_id

        return True

    # TODO: [job v2] call this from model instance as part of check_job_process
    def check_job_completed(self) -> bool:
        if self.job_status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return True

        # cannot check SYNC jobs, so if the status is unknown, it's not completed yet
        if self.model_execution_mode == ModelExecutionMode.SYNC:
            return False

        status_response = ModelIntegrationController.instance().get_job_status(
            self.model_id,
            str(self.work_request_id),
            self.pod.ip,
            self.job_id,
        )

        if status_response.status not in [JobStatus.COMPLETED, JobStatus.FAILED]:
            ContextLogger.debug(
                self._logger_key,
                "Job still processing for workrequest [%s]..." % self.work_request_id,
            )

            return False

        if status_response.status == JobStatus.COMPLETED:
            ContextLogger.debug(self._logger_key, "Job COMPLETED")

            self.job_result = ModelIntegrationController.instance().get_job_result(
                self.model_id,
                str(self.work_request_id),
                self.pod.ip,
                self.job_id,
            )
        elif status_response.status == JobStatus.FAILED:
            ContextLogger.debug(self._logger_key, "Job FAILED")

        self.job_status = status_response.status

        return True

    def _monitor_async_job(self):
        if self.model_execution_mode == ModelExecutionMode.SYNC:
            return

        while True:
            if self.check_job_completed():
                break

            sleep(15)

    def _submit_job_sync(self) -> bool:
        ContextLogger.debug(
            self._logger_key,
            "Submitting SYNC job to model [%s] for workrequest [%s] with inputs [%d] ..."
            % (self.model_id, self.work_request_id, len(self.job_entries)),
        )

        attempt_count = 0

        while attempt_count <= self.retry_count:
            try:
                (
                    self.job_status,
                    self.job_status_reason,
                    self.job_result,
                ) = ModelIntegrationController.instance().submit_job_sync(
                    self.model_id,
                    str(self.work_request_id),
                    self.pod.ip,
                    self.job_entries,
                )

                break
            except:
                error_str = (
                    "Failed to submit SYNC job for instance [%s], workrequest [%s], error [%s]"
                    % (self.pod.name, self.work_request_id, repr(exc_info()))
                )

                if attempt_count < self.retry_count:
                    ContextLogger.warn(self._logger_key, error_str)
                else:
                    ContextLogger.error(self._logger_key, error_str)
                    return False

            attempt_count += 1

        if self.job_result is None or self.job_status == JobStatus.FAILED:
            ContextLogger.error(
                self._logger_key,
                "Failed to submit SYNC job for instance [%s], workrequest [%s] after [%d] attempts"
                % (self.pod.name, self.work_request_id, attempt_count),
            )

            return False

        return True

    def submit_job(self) -> bool:
        try:
            if self.model_execution_mode == ModelExecutionMode.ASYNC:
                return self._submit_job()
            else:
                self.start()

                return True
        except:
            ContextLogger.error(
                self._logger_key,
                "Job submision failed for workrequest [%s] on pod [%s], error = [%s]"
                % (self.work_request_id, self.pod.name, repr(exc_info())),
            )
            traceback.print_exc(file=stdout)

            return False

    def finalize(self):
        del ContextLogger.instance().context_logger_map[self._logger_key]

    def run(self):
        ContextLogger.debug(self._logger_key, "Process started")

        try:
            if self.model_execution_mode == ModelExecutionMode.ASYNC:
                if self._submit_job():
                    self._monitor_async_job()
            else:
                self._submit_job_sync()
        except:
            ContextLogger.error(
                self._logger_key,
                "Job submision failed for workrequest [%s] on pod [%s], error = [%s]"
                % (self.work_request_id, self.pod.name, repr(exc_info())),
            )
            traceback.print_exc(file=stdout)

        ContextLogger.debug(self._logger_key, "Process completed")
