from sys import exc_info, stdout
from threading import Event, Thread
import traceback
from typing import List, Union
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.thread_safe_list import ThreadSafeList

from library.process_lock import ProcessLock
from objects.k8s import ErsiliaAnnotations, K8sPod
from controllers.k8s import K8sController
from controllers.model import ModelController

from controllers.scaling_worker import ScalingWorker


class ScalingManagerKillInstance(KillInstance):
    def kill(self):
        ScalingManager.instance().kill()


class ScalingManager(Thread):

    WORKER_LOADBALANCE_WAIT_TIME = 20
    NUM_WORKERS = 1

    _instance: "ScalingManager" = None

    _logger_key: str = None
    _kill_event: Event

    _process_lock: ProcessLock

    _workers: ThreadSafeList[ScalingWorker]

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "ScalingManager"
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
    def initialize() -> "ScalingManager":
        if ScalingManager._instance is not None:
            return ScalingManager._instance

        ScalingManager._instance = ScalingManager()
        GracefulKiller.instance().register_kill_instance(ScalingManagerKillInstance())

        return ScalingManager._instance

    @staticmethod
    def instance() -> "ScalingManager":
        return ScalingManager._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _find_available_instances(self, model_id: str, request_id: str) -> List[K8sPod]:
        pods = K8sController.instance().load_model_pods(model_id)

        if len(pods) == 0:
            return []

        _available_pods: List[K8sPod] = []

        for pod in pods:
            _request_id_annotation = pod.get_annotation(
                ErsiliaAnnotations.REQUEST_ID.value
            )

            if _request_id_annotation is None or len(_request_id_annotation) == 0:
                _available_pods.append(pod)
            elif _request_id_annotation == request_id:
                return [pod]

        return _available_pods

    def _acquire_existing_instance(
        self, model_id: str, request_id: str
    ) -> Union[None, K8sPod]:
        _available_instances = self._find_available_instances(model_id, request_id)

        # check for existing annotation
        if len(_available_instances) == 1 and (
            _available_instances[0].annotation_equals(
                ErsiliaAnnotations.REQUEST_ID.value, str(request_id)
            )
        ):
            return _available_instances[0]

        if len(_available_instances) > 0:
            # NOTE: we loop over all instances and re-check the pod,
            #       another Scaler might have taken the pod since last checking
            for pod in _available_instances:
                checked_pod = K8sController.instance().get_pod(pod.name)
                _request_id_annotation = checked_pod.get_annotation(
                    ErsiliaAnnotations.REQUEST_ID.value
                )

                if (
                    _request_id_annotation is not None
                    and len(_request_id_annotation) > 0
                ):
                    continue

                acquired_pod = K8sController.instance().attach_work_request(
                    model_id, pod.name, request_id
                )

                if acquired_pod is not None:
                    return acquired_pod

        return None

    def acquire_instance(
        self, model_id: str, request_id: str, timeout: float = 30
    ) -> Union[None, K8sPod]:
        ContextLogger.debug(
            self._logger_key,
            "Acquiring instance for model [%s], request_id = [%s]..."
            % (model_id, request_id),
        )

        lock_acquired = False

        try:
            model = ModelController.instance().get_model(model_id)
            scaling_info = ModelController.instance().get_model_scaling_info(model_id)

            if scaling_info is None:
                raise Exception("No scaling info found for model")

            if not scaling_info.enabled:
                ContextLogger.warn(
                    self._logger_key,
                    "Model scaling is disabled, no instance will be provisioned",
                )
                return None

            if not self._process_lock.acquire_lock(model_id, timeout=timeout):
                raise Exception(
                    "Failed to acquire lock on model [%s] within [%d] seconds"
                    % (model_id, timeout)
                )

            lock_acquired = True
            _existing_instance = self._acquire_existing_instance(model_id, request_id)

            if _existing_instance is not None:
                return _existing_instance

            # if none found, check if scaling is at max, else scale up + redo instance check (with timeout on scale up)
            if (
                scaling_info.max_instances != -1
                and scaling_info.current_instances >= scaling_info.max_instances
            ):
                ContextLogger.warn(
                    self._logger_key,
                    "Scaling is at max instances [%d], no instance will be provisioned"
                    % scaling_info.max_instances,
                )
                return None

            new_pod = K8sController.instance().deploy_new_pod(
                model_id,
                model.details.k8s_resources,
                disable_memory_limit=model.details.disable_memory_limit,
                annotations=dict([(ErsiliaAnnotations.REQUEST_ID.value, request_id)]),
                model_template_version=model.details.template_version,
            )

            if new_pod is None:
                raise Exception("Failed to scale up model [%s]" % model_id)

            return new_pod
        except:
            error_str = (
                "Failed to acquire instance for model = [%s], request = [%s], error = [%s]"
                % (model_id, request_id, repr(exc_info()))
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

            return None
        finally:
            if lock_acquired:
                self._process_lock.release_lock(model_id)

    def release_instance(self, model_id: str, request_id: str) -> None:
        pods = K8sController.instance().load_model_pods(model_id)

        if len(pods) == 0:
            return

        # check for existing annotation
        for instance in pods:
            if not instance.annotation_equals(
                ErsiliaAnnotations.REQUEST_ID.value, request_id
            ):
                continue

            K8sController.instance().clear_work_request(model_id, instance.name)

    def _load_balance_workers(self):
        # TODO: change this to monitor current workers vs config and update worker models
        # TODO: check for disabled models (remove if ALL scaled down)
        # TODO: randomize order of models and round-robin between workers
        if len(self._workers) == ScalingManager.NUM_WORKERS:
            return

        models = ModelController.instance().get_models()

        worker = ScalingWorker(self._process_lock)
        worker.update_model_ids(list(map(lambda m: m.id, models)))
        worker.start()
        self._workers.append(worker)

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

        self._load_balance_workers()

        while True:
            if self._wait_or_kill(ScalingManager.WORKER_LOADBALANCE_WAIT_TIME):
                break

            try:
                self._load_balance_workers()
            except:
                error_str = "Failed to load balance workers, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

        self._stop_workers()

        ContextLogger.info(self._logger_key, "Controller stopped")
