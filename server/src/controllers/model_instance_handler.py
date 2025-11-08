import traceback
from datetime import datetime
from enum import Enum
from json import loads
from sys import exc_info, stdout
from threading import Event, Thread
from time import sleep
from typing import Dict, List, Union

from config.application_config import ApplicationConfig
from controllers.instance_metrics import InstanceMetricsController
from controllers.job_submission_process import JobSubmissionProcess
from controllers.k8s import K8sController
from controllers.model import ModelController
from controllers.model_instance_log import (
    ModelInstanceLogController,
    ModelInstanceLogEvent,
)
from controllers.s3_integration import S3IntegrationController
from controllers.server import ServerController
from db.daos.model_instance_log import (
    ModelInstanceLogDAO,
    ModelInstanceLogQuery,
    ModelInstanceLogRecord,
)
from objects.instance import ModelInstance
from objects.k8s import ErsiliaAnnotations, K8sPod
from python_framework.config_utils import load_environment_variable
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.thread_safe_cache import ThreadSafeCache
from python_framework.time import utc_now

from src.controllers.work_request import WorkRequestController
from src.objects.model import ModelExecutionMode
from src.objects.model_integration import JobStatus
from src.objects.work_request import WorkRequest, WorkRequestStatus

###
# The ModelInstanceHandler should control the entire life-cycle of a Model Instance
#   - pod creation
#   - job submission
#   - job status + result checking
#   - pod termination
#   - monitoring
#
###


class ModelInstanceState(Enum):
    REQUESTED = "REQUESTED"
    INITIALIZING = "INITIALIZING"
    WAITING_FOR_READINESS = "WAITING_FOR_READINESS"
    ACTIVE = "ACTIVE"
    SHOULD_TERMINATE = "SHOULD_TERMINATE"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class ModelInstanceControllerStub:
    def remove_instance(
        self, model_id: str, work_request_id: str, terminate: bool = False
    ):
        pass


