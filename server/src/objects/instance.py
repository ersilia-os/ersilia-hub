from pydantic import BaseModel
from objects.k8s import K8sPod
from objects.k8s_model import K8sPodModel
from objects.metrics import (
    InstanceMetrics,
    InstanceMetricsModel,
)
from objects.instance_recommendations import (
    ModelInstanceResourceProfile,
    ModelInstanceResourceProfileModel,
)


class ModelInstance:

    k8s_pod: K8sPod
    metrics: InstanceMetrics | None
    cpu_resource_profile: ModelInstanceResourceProfile
    memory_resource_profile: ModelInstanceResourceProfile

    def __init__(
        self,
        k8s_pod: K8sPod,
        metrics: InstanceMetrics | None,
    ):
        self.k8s_pod = k8s_pod
        self.metrics = metrics
        self.cpu_resource_profile = ModelInstanceResourceProfile(
            (
                0.0
                if metrics is None or metrics.cpu_running_averages is None
                else metrics.cpu_running_averages.min
            ),
            (
                0.0
                if metrics is None or metrics.cpu_running_averages is None
                else metrics.cpu_running_averages.max
            ),
            (
                0.0
                if k8s_pod.resources is None or k8s_pod.resources.cpu_request is None
                else float(k8s_pod.resources.cpu_request)
            ),
            (
                0.0
                if k8s_pod.resources is None or k8s_pod.resources.cpu_limit is None
                else float(k8s_pod.resources.cpu_limit)
            ),
        )
        self.memory_resource_profile = ModelInstanceResourceProfile(
            (
                0.0
                if metrics is None or metrics.memory_running_averages is None
                else metrics.memory_running_averages.min
            ),
            (
                0.0
                if metrics is None or metrics.memory_running_averages is None
                else metrics.memory_running_averages.max
            ),
            (
                0.0
                if k8s_pod.resources is None or k8s_pod.resources.memory_request is None
                else float(k8s_pod.resources.memory_request)
            ),
            (
                0.0
                if k8s_pod.resources is None or k8s_pod.resources.memory_limit is None
                else float(k8s_pod.resources.memory_limit)
            ),
        )


class ModelInstanceModel(BaseModel):

    k8s_pod: K8sPodModel
    metrics: InstanceMetricsModel | None
    cpu_resource_profile: ModelInstanceResourceProfileModel
    memory_resource_profile: ModelInstanceResourceProfileModel

    @staticmethod
    def from_object(obj: ModelInstance) -> "ModelInstanceModel":
        return ModelInstanceModel(
            k8s_pod=K8sPodModel.from_object(obj.k8s_pod),
            metrics=InstanceMetricsModel.from_object(obj.metrics),
            cpu_resource_profile=ModelInstanceResourceProfileModel.from_object(
                obj.cpu_resource_profile
            ),
            memory_resource_profile=ModelInstanceResourceProfileModel.from_object(
                obj.memory_resource_profile
            ),
        )


class InstancesLoadFilters(BaseModel):
    active: bool | None = True
    persisted: bool | None = False
    model_id: str | None = None
    instance_id: str | None = None
