from enum import Enum
from typing import Any, Dict, List, Union
from kubernetes.client import (
    V1Pod,
    V1PodCondition,
    V1ContainerStatus,
    V1PodStatus,
    V1PodTemplate,
    V1PodTemplateSpec,
    V1ObjectMeta,
    V1Affinity,
    V1NodeAffinity,
    V1Node,
    V1ResourceRequirements,
)
from python_framework.time import string_from_date

from objects.k8s_generator import (
    generate_labels,
    generate_image,
    generate_affinity,
    generate_tolerations,
    generate_memory_limit,
)
from copy import deepcopy


class ErsiliaLabels(Enum):

    MODEL_ID = "ersilia.modelid"
    MODEL_SIZE = "ersilia.modelsize"
    MODEL_TEMPLATE_VERSION = "ersilia.modeltemplate.version"
    K8S_COMPONENT = "app.kubernetes.io/component"


class ErsiliaAnnotations(Enum):

    REQUEST_ID = "ersilia.requestid"


class K8sPodContainerState:

    phase: str
    started: bool
    ready: bool
    restart_count: int
    state_times: Dict[str, str]
    last_state_times: Dict[str, str]

    def __init__(
        self,
        phase: str,
        started: bool,
        ready: bool,
        restart_count: int,
        state_times: Dict[str, str],
        last_state_times: Dict[str, str],
    ):
        self.phase = phase
        self.started = started
        self.ready = ready
        self.restart_count = restart_count
        self.state_times = state_times
        self.last_state_times = last_state_times

    @staticmethod
    def from_k8s_status(status: V1PodStatus) -> "K8sPodContainerState":
        state_times = {
            "running": None,
            "terminated": None,
            "waiting": None,
        }
        last_state_times = {
            "running": None,
            "terminated": None,
            "waiting": None,
        }

        if status.container_statuses is None or len(status.container_statuses) == 0:
            return K8sPodContainerState(
                status.phase,
                False,
                False,
                0,
                state_times,
                last_state_times,
            )

        container_status: V1ContainerStatus = status.container_statuses[0]
        container_state = (
            None if container_status.state is None else container_status.state.to_dict()
        )
        container_last_state = (
            None
            if container_status.last_state is None
            else container_status.last_state.to_dict()
        )

        if container_state is not None:
            for state_key in state_times.keys():
                if (
                    state_key in container_state
                    and container_state[state_key] is not None
                    and "started_at" in container_state[state_key]
                ):
                    state_times[state_key] = string_from_date(
                        container_state[state_key]["started_at"]
                    )

        if container_last_state is not None:
            for state_key in last_state_times.keys():
                if (
                    state_key in container_last_state
                    and container_last_state[state_key] is not None
                    and "started_at" in container_last_state[state_key]
                ):
                    last_state_times[state_key] = string_from_date(
                        container_last_state[state_key]["started_at"]
                    )

        return K8sPodContainerState(
            status.phase,
            container_status.started,
            container_status.ready,
            container_status.restart_count,
            state_times,
            last_state_times,
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "started": self.started,
            "ready": self.ready,
            "restartCount": self.restart_count,
            "stateTimes": self.state_times,
            "lastStateTimes": self.last_state_times,
        }


class K8sPodCondition:

    last_probe_time: str
    last_transition_time: str
    message: str
    reason: str
    status: str
    type: str

    def __init__(
        self,
        last_probe_time: str,
        last_transition_time: str,
        message: str,
        reason: str,
        status: str,
        type: str,
    ):
        self.last_probe_time = last_probe_time
        self.last_transition_time = last_transition_time
        self.message = message
        self.reason = reason
        self.status = status
        self.type = type

    @staticmethod
    def from_k8s_condition(k8s_condition: V1PodCondition) -> "K8sPodCondition":
        return K8sPodCondition(
            (
                None
                if k8s_condition.last_probe_time is None
                else string_from_date(k8s_condition.last_probe_time)
            ),
            (
                None
                if k8s_condition.last_transition_time is None
                else string_from_date(k8s_condition.last_transition_time)
            ),
            k8s_condition.message,
            k8s_condition.reason,
            k8s_condition.status,
            k8s_condition.type,
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "lastProbeTime": self.last_probe_time,
            "lastTransitionTime": self.last_transition_time,
            "message": self.message,
            "reason": self.reason,
            "status": self.status,
            "type": self.type,
        }


class K8sPodState:

    conditions: List[K8sPodCondition]
    message: str
    reason: str
    start_time: str

    def __init__(
        self,
        conditions: List[K8sPodCondition],
        message: str,
        reason: str,
        start_time: str,
    ):
        self.conditions = conditions
        self.message = message
        self.reason = reason
        self.start_time = start_time

    @staticmethod
    def from_k8s_status(status: V1PodStatus) -> "K8sPodState":
        return K8sPodState(
            (
                []
                if status.conditions is None
                else list(map(K8sPodCondition.from_k8s_condition, status.conditions))
            ),
            status.message,
            status.reason,
            None if status.start_time is None else string_from_date(status.start_time),
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "conditions": list(map(lambda x: x.to_object(), self.conditions)),
            "message": self.message,
            "reason": self.reason,
            "startTime": self.start_time,
        }