class ModelInstanceHandler(Thread):
    _logger_key: str
    _kill_event: Event

    _controller: ModelInstanceControllerStub

    model_id: str
    work_request_id: str
    pod_name: str | None
    k8s_pod: K8sPod | None

    state: ModelInstanceState
    pod_exists: bool

    job_submission_process: JobSubmissionProcess | None
    job_submission_entries: list[str] | None

    def __init__(
        self,
        model_id: str,
        work_request_id: int,
        controller: ModelInstanceControllerStub,
        job_submission_entries: list[str] | None = None,
    ):
        Thread.__init__(self)

        self._logger_key = f"ModelInstanceHandler[{model_id}@{work_request_id}]"
        self._kill_event = Event()
        self._controller = controller

        self.model_id = model_id
        self.work_request_id = str(work_request_id)
        self.pod_name = None
        self.k8s_pod = None

        self.state = ModelInstanceState.REQUESTED
        self.pod_exists = False

        self.job_submission_process = None
        self.job_submission_entries = job_submission_entries

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    "LOG_LEVEL_ModelInstanceHandler", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()
        self.state = ModelInstanceState.SHOULD_TERMINATE

    def is_active(self) -> bool:
        return self.state not in [
            ModelInstanceState.SHOULD_TERMINATE,
            ModelInstanceState.TERMINATING,
            ModelInstanceState.TERMINATED,
        ]

    def _on_terminated(self):
        self.state = ModelInstanceState.TERMINATING

        InstanceMetricsController.instance().persist_metrics(
            "eos-models", self.pod_name
        )

        # remove pod from metricscontroller
        InstanceMetricsController.instance().remove_instance(
            "eos-models", self.pod_name
        )

        if self.job_submission_process is not None:
            try:
                if self.job_submission_process.is_alive():
                    self.job_submission_process.kill()
                    self.job_submission_process.join()
            except:
                pass

        if self.pod_exists:
            try:
                logs = K8sController.instance().download_pod_logs(
                    self.model_id, target_pod_name=self.pod_name
                )

                if logs is not None:
                    S3IntegrationController.instance().upload_instance_logs(
                        self.model_id, self.work_request_id, logs
                    )
            except:
                pass

            self._terminate_pod()

        self.state = ModelInstanceState.TERMINATED
        ContextLogger.info(self._logger_key, "Handler terminated")

        ModelInstanceLogController.instance().log_instance(
            ModelInstanceLogEvent.INSTANCE_TERMINATED,
            k8s_pod=self.k8s_pod,
            model_id=self.model_id,
            work_request_id=self.work_request_id,
        )

    def _finalize(self):
        ContextLogger.info(self._logger_key, "Handler finalized")
        del ContextLogger.instance().context_logger_map[self._logger_key]

        if self.job_submission_process is not None:
            try:
                self.job_submission_process.finalize()
            except:
                pass

        self._controller.remove_instance(self.model_id, self.work_request_id)

    def _create_pod(self) -> bool:
        try:
            model = ModelController.instance().get_model(self.model_id)

            if model is None:
                raise Exception("model [%s] not found" % self.model_id)

            if not model.enabled:
                raise Exception("model [%s] is disabled" % self.model_id)

            new_pod = K8sController.instance().deploy_new_pod(
                self.model_id,
                model.details.k8s_resources,
                disable_memory_limit=model.details.disable_memory_limit,
                annotations=dict(
                    [
                        (ErsiliaAnnotations.REQUEST_ID.value, self.work_request_id),
                        (
                            ErsiliaAnnotations.SERVER_ID.value,
                            ServerController.instance().server_id,
                        ),
                    ]
                ),
                model_template_version=model.details.template_version,
            )

            if new_pod is None:
                raise Exception("null pod on creation")

            self.k8s_pod = new_pod
            self.pod_name = new_pod.name
            self.pod_exists = True

            ModelInstanceLogController.instance().log_instance(
                ModelInstanceLogEvent.INSTANCE_POD_CREATED,
                k8s_pod=self.k8s_pod,
                model_id=self.model_id,
                work_request_id=self.work_request_id,
            )

            return True
        except:
            ContextLogger.error(
                self._logger_key, f"Failed to create pod, error = [{repr(exc_info())}]"
            )
            traceback.print_exc(file=stdout)

            self.state = ModelInstanceState.SHOULD_TERMINATE
            self.pod_exists = False

            ModelInstanceLogController.instance().log_instance(
                ModelInstanceLogEvent.INSTANCE_POD_CREATION_FAILED,
                model_id=self.model_id,
                work_request_id=self.work_request_id,
            )

            return False

    def _terminate_pod(self):
        if not self.pod_exists:
            return

        _pod_name = (
            self.pod_name
            if self.pod_name is not None
            else self.k8s_pod.name
            if self.k8s_pod is not None
            else None
        )

        if _pod_name is None:
            ContextLogger.warn(
                self._logger_key, "Failed to terminate pod, cannot determine name"
            )

            return

        try:
            if K8sController.instance().delete_pod(
                self.model_id, target_pod_name=_pod_name, force=True
            ):
                ContextLogger.debug(self._logger_key, "Pod [%s] terminated" % _pod_name)

                ModelInstanceLogController.instance().log_instance(
                    ModelInstanceLogEvent.INSTANCE_POD_TERMINATED,
                    k8s_pod=self.k8s_pod,
                    model_id=self.model_id,
                    work_request_id=self.work_request_id,
                )
            else:
                ContextLogger.warn(
                    self._logger_key,
                    "Pod [%s] termination failed - possibly already terminated"
                    % _pod_name,
                )
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to terminate pod [%s], error = %s"
                % (_pod_name, repr(exc_info())),
            )

    def _on_start(self) -> bool:
        if not self._create_pod():
            return False

        # load pod + state for first time
        if not self._check_pod_state(self.k8s_pod):
            return False

        # add pod to podmetricscontroller
        # TODO: need to add namespace to pod
        InstanceMetricsController.instance().register_instance(
            "eos-models", self.pod_name, self.model_id
        )

        return True

    # NOTE: theoretically, this will always return true after _on_start has been executed, till termination
    # NOTE: this is not checking if the pod is scheduled (started), only CREATED
    def wait_for_pod_created(self, timeout: int = 0) -> bool:
        if self.state in [
            ModelInstanceState.SHOULD_TERMINATE,
            ModelInstanceState.TERMINATING,
            ModelInstanceState.TERMINATED,
        ]:
            return False

        if self.k8s_pod is not None:
            return True

        start_time = 0 if timeout <= 0 else datetime.now().timestamp()

        while True:
            if self.k8s_pod is not None:
                return True

            sleep(2)

            if timeout > 0 and (datetime.now().timestamp() - start_time > timeout):
                ContextLogger.warn(
                    self._logger_key,
                    "wait_for_pod_created timeout [%d] reached" % timeout,
                )
                return False

    def wait_for_pod_ready(self, timeout: int = 0) -> bool:
        if self.k8s_pod is not None and self.k8s_pod.state.ready:
            return True

        start_time = 0 if timeout <= 0 else datetime.now().timestamp()

        while True:
            if self.k8s_pod is not None and self.k8s_pod.state.ready:
                return True

            sleep(2)

            if timeout > 0 and (datetime.now().timestamp() - start_time > timeout):
                ContextLogger.warn(
                    self._logger_key,
                    "wait_for_pod_ready timeout [%d] reached" % timeout,
                )
                return False

    def _check_pod_state(self, k8s_pod: K8sPod | None = None) -> bool:
        _k8s_pod: K8sPod | None = k8s_pod
        _initial_k8s_pod = _k8s_pod

        try:
            if _k8s_pod is None and self.pod_name is None:
                ContextLogger.debug(
                    self._logger_key,
                    f"Loading pod by request model_id = [{self.model_id}], request_id = [{self.work_request_id}]...",
                )
                _k8s_pod = K8sController.instance().get_pod_by_request(
                    self.model_id, self.work_request_id
                )
            else:
                ContextLogger.debug(
                    self._logger_key, f"Loading pod by name = [{self.pod_name}]..."
                )
                _k8s_pod = K8sController.instance().get_pod(self.pod_name)

            if _k8s_pod is None:
                ContextLogger.warn(
                    self._logger_key, "Pod missing, likely terminated by k8s"
                )
                self.state = ModelInstanceState.SHOULD_TERMINATE
                self.pod_exists = False

                return False

            self.k8s_pod = _k8s_pod
            self.pod_name = _k8s_pod.name
            self.pod_exists = True

            # update log
            if _initial_k8s_pod is None:
                # NOTE: pod creation is logged in create_pod method
                pass
            elif (
                _initial_k8s_pod.state.ready != _k8s_pod.state.ready
                or _initial_k8s_pod.state.phase != _k8s_pod.state.phase
            ):
                if not _initial_k8s_pod.state.ready and _k8s_pod.state.ready:
                    ModelInstanceLogController.instance().log_instance(
                        log_event=ModelInstanceLogEvent.INSTANCE_POD_READY,
                        k8s_pod=_k8s_pod,
                    )

            # update instance state
            if (
                self.k8s_pod.state.phase == "Terminating"
                or self.k8s_pod.state.phase == "Terminated"
            ):
                self.state = ModelInstanceState.SHOULD_TERMINATE
            elif self.k8s_pod.state.ready:
                self.state = ModelInstanceState.ACTIVE

            return True
        except:
            ContextLogger.error(
                self._logger_key, f"Failed to find pod, error = [{repr(exc_info())}]"
            )
            traceback.print_exc(file=stdout)

            self.state = ModelInstanceState.SHOULD_TERMINATE
            self.pod_exists = False

            return False

    def _submit_job(self) -> bool:
        # NOTE: we only allow job submission ONCE per model instance (for now)
        #       if submission failed for any reason, we need to restart the instance
        if self.job_submission_process is not None:
            ContextLogger.warn(self._logger_key, "JobSubmissionProcess already exists, not re-submitting job")
            return False
        
        if self.job_submission_entries is None or len(self.job_submission_entries) == 0:
            ContextLogger.warn(self._logger_key, "Cannot submit job, no job entries defined")
            return False

        work_request: WorkRequest | None = None

        try:
            work_request = WorkRequestController.instance().get_requests(
                id=self.work_request_id
            )[0]

            _job_entries =  self.work_request.request_payload.entries
            if self.non_cached_inputs is None            if self.non_cached_inputs is None
            else self.non_cached_inputs            else self.non_cached_inputs
            self.job_submission_process = JobSubmissionProcess(
                self.model_id, self.work_request_id, _job_entries, self.k8s_pod
            )

            if not self.job_submission_process.submit_job():
                ContextLogger.warn(self._logger_key, "Failed to submit job")

                return False

            ModelInstanceLogController.instance().log_instance(
                log_event=ModelInstanceLogEvent.INSTANCE_JOB_SUBMITTED,
                k8s_pod=self.pod,
            )
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to submit job, error = [%s]" % repr(exc_info()),
            )

            return False

        updated_work_request: WorkRequest | None = work_request.copy()
        updated_work_request.request_status = WorkRequestStatus.PROCESSING
        updated_work_request.model_job_id = (
            self.job_submission_process.job_id
            if self.job_submission_process.model_execution_mode
            == ModelExecutionMode.ASYNC
            else "SYNC"
        )
        updated_work_request.request_status_reason = (
            "JOB SUBMITTED"
            if self.job_submission_process.model_execution_mode
            == ModelExecutionMode.ASYNC
            else "SYNC JOB SUBMITTED"
        )
        updated_work_request.job_submission_timestamp = utc_now()
        updated_work_request = WorkRequestController.instance().update_request(
            updated_work_request, retry_count=1
        )

        if updated_work_request is None:
            ContextLogger.error(
                self._logger_key,
                "Failed to update workrequest [%d] with new job_id" % work_request.id,
            )

        return True

    def _handle_job_submission_process(self):
        try:
            if self.job_submission_process.handle_job_completion():
                self.state = ModelInstanceState.SHOULD_TERMINATE
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to handle job submission process, error = [%s]"
                % repr(exc_info()),
            )

    def is_job_completed(self) -> bool:
        return (
            self.job_submission_process is not None
            and self.job_submission_process.job_status
            in [JobStatus.COMPLETED, JobStatus.FAILED]
        )

    def run(self):
        ContextLogger.info(self._logger_key, "Starting handler")

        try:
            if self._on_start():
                ModelInstanceLogController.instance().log_instance(
                    ModelInstanceLogEvent.INSTANCE_CREATED,
                    k8s_pod=self.k8s_pod,
                    model_id=self.model_id,
                    work_request_id=self.work_request_id,
                )

                while True:
                    if self._wait_or_kill(5):
                        break

                    _ = self._check_pod_state()

                    if self.state == ModelInstanceState.SHOULD_TERMINATE:
                        break

                    if self.job_submission_process is None:
                        # only submit job once pod is created and in READY state
                        if (
                            not self.pod_exists
                            or self.state != ModelInstanceState.ACTIVE
                            or self.k8s_pod is None
                            or not self.k8s_pod.state.ready
                        ):
                            continue

                        if not self._submit_job():
                            ModelInstanceLogController.instance().log_instance(
                                ModelInstanceLogEvent.INSTANCE_JOB_SUBMISSION_FAILED,
                                model_id=self.model_id,
                                work_request_id=self.work_request_id,
                            )

                            break
                    else:
                        self._handle_job_submission_process()

                        if self.state == ModelInstanceState.SHOULD_TERMINATE:
                            break
            else:
                ModelInstanceLogController.instance().log_instance(
                    ModelInstanceLogEvent.INSTANCE_CREATION_FAILED,
                    model_id=self.model_id,
                    work_request_id=self.work_request_id,
                )
        finally:
            self._on_terminated()

        # NOTE: we only want to "finalize" once the instance is marked for "kill"
        #       this happens after the WorkRequest has completed processing
        while True:
            if self._wait_or_kill(10):
                break

        self._finalize()


