from enum import Enum

from objects.instance_recommendations import (
    ModelInstanceRecommendations,
    ModelInstanceRecommendationsModel,
    ModelInstanceResourceProfile,
    ModelInstanceResourceProfileModel,
)
from objects.k8s import K8sPod
from objects.k8s_model import K8sPodModel
from objects.metrics import (
    InstanceMetrics,
    InstanceMetricsModel,
)
from pydantic import BaseModel

from src.db.daos.model_instance_log import ModelInstanceLogRecord


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


class InstanceLogEntry:
    model_id: str
    instance_id: str
    correlation_id: str
    instance_details: K8sPod | None
    log_event: str
    log_timestamp: str

    def __init__(
        self,
        model_id: str,
        instance_id: str,
        correlation_id: str,
        instance_details: K8sPod | None,
        log_event: str,
        log_timestamp: str,
    ) -> None:
        self.model_id = model_id
        self.instance_id = instance_id
        self.correlation_id = correlation_id
        self.instance_details = instance_details
        self.log_event = log_event
        self.log_timestamp = log_timestamp

    @staticmethod
    def from_record(record: ModelInstanceLogRecord) -> "InstanceLogEntry":
        return InstanceLogEntry(
            model_id=record.modelid,
            instance_id=record.instanceid,
            correlation_id=record.correlationid,
            instance_details=(
                None
                if record.instance_details is None or len(record.instance_details) <= 5
                else K8sPod.from_object(record.instance_details)
            ),
            log_event=record.log_event,
            log_timestamp=record.log_timestamp,
        )


class InstanceLogEntryModel(BaseModel):
    model_id: str
    instance_id: str
    correlation_id: str
    instance_details: K8sPodModel | None
    log_event: str
    log_timestamp: str

    @staticmethod
    def from_object(obj: InstanceLogEntry) -> "InstanceLogEntryModel":
        return InstanceLogEntryModel(
            model_id=obj.model_id,
            instance_id=obj.instance_id,
            correlation_id=obj.correlation_id,
            instance_details=None
            if obj.instance_details is None
            else K8sPodModel.from_object(obj.instance_details),
            log_event=obj.log_event,
            log_timestamp=obj.log_timestamp,
        )
