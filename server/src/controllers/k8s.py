from sys import exc_info, stdout
import traceback
from typing import Dict, List, Union
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from kubernetes import client, config
from kubernetes.client import (
    CoreV1Api,
    AppsV1Api,
    V1PodList,
    V1Pod,
    V1PodTemplateList,
    V1NodeList,
    V1Node,
)
from objects.k8s import (
    ErsiliaAnnotations,
    K8sNode,
    K8sPod,
    K8sPodTemplate,
    ErsiliaLabels,
)
from library.process_lock import ProcessLock
from subprocess import Popen
from threading import Thread, Event
from python_framework.graceful_killer import GracefulKiller, KillInstance

from python_framework.thread_safe_cache import ThreadSafeCache

from controllers.model_instance_log import (
    ModelInstanceLogController,
    ModelInstanceLogEvent,
)


class K8sControllerKillInstance(KillInstance):
    def kill(self):
        K8sController.instance().kill()


class K8sController(Thread):

    UPDATE_WAIT_TIME = 30
    MODEL_LABEL_SELECTOR = "app.kubernetes.io/component=model"
    MODELTEMPLATE_LABEL_SELECTOR = "app.kubernetes.io/component=model-template"

    _instance: "K8sController" = None

    _logger_key: str = None
    _kill_event: Event
    _namespace: str
    _api_apps: AppsV1Api
    _api_core: CoreV1Api

    _process_lock: ProcessLock

    _template_cache: ThreadSafeCache[str, K8sPodTemplate]

    def __init__(self, namespace: str, load_k8s_in_cluster: bool):
        Thread.__init__(self)

        self._logger_key = "K8sController"
        self._kill_event = Event()

        self._namespace = namespace
        self._process_lock = ProcessLock()
        self._template_cache = None

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

        ContextLogger.info(self._logger_key, "Initializing k8s client...")

        if load_k8s_in_cluster:
            # TODO: load in cluster service account
            config.load_incluster_config()
        else:
            config.load_kube_config()

        self._api_apps = client.AppsV1Api()
        self._api_core = client.CoreV1Api()

        ContextLogger.info(self._logger_key, "k8s client initialized.")

    @staticmethod
    def initialize() -> "K8sController":
        if K8sController._instance is not None:
            return K8sController._instance

        K8sController._instance = K8sController(
            load_environment_variable("MODELS_NAMESPACE"),
            (
                load_environment_variable(
                    "LOAD_K8S_IN_CLUSTER", default="FALSE"
                ).upper()
                == "TRUE"
            ),
        )
        GracefulKiller.instance().register_kill_instance(K8sControllerKillInstance())

        return K8sController._instance

    @staticmethod
    def instance() -> "K8sController":
        return K8sController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _release_lock(
        self, model_id: str, pod_name: str = None, timeout: float = -1
    ) -> None:
        _lock_id = model_id if pod_name is None else f"{model_id}_{pod_name}"
        self._process_lock.release_lock(_lock_id)

    # NOTE: THIS IS NOT SAFE ACROSS MULTIPLE INSTANCES
    def _acquire_lock(
        self, model_id: str, pod_name: str = None, timeout: float = -1
    ) -> bool:
        _lock_id = model_id if pod_name is None else f"{model_id}_{pod_name}"

        return self._process_lock.acquire_lock(_lock_id, timeout=timeout)

    def create_model_pod(
        self,
        model_id: str,
        size_megabytes: int,
        disable_memory_limit: bool,
        annotations: Dict[str, str] = None,
        model_template_version: str = "0.0.0",
    ) -> Union[None | K8sPod]:
        ContextLogger.debug(
            self._logger_key,
            "Creating pod for model [%s]%s"
            % (
                model_id,
                "" if annotations is None else " with annotations [%s]" % annotations,
            ),
        )

        _pod: V1Pod = None

        template_key = f"model-template_{model_template_version}"

        if template_key not in self._template_cache:
            raise Exception("Missing k8s template [%s]" % template_key)

        template = (
            self._template_cache[template_key]
            .copy()
            .transform_for_model(model_id, size_megabytes, disable_memory_limit)
        )
        ContextLogger.trace(
            self._logger_key, "pod template [%s]" % template.to_object()
        )
        _pod = template.to_pod()

        if annotations is not None:
            for key, value in annotations.items():
                _pod.metadata.annotations[key] = value

        _created_pod = self._api_core.create_namespaced_pod(self._namespace, _pod)

        if _created_pod is None:
            raise Exception(
                "Failed to create model pod - pod failed to apply, error = [%s]"
                % repr(exc_info())
            )

        k8s_pod = K8sPod.from_k8s(_created_pod)

        ModelInstanceLogController.instance().log_instance(
            log_event=ModelInstanceLogEvent.INSTANCE_CREATED, k8s_pod=k8s_pod
        )

        ContextLogger.info(
            self._logger_key,
            "Pod created for model id [%s], podname [%s]" % (model_id, k8s_pod.name),
        )

        return k8s_pod

    def load_model_pods(self, model_id: str = None) -> List[K8sPod]:
        pods: List[K8sPod] = []
        continue_token: str = None
        label_selector = K8sController.MODEL_LABEL_SELECTOR

        if model_id is not None:
            label_selector = (
                f"{label_selector},app.kubernetes.io/instance=model-{model_id}"
            )

        while True:
            pod_list: V1PodList = self._api_core.list_namespaced_pod(
                self._namespace,
                label_selector=label_selector,
                _continue=continue_token,
            )

            for pod in pod_list.items:
                pods.append(K8sPod.from_k8s(pod))

            if pod_list.metadata._continue is None:
                break

            continue_token = pod_list.metadata._continue

        return pods

    def get_pod(self, pod_name: str) -> K8sPod:
        pod = self._api_core.read_namespaced_pod(pod_name, self._namespace)

        if pod is None:
            return None

        return K8sPod.from_k8s(pod)

    def get_pod_by_request(self, model_id: str, request_id: str) -> Union[K8sPod, None]:
        pods = self.load_model_pods(model_id)

        for pod in pods:
            if pod.annotation_equals(
                ErsiliaAnnotations.REQUEST_ID.value, str(request_id)
            ):
                return pod

        return None

    def attach_work_request(
        self, model_id: str, pod_name: str, request_id: str
    ) -> Union[K8sPod, None]:
        _lock_acquired = False

        try:
            current_pod = self.get_pod(pod_name)

            if current_pod is None:
                return None

            ModelInstanceLogController.instance().log_instance(
                log_event=ModelInstanceLogEvent.INSTANCE_QUERIED, k8s_pod=current_pod
            )

            if not self._acquire_lock(model_id, pod_name):
                raise Exception(
                    "Failed to acquire lock on model = [%s], pod = [%s], error = [%s]"
                    % (model_id, pod_name, repr(exc_info()))
                )

            _lock_acquired = True

            patch = (
                []
                if len(current_pod.annotations) > 0
                else [{"op": "add", "path": "/metadata/annotations", "value": {}}]
            )
            patch.append(
                {
                    "op": "add",
                    "path": "/metadata/annotations/%s"
                    % ErsiliaAnnotations.REQUEST_ID.value,
                    "value": str(request_id),
                }
            )

            # NOTE: error should bubble up?
            patched_pod = self._api_core.patch_namespaced_pod(
                pod_name, self._namespace, patch
            )

            k8s_pod = None if patched_pod is None else K8sPod.from_k8s(patched_pod)

            if k8s_pod is not None:
                ModelInstanceLogController.instance().log_instance(
                    log_event=ModelInstanceLogEvent.INSTANCE_UPDATED, k8s_pod=k8s_pod
                )

            return k8s_pod
        finally:
            if _lock_acquired:
                self._release_lock(model_id, pod_name)

    def clear_work_request(self, model_id: str, pod_name: str) -> Union[K8sPod, None]:
        _lock_acquired = False

        try:
            current_pod = self.get_pod(pod_name)

            if current_pod is None:
                return None

            ModelInstanceLogController.instance().log_instance(
                log_event=ModelInstanceLogEvent.INSTANCE_QUERIED, k8s_pod=current_pod
            )

            if len(current_pod.annotations) == 0:
                # already removed
                return current_pod

            if not self._acquire_lock(model_id, pod_name):
                raise Exception(
                    "Failed to acquire lock on model = [%s], pod = [%s], error = [%s]"
                    % (model_id, pod_name, repr(exc_info()))
                )

            _lock_acquired = True

            patch = [
                {
                    "op": "remove",
                    "path": "/metadata/annotations/%s"
                    % ErsiliaAnnotations.REQUEST_ID.value,
                }
            ]

            # NOTE: error should bubble up?
            patched_pod = self._api_core.patch_namespaced_pod(
                pod_name, self._namespace, patch
            )

            k8s_pod = None if patched_pod is None else K8sPod.from_k8s(patched_pod)

            if k8s_pod is not None:
                ModelInstanceLogController.instance().log_instance(
                    log_event=ModelInstanceLogEvent.INSTANCE_UPDATED, k8s_pod=k8s_pod
                )

            return k8s_pod
        finally:
            if _lock_acquired:
                self._release_lock(model_id, pod_name)

    # find pod(s) to delete
    # 1. check pod_name
    # 2. check if no request assigned
    # 3. if no request assigned, check age (must be at least 60s old), else we might delete currently scaling pods
    def _get_scale_down_candidate_pods(
        self,
        current_pods: List[K8sPod],
        scale_down_count: int,
        target_pod_name: str = None,
    ) -> List[K8sPod]:
        candidate_pods: List[K8sPod] = []
        _candidate_names: List[str] = []

        # first find the target pod
        if target_pod_name is not None:
            for pod in current_pods:
                if pod.name == target_pod_name:
                    candidate_pods.append(pod)
                    _candidate_names.append(pod.name)

        for pod in current_pods:
            if len(candidate_pods) == scale_down_count:
                return candidate_pods

            if pod.name in _candidate_names:
                continue
            if not pod.annotation_is_null(ErsiliaAnnotations.REQUEST_ID.value):
                continue
            # TODO: also check time within 60s
            if not pod.state.state_times["running"] is None:
                continue

            candidate_pods.append(pod)
            _candidate_names.append(pod.name)

        return candidate_pods

    def _delete_pod(self, pod_name: str, model_id: str = None) -> bool:
        try:
            deleted_pod = self._api_core.delete_namespaced_pod(
                pod_name, self._namespace
            )

            if deleted_pod is None:
                raise Exception("Failed to delete pod")

            k8s_pod = K8sPod.from_k8s(deleted_pod)

            ModelInstanceLogController.instance().log_instance(
                log_event=ModelInstanceLogEvent.INSTANCE_TERMINATED, k8s_pod=k8s_pod
            )

            return True
        except:
            ContextLogger.warn(
                self._logger_key,
                "Failed to delete instance [%s]%s, error = [%s]"
                % (
                    pod_name,
                    "" if model_id is None else " for model [%s]" % model_id,
                    repr(exc_info()),
                ),
            )
            traceback.print_exc(file=stdout)

            return False

    def _scale_down_pods(
        self,
        model_id: str,
        current_pods: List[K8sPod],
        new_replicas: int,
        target_pod_name: str = None,  # used to scale down specific pod
    ) -> bool:
        _lock_acquired = False

        try:
            if not self._acquire_lock(model_id):
                ContextLogger.error(
                    self._logger_key,
                    "Failed to acquire lock on model = [%s], error = [%s]"
                    % (model_id, repr(exc_info())),
                )
                return False

            _lock_acquired = True

            scale_down_candidates = self._get_scale_down_candidate_pods(
                current_pods, len(current_pods) - new_replicas, target_pod_name
            )

            for pod in scale_down_candidates:
                self._delete_pod(pod.name, model_id)

            # NOTE: this is "assumed", but we should probably compare NEW instance count vs expected instances
            return True
        finally:
            if _lock_acquired:
                self._release_lock(model_id)

    # def _scale_up_pods(
    #     self, model_id: str, current_replicas: int, new_replicas: int
    # ) -> bool:
    #     _lock_acquired = False

    #     try:
    #         if not self._acquire_lock(model_id):
    #             ContextLogger.error(
    #                 self._logger_key,
    #                 "Failed to acquire lock on model = [%s], error = [%s]"
    #                 % (model_id, repr(exc_info())),
    #             )
    #             return False

    #         _lock_acquired = True

    #         _current_replicas = len(self.load_model_pods(model_id))

    #         while _current_replicas < new_replicas:
    #             # TODO: add size_megabytes: int, disable_memory_limit: bool,
    #             self.create_model_pod(model_id)

    #             _current_replicas = len(self.load_model_pods(model_id))

    #         return True
    #     finally:
    #         if _lock_acquired:
    #             self._release_lock(model_id)

    def deploy_new_pod(
        self,
        model_id: str,
        size_megabytes: int,
        disable_memory_limit: bool,
        annotations: Dict[str, str] = None,
        model_template_version: str = "0.0.0",
    ) -> Union[None, K8sPod]:
        _lock_acquired = False

        try:
            if not self._acquire_lock(model_id):
                ContextLogger.error(
                    self._logger_key,
                    "Failed to acquire lock on model = [%s], error = [%s]"
                    % (model_id, repr(exc_info())),
                )
                return False

            _lock_acquired = True

            return self.create_model_pod(
                model_id,
                size_megabytes,
                disable_memory_limit,
                annotations=annotations,
                model_template_version=model_template_version,
            )
        finally:
            if _lock_acquired:
                self._release_lock(model_id)

    def delete_pod(
        self,
        model_id: str,
        annotations_filter: Dict[str, str] = None,
        target_pod_name: str = None,
    ) -> bool:
        if target_pod_name is not None:
            return self._delete_pod(target_pod_name, model_id)

        if annotations_filter is None or len(annotations_filter) == 0:
            ContextLogger.warn(
                self._logger_key,
                "Failed to delete_pod, missing 'target_pod_name' or 'annotations_filter' argument",
            )
            return False

        current_pods: List[K8sPod] = self.load_model_pods(model_id)
        target_pod_name: str = None

        for pod in current_pods:
            for key, value in annotations_filter.items():
                if not pod.annotation_equals(key, value):
                    continue

            target_pod_name = pod.name

        if target_pod_name is None:
            return True  # could not find pod, so we assume it's already scaled down

        return self._delete_pod(target_pod_name, model_id)

    def scale_pods(
        self,
        model_id: str,
        new_replicas: int,
        target_pod_name: str = None,  # used to scale down specific pod
    ) -> bool:
        _current_pods: List[K8sPod] = self.load_model_pods(model_id)

        if len(_current_pods) < new_replicas:
            return False
            # TODO: need to update this method to allow "generic" scaling without model, or ignore it
            # return self._scale_up_pods(model_id, len(_current_pods), new_replicas)
        elif len(_current_pods) > new_replicas:
            return self._scale_down_pods(
                model_id, _current_pods, new_replicas, target_pod_name
            )
        else:
            ContextLogger.debug(
                self._logger_key,
                "Pods already scaled to expected replicas [%d] for [%s]"
                % (new_replicas, model_id),
            )
            return True

    # we use subprocess.run to set up a local port
    # the k8s sdk uses python sockets, which is more complicated to manage within this app
    def portforward(
        self,
        model_id: str,
        request_id: str,
        port: int,
        pod_name: str = None,
        target_port: int = 80,
    ) -> Popen:
        _pod_name = pod_name

        if pod_name is None:
            pod = self.get_pod_by_request(model_id, request_id)

            if pod is None:
                ContextLogger.warn(
                    self._logger_key,
                    "Failed to portforward for model_id [%s], request_id [%s] - no pod found"
                    % (model_id, request_id),
                )
                return False

            _pod_name = pod.name

        try:
            process = Popen(
                [
                    "kubectl",
                    "port-forward",
                    f"pod/{_pod_name}",
                    "-n",
                    self._namespace,
                    f"{port}:{target_port}",
                ]
            )

            if process.returncode is not None and process.returncode != 0:
                ContextLogger.error(
                    self._logger_key,
                    "Failed to open Process for kubectl port-forward, pod-name = [%s], returncode = [%d]"
                    % (_pod_name, process.returncode),
                )

                try:
                    process.kill()
                except:
                    # ignore this
                    pass

                return None

            return process
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to set up portforward for port [%d], error = [%s]"
                % (port, repr(exc_info())),
            )
            traceback.print_exc(file=stdout)

            return None

    def list_nodes(self) -> List[K8sNode]:
        try:
            nodes: V1NodeList = self._api_core.list_node()

            return list(map(K8sNode.from_k8s, nodes))
        except:
            ContextLogger.error(
                self._logger_key, f"Failed to list nodes, error = [{repr(exc_info())}]"
            )
            traceback.print_exc(file=stdout)

            return []

    def scrape_node_metrics(self, node_name: str) -> List[str]:
        try:
            metrics = self._api_core.connect_get_node_proxy_with_path(
                name=node_name,
                path="metrics/resource",
            )

            if metrics is None or len(metrics) == 0:
                return []

            return metrics.split("\n")
        except:
            ContextLogger.warn(
                self._logger_key,
                f"Failed to scrape metrics for node [{node_name}], error = [{repr(exc_info())}]",
            )

            return []

    def _load_model_podtemplates(self) -> List[K8sPodTemplate]:
        pod_templates: List[K8sPodTemplate] = []
        continue_token: str = None
        label_selector = K8sController.MODELTEMPLATE_LABEL_SELECTOR

        while True:
            ContextLogger.trace(
                self._logger_key,
                "namespace=[%s], label_selector=[%s], continue_token=[%s]"
                % (self._namespace, label_selector, continue_token),
            )
            pod_templates_list: V1PodTemplateList = (
                self._api_core.list_namespaced_pod_template(
                    self._namespace,
                    label_selector=label_selector,
                    _continue=continue_token,
                )
            )
            for template in pod_templates_list.items:
                pod_templates.append(K8sPodTemplate.from_k8s(template))

            if pod_templates_list.metadata._continue is None:
                break

            continue_token = pod_templates_list.metadata._continue

        return pod_templates

    def _update_templates_cache(self):
        ContextLogger.debug(self._logger_key, "Updating templates cache")

        templates = self._load_model_podtemplates()
        new_cache = ThreadSafeCache()

        for template in templates:
            template_key = "%s_%s" % (
                template.get_label(ErsiliaLabels.K8S_COMPONENT.value),
                template.get_label(ErsiliaLabels.MODEL_TEMPLATE_VERSION.value),
            )

            new_cache[template_key] = template

        self._template_cache = new_cache

        ContextLogger.info(self._logger_key, "Templates cache updated")

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        while True:
            try:
                self._update_templates_cache()
            except:
                error_str = "Failed to update k8s caches, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

            if self._wait_or_kill(K8sController.UPDATE_WAIT_TIME):
                break

        ContextLogger.info(self._logger_key, "Controller stopped")
