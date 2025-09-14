from enum import Enum
from pydantic import BaseModel
from objects.k8s import K8sPod
from objects.k8s_model import K8sPodModel
from objects.metrics import (
    InstanceMetrics,
    InstanceMetricsModel,
)
from objects.instance_recommendations import (
    ModelInstanceRecommendations,
    ModelInstanceRecommendationsModel,
    ModelInstanceResourceProfile,
    ModelInstanceResourceProfileModel,
)


class ModelInstance:

    k8s_pod: K8sPod
    metrics: InstanceMetrics | None
    resource_profile: ModelInstanceResourceProfile | None
    resource_recommendations: ModelInstanceRecommendations | None

    def __init__(
        self,
        k8s_pod: K8sPod,
        metrics: InstanceMetrics | None = None,
        resource_profile: ModelInstanceResourceProfile | None = None,
        resource_recommendations: ModelInstanceRecommendations | None = None,
    ):
        self.k8s_pod = k8s_pod
        self.metrics = metrics
        self.resource_profile = resource_profile
        self.resource_recommendations = resource_recommendations


class ModelInstanceModel(BaseModel):

    k8s_pod: K8sPodModel
    metrics: InstanceMetricsModel | None
    resource_profile: ModelInstanceResourceProfileModel | None
    resource_recommendations: ModelInstanceRecommendationsModel | None

    @staticmethod
    def from_object(obj: ModelInstance) -> "ModelInstanceModel":
        return ModelInstanceModel(
            k8s_pod=K8sPodModel.from_object(obj.k8s_pod),
            metrics=InstanceMetricsModel.from_object(obj.metrics),
            resource_profile=ModelInstanceResourceProfileModel.from_object(
                obj.resource_profile
            ),
            resource_recommendations=ModelInstanceRecommendationsModel.from_object(
                obj.resource_recommendations
            ),
        )


class InstancesLoadFilters(BaseModel):
    active: bool | None = True
    persisted: bool | None = False
    model_id: str | None = None
    instance_id: str | None = None
    load_resource_profiles: bool | None = False
    load_recommendations: bool | None = False

class InstanceAction(Enum):

    STOP_INSTANCE = "STOP_INSTANCE"

class InstanceActionModel(BaseModel):
    model_id: str | None = None
    instance_id: str | None = None
    action: str