def parse_k8s_cpu_value(k8s_value: str) -> Union[int, None]:
    if k8s_value is None or len(k8s_value) == 0:
        return None

    _k8s_value = k8s_value.strip()

    if _k8s_value.endswith("m"):
        return int(_k8s_value[:-1])
    else:
        # assume integer value for full cores
        return int(_k8s_value) * 1000


def parse_k8s_memory_value(k8s_value: str) -> Union[int, None]:
    if k8s_value is None or len(k8s_value) == 0:
        return None

    _k8s_value = k8s_value.strip()

    if _k8s_value.endswith("Mi"):
        return int(_k8s_value[:-2])
    elif _k8s_value.endswith("Gi"):
        return int(_k8s_value[:-2]) * 1024

    return 0


class K8sPodResources:
    cpu_request: int  # in millicores
    cpu_limit: Union[int, None]  # in millicores
    memory_request: int  # in megabytes
    memory_limit: Union[int, None]  # in megabytes

    def __init__(
        self,
        cpu_request: int,
        cpu_limit: Union[int, None],
        memory_request: int,
        memory_limit: Union[int, None],
    ):
        self.cpu_request = cpu_request
        self.cpu_limit = cpu_limit
        self.memory_request = memory_request
        self.memory_limit = memory_limit

    @staticmethod
    def from_k8s(k8s_resources: V1ResourceRequirements) -> "K8sPodResources":
        return K8sPodResources(
            (
                None
                if k8s_resources.requests is None or "cpu" not in k8s_resources.requests
                else parse_k8s_cpu_value(k8s_resources.requests["cpu"])
            ),
            (
                None
                if k8s_resources.limits is None or "cpu" not in k8s_resources.limits
                else parse_k8s_cpu_value(k8s_resources.limits["cpu"])
            ),
            (
                None
                if k8s_resources.requests is None
                or "memory" not in k8s_resources.requests
                else parse_k8s_memory_value(k8s_resources.requests["memory"])
            ),
            (
                None
                if k8s_resources.limits is None or "memory" not in k8s_resources.limits
                else parse_k8s_memory_value(k8s_resources.limits["memory"])
            ),
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "cpuRequest": self.cpu_request,
            "cpuLimit": self.cpu_limit,
            "memoryRequest": self.memory_request,
            "memoryLimit": self.memory_limit,
        }


class K8sPod:

    name: str
    state: K8sPodContainerState
    ip: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    pod_state: K8sPodState
    node_name: str | None
    resources: K8sPodResources

    def __init__(
        self,
        name: str,
        state: K8sPodContainerState,
        ip: str,
        labels: Dict[str, str],
        annotations: Dict[str, str],
        pod_state: K8sPodState,
        node_name: str | None,
        resources: K8sPodResources | None,
    ):
        self.name = name
        self.state = state
        self.ip = ip
        self.labels = labels
        self.annotations = annotations
        self.pod_state = pod_state
        self.node_name = node_name
        self.resources = resources

    @staticmethod
    def from_k8s(k8s_pod: V1Pod) -> "K8sPod":
        annotations = (
            dict(k8s_pod.metadata.annotations)
            if k8s_pod.metadata.annotations is not None
            else {}
        )

        return K8sPod(
            k8s_pod.metadata.name,
            K8sPodContainerState.from_k8s_status(k8s_pod.status),
            k8s_pod.status.pod_ip,
            dict(k8s_pod.metadata.labels),
            annotations,
            K8sPodState.from_k8s_status(k8s_pod.status),
            k8s_pod.spec.node_name,
            K8sPodResources.from_k8s(k8s_pod.spec.containers[0].resources),
        )

    def get_annotation(self, annotation: str) -> Union[str, None]:
        if annotation in self.annotations:
            return self.annotations[annotation]
        else:
            return None

    def annotation_equals(self, annotation: str, value: str) -> bool:
        annotation_value = self.get_annotation(annotation)

        if annotation_value is None:
            return False

        return annotation_value == str(value)

    def annotation_is_null(self, annotation: str) -> bool:
        return (
            annotation not in self.annotations
            or self.annotations[annotation] is None
            or len(self.annotations[annotation]) == 0
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.to_object(),
            "ip": self.ip,
            "labels": self.labels,
            "annotations": self.annotations,
            "podState": self.pod_state.to_object(),
            "nodeName": self.node_name,
            "resources": None if self.resources is None else self.resources.to_object(),
        }


