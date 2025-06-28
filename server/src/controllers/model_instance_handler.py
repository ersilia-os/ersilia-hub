from enum import Enum
from sys import exc_info, stdout
from threading import Event, Thread
import traceback
from typing import Union

from controllers.k8s import K8sController
from server.src.controllers.instance_metrics import InstanceMetricsController
from objects.k8s import K8sPod
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.thread_safe_cache import ThreadSafeCache

###
# The ModelInstanceHandler should control the entire life-cycle of a Model Instance
#   - pod creation
#   - job submission
#   - job status + result checking
#   - pod termination
#   - monitoring
#
# TODO: eventually, we should merge the current JobSubmissionTask (thread) with this handler
# TODO: move the pod creation stuff from k8s to here, keep k8s integration there but move template stuff
# TODO: handle startup and termination here
# NOTE: ! no major changes required on WorkRequestWorker really, just integrate with this class instead of k8scontroller directly
###


class ModelInstanceState(Enum):

    REQUESTED = "REQUESTED"
    INITIALIZING = "INITIALIZING"
    WAITING_FOR_READINESS = "WAITING_FOR_READINESS"
    ACTIVE = "ACTIVE"
    SHOULD_TERMINATE = "SHOULD_TERMINATE"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"


class ModelInstanceHandler(Thread):

    _logger_key: str = None
    _kill_event: Event

    model_id: str
    work_request_id: str
    pod_name: Union[str, None]
    k8s_pod: K8sPod

    state: ModelInstanceState

    def __init__(self, model_id: str, work_request_id: str):
        super().__init__(self)

        self._logger_key = f"ModelInstanceHandler[{model_id}@{work_request_id}]"
        self._kill_event = Event()

        self.model_id = model_id
        self.work_request_id = work_request_id
        self.pod_name = None
        self.k8s_pod = None

        self.state = ModelInstanceState.REQUESTED

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_ModelInstanceHandler", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _on_terminated(self):
        self.state = ModelInstanceState.TERMINATING

        InstanceMetricsController.instance().persist_metrics(
            "eos-models", self.pod_name
        )

        # remove pod from metricscontroller
        InstanceMetricsController.instance().remove_pod("eos-models", self.pod_name)

        try:
            K8sController.instance().delete_pod(
                self.model_id, target_pod_name=self.pod_name
            )
        except:
            pass

        # TODO: wait for pod to be GONE

        self.state = ModelInstanceState.TERMINATED

    def _finalize(self):
        del ContextLogger.instance().context_logger_map[self._logger_key]

    def _on_start(self):
        # TODO: eventually start pod here

        # load pod + state for first time
        self._check_pod_state()

        # add pod to podmetricscontroller
        # TODO: need to add namespace to pod
        InstanceMetricsController.instance().register_pod("eos-models", self.pod_name)

    def _check_pod_state(self):
        k8s_pod: Union[K8sPod, None] = None

        try:
            if self.pod_name is None:
                k8s_pod = K8sController.instance().get_pod_by_request(
                    self.model_id, self.work_request_id
                )
            else:
                k8s_pod = K8sController.instance().get_pod(self.pod_name)

            if k8s_pod is None:
                ContextLogger.warn(
                    self._logger_key, "Pod missing, likely terminated by k8s"
                )
                self.state = ModelInstanceState.SHOULD_TERMINATE

                return

            self.k8s_pod = k8s_pod
            self.pod_name = k8s_pod.name

            if (
                self.k8s_pod.state.phase == "Terminating"
                or self.k8s_pod.state.phase == "Terminated"
            ):
                self.state = ModelInstanceState.SHOULD_TERMINATE
            elif self.k8s_pod.state.ready:
                self.state = ModelInstanceState.ACTIVE

            # TODO: update state e.g. readiness + active
        except:
            ContextLogger.error(
                self._logger_key, f"Failed to find pod, error = [{repr(exc_info())}]"
            )
            traceback.print_exc(file=stdout)

            self.state = ModelInstanceState.SHOULD_TERMINATE

    def run(self):
        ContextLogger.info(self._logger_key, "Starting handler")

        self._on_start()

        while True:
            if self._wait_or_kill(10):
                break

            self._check_pod_state()

            if self.state == ModelInstanceState.SHOULD_TERMINATE:
                break

        self._on_terminated()
        self._finalize()

        ContextLogger.info(self._logger_key, "Handler terminated")


class ModelInstanceControllerKillInstance(KillInstance):
    def kill(self):
        ModelInstanceController.instance().kill()


class ModelInstanceController:

    _instance: "ModelInstanceController" = None
    _logger_key: str = None

    model_instance_handlers: ThreadSafeCache[str, ModelInstanceHandler]

    def __init__(self):
        super().__init__(self)

        self._logger_key = "ModelInstanceController"

        self.model_instance_handlers = ThreadSafeCache()

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

    def request_instance(
        self, model_id: str, work_request_id: str
    ) -> ModelInstanceHandler:
        key = f"{model_id}_{work_request_id}"

        if key in self.model_instance_handlers:
            return self.model_instance_handlers[key]

        handler = ModelInstanceHandler(model_id, work_request_id)
        self.model_instance_handlers[key] = handler
        handler.start()

        return handler

    def get_instance(
        self, model_id: str, work_request_id: str
    ) -> Union[ModelInstanceHandler, None]:
        key = f"{model_id}_{work_request_id}"

        if key in self.model_instance_handlers:
            return self.model_instance_handlers[key]

        return None
