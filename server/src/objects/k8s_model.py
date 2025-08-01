from typing import Dict, List

from pydantic import BaseModel

from objects.k8s import (
    K8sPod,
    K8sPodCondition,
    K8sPodContainerState,
    K8sPodResources,
    K8sPodState,
)


class K8sPodContainerStateModel(BaseModel):

    phase: str
    started: bool
    ready: bool
    restart_count: int
    state_times: Dict[str, str | None]
    last_state_times: Dict[str, str | None]

    @staticmethod
    def from_object(obj: K8sPodContainerState) -> "K8sPodContainerStateModel":
        return K8sPodContainerStateModel(
            phase=obj.phase,
            started=obj.started,
            ready=obj.ready,
            restart_count=obj.restart_count,
            state_times=obj.state_times,
            last_state_times=obj.last_state_times,
        )


class K8sPodConditionModel(BaseModel):

    last_probe_time: str | None
    last_transition_time: str | None
    message: str | None
    reason: str | None
    status: str | None
    type: str | None

    @staticmethod
    def from_object(obj: K8sPodCondition) -> "K8sPodConditionModel":
        return K8sPodConditionModel(
            last_probe_time=obj.last_probe_time,
            last_transition_time=obj.last_transition_time,
            message=obj.message,
            reason=obj.reason,
            status=obj.status,
            type=obj.type,
        )


class K8sPodStateModel(BaseModel):

    conditions: List[K8sPodConditionModel]
    message: str | None
    reason: str | None
    start_time: str | None

    @staticmethod
    def from_object(obj: K8sPodState) -> "K8sPodStateModel":
        return K8sPodStateModel(
            conditions=(
                []
                if obj.conditions is None
                else list(map(K8sPodConditionModel.from_object, obj.conditions))
            ),
            message=obj.message,
            reason=obj.reason,
            start_time=obj.start_time,
        )


class K8sPodResourcesModel(BaseModel):
    cpu_request: int  # in millicores
    cpu_limit: int | None  # in millicores
    memory_request: int  # in megabytes
    memory_limit: int | None  # in megabytes

    @staticmethod
    def from_object(obj: K8sPodResources) -> "K8sPodResourcesModel":
        if obj is None:
            return obj

        return K8sPodResourcesModel(
            cpu_request=obj.cpu_request,
            cpu_limit=obj.cpu_limit,
            memory_request=obj.memory_request,
            memory_limit=obj.memory_limit,
        )

    def to_object(self) -> K8sPodResources:
        return K8sPodResources(
            cpu_request=self.cpu_request,
            cpu_limit=self.cpu_limit,
            memory_request=self.memory_request,
            memory_limit=self.memory_limit,
        )


class K8sPodModel(BaseModel):

    name: str
    namespace: str
    state: K8sPodContainerStateModel
    ip: str | None
    labels: Dict[str, str]
    annotations: Dict[str, str]
    pod_state: K8sPodStateModel
    node_name: str | None
    resources: K8sPodResourcesModel | None

    @staticmethod
    def from_object(k8s_pod: K8sPod) -> "K8sPodModel":
        return K8sPodModel(
            name=k8s_pod.name,
            namespace=k8s_pod.namespace,
            state=K8sPodContainerStateModel.from_object(k8s_pod.state),
            ip=k8s_pod.ip,
            labels=k8s_pod.labels,
            annotations=k8s_pod.annotations,
            pod_state=K8sPodStateModel.from_object(k8s_pod.pod_state),
            node_name=k8s_pod.node_name,
            resources=K8sPodResourcesModel.from_object(k8s_pod.resources),
        )