class K8sPodTemplate:

    name: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    template: V1PodTemplateSpec

    def __init__(
        self,
        name: str,
        labels: Dict[str, str],
        annotations: Dict[str, str],
        template: V1PodTemplateSpec,
    ):
        self.name = name
        self.labels = labels
        self.annotations = annotations
        self.template = template

    def copy(self) -> "K8sPodTemplate":
        return K8sPodTemplate(
            self.name,
            dict(self.labels),
            dict(self.annotations),
            deepcopy(self.template),
        )

    @staticmethod
    def from_k8s(k8s_pod_template: V1PodTemplate) -> "K8sPodTemplate":
        annotations = (
            dict(k8s_pod_template.metadata.annotations)
            if k8s_pod_template.metadata.annotations is not None
            else {}
        )
        # strip unnecessary large object
        del annotations["kubectl.kubernetes.io/last-applied-configuration"]

        return K8sPodTemplate(
            k8s_pod_template.metadata.name,
            dict(k8s_pod_template.metadata.labels),
            annotations,
            k8s_pod_template.template,
        )

    def get_annotation(self, annotation: str) -> Union[str, None]:
        if annotation in self.annotations:
            return self.annotations[annotation]
        else:
            return None

    def annotation_equals(self, annotation: str, value: str) -> bool:
        annotation_value = self.get_annotation(annotation)

        return annotation_value is not None and annotation_value == str(value)

    def get_label(self, label: str) -> Union[str, None]:
        if label in self.labels:
            return self.labels[label]
        else:
            return None

    def label_equals(self, label: str, value: str) -> bool:
        label_value = self.get_label(label)

        return label_value is not None and label_value == value

    def get_model_size_megabytes(self) -> int:
        if ErsiliaLabels.MODEL_SIZE.value not in self.labels:
            return -1

        _size_str = self.labels[ErsiliaLabels.MODEL_SIZE.value]

        if _size_str.endswith("Mi"):
            return int(_size_str.strip("Mi"))
        elif _size_str.endswith("Gi"):
            return int(_size_str.strip("Gi")) * 1024

    def to_object(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "labels": self.labels,
            "annotations": self.annotations,
            "template": self.template.to_dict(),
        }

    def to_pod(self) -> V1Pod:
        metadata = V1ObjectMeta(
            generate_name=self.template.metadata.generate_name,
            labels=(
                {}
                if self.template.metadata.labels is None
                else self.template.metadata.labels
            ),
            annotations=(
                {}
                if self.template.metadata.annotations is None
                else self.template.metadata.annotations
            ),
        )
        pod = V1Pod(
            api_version="v1", kind="Pod", metadata=metadata, spec=self.template.spec
        )

        return pod

    def transform_for_model(
        self, model_id: str, size_megabytes: int, disable_memory_limit: bool
    ) -> "K8sPodTemplate":
        model_template = self.copy()

        model_template.template.metadata.generate_name = f"{model_id}-"
        model_template.template.spec.containers[0].image = generate_image(model_id)

        if model_template.template.spec.containers[0].resources is not None:
            if disable_memory_limit:
                if (
                    "memory"
                    in model_template.template.spec.containers[0].resources.limits
                ):
                    del model_template.template.spec.containers[0].resources.limits[
                        "memory"
                    ]
            else:
                model_template.template.spec.containers[0].resources.limits[
                    "memory"
                ] = generate_memory_limit(size_megabytes, disable_memory_limit)

        additional_labels = generate_labels(model_id, size_megabytes)
        tolerations = generate_tolerations(size_megabytes)
        affinity = generate_affinity(size_megabytes)

        if model_template.template.metadata.labels is None:
            model_template.template.metadata.labels = {}

        for key, value in additional_labels.items():
            model_template.template.metadata.labels[key] = value

        if self.template.spec.tolerations is None:
            model_template.template.spec.tolerations = []

        model_template.template.spec.tolerations += tolerations

        if model_template.template.spec.affinity is None:
            model_template.template.spec.affinity = V1Affinity()

        print(
            "current affinity = ", model_template.template.spec.affinity.node_affinity
        )

        if model_template.template.spec.affinity.node_affinity is None:
            model_template.template.spec.affinity.node_affinity = V1NodeAffinity(
                preferred_during_scheduling_ignored_during_execution=affinity
            )
        elif (
            model_template.template.spec.affinity.node_affinity.preferred_during_scheduling_ignored_during_execution
            is None
        ):
            model_template.template.spec.affinity.node_affinity.preferred_during_scheduling_ignored_during_execution = (
                affinity
            )
        else:
            model_template.template.spec.affinity.node_affinity.preferred_during_scheduling_ignored_during_execution += (
                affinity
            )

        return model_template


class K8sNode:

    name: str
    labels: Dict[str, str]
    # TODO: add status

    def __init__(self, name: str, labels: Dict[str, str]):
        self.name = name
        self.labels = labels

    @staticmethod
    def from_k8s(k8s_node: V1Node) -> "K8sNode":
        return K8sNode(
            k8s_node.metadata.name,
            dict(k8s_node.metadata.labels),
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "labels": self.labels,
        }