class ModelInstanceControllerKillInstance(KillInstance):
    def kill(self):
        ModelInstanceController.instance().kill()


class ModelInstanceController:
    _instance: "ModelInstanceController" = None
    _logger_key: str = None

    model_instance_handlers: ThreadSafeCache[str, ModelInstanceHandler]

    max_instances_limit: int

    def __init__(self):
        self._logger_key = "ModelInstanceController"

        self.model_instance_handlers = ThreadSafeCache()
        self.max_instances_limit = int(
            load_environment_variable("MAX_CONCURRENT_MODEL_INSTANCES", default="25")
        )

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "ModelInstanceController":
        if ModelInstanceController._instance is not None:
            return ModelInstanceController._instance

        ModelInstanceController._instance = ModelInstanceController()
        GracefulKiller.instance().register_kill_instance(
            ModelInstanceControllerKillInstance()
        )

        return ModelInstanceController._instance

    @staticmethod
    def instance() -> "ModelInstanceController":
        return ModelInstanceController._instance

    def kill(self):
        for handler in self.model_instance_handlers.values():
            handler.kill()

        for handler in self.model_instance_handlers.values():
            handler.join()

    def max_instances_limit_reached(self) -> bool:
        ContextLogger.debug(
            self._logger_key,
            f"curr instance = [{len(self.model_instance_handlers)}], max = [{self.max_instances_limit}]",
        )
        return len(self.model_instance_handlers) >= self.max_instances_limit

    def request_instance(
        self,
        model_id: str,
        work_request_id: str,
        ignore_max_concurrent_limit: bool = False,
        job_submission_entries: list[str] | None = None,
    ) -> ModelInstanceHandler:
        if not ignore_max_concurrent_limit and self.max_instances_limit_reached():
            raise Exception("Max Concurrent Model Instances reached")

        key = f"{model_id}-wr:{work_request_id}"

        if key in self.model_instance_handlers:
            return self.model_instance_handlers[key]

        handler = ModelInstanceHandler(model_id, work_request_id, self, job_submission_entries)
        self.model_instance_handlers[key] = handler
        handler.start()

        ModelInstanceLogController.instance().log_instance(
            ModelInstanceLogEvent.INSTANCE_REQUESTED,
            model_id=model_id,
            work_request_id=work_request_id,
        )

        return handler

    def remove_instance(
        self, model_id: str, work_request_id: str, terminate: bool = False
    ):
        key = f"{model_id}_{work_request_id}"

        if key not in self.model_instance_handlers:
            return

        if terminate:
            self.model_instance_handlers[key].kill()

        del self.model_instance_handlers[key]

    def get_instance(
        self, model_id: str, work_request_id: int
    ) -> Union[ModelInstanceHandler, None]:
        key = f"{model_id}_{work_request_id}"

        if key in self.model_instance_handlers:
            return self.model_instance_handlers[key]

        return None

    def load_active_instances(
        self, model_ids: List[str] = None, work_request_id: Union[str, None] = None
    ) -> List[ModelInstance]:
        active_instances: List[ModelInstance] = []

        for handler in self.model_instance_handlers.values():
            # TODO: apply filters

            if handler.k8s_pod is None:
                continue

            metrics = InstanceMetricsController.instance().get_instance(
                handler.k8s_pod.namespace, handler.k8s_pod.name
            )

            active_instances.append(ModelInstance(handler.k8s_pod, metrics))

        return active_instances

    def load_persisted_instances(
        self,
        model_ids: List[str] = None,
        work_request_id: Union[str, None] = None,
        instance_id: Union[str, None] = None,
    ) -> List[ModelInstance]:
        instances: Dict[str, ModelInstance] = {}
        log_model_ids: List[str] = []
        log_instance_ids: List[str] = []

        try:
            instance_log_records: List[ModelInstanceLogRecord] = (
                ModelInstanceLogDAO.execute_query(
                    ModelInstanceLogQuery.SELECT_FILTERED,
                    ApplicationConfig.instance().database_config,
                    query_kwargs={
                        "model_ids": model_ids,
                        "instance_ids": None if instance_id is None else [instance_id],
                        "correlation_ids": (
                            None if work_request_id is None else [work_request_id]
                        ),
                        "log_events": ["INSTANCE_READY"],
                    },
                )
            )

            if instance_log_records is None or len(instance_log_records) == 0:
                return []

            for record in instance_log_records:
                instances[record.instanceid] = ModelInstance(
                    K8sPod.from_object(loads(record.instance_details)), None
                )

                if record.instanceid not in log_instance_ids:
                    log_instance_ids.append(record.instanceid)

                if record.modelid not in log_model_ids:
                    log_model_ids.append(record.modelid)
        except:
            error_str = "Failed to load ModelInstanceLogs, error = [%s]" % (
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

            return []

        try:
            instance_metrics = InstanceMetricsController.instance().load_persisted(
                log_model_ids, log_instance_ids
            )

            for metrics in instance_metrics:
                if metrics.instance_id not in instances:
                    continue

                instances[metrics.instance_id].metrics = metrics
        except:
            error_str = "Failed to load InstanceMetrics from DB, error = [%s]" % (
                repr(exc_info())
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return list(instances.values())

    def ensure_instance_terminated(
        self, model_id: str, work_request_id: int, wait: bool = False
    ):
        instance = self.get_instance(model_id, work_request_id)

        if instance is None:
            ContextLogger.debug(
                self._logger_key,
                "No instance found for model [%s], workrequest [%d]"
                % (model_id, work_request_id),
            )
            return

        instance.kill()

        if wait:
            instance.join()
