from enum import Enum
from json import loads
from typing import Any

from db.daos.model_instance import ModelInstanceExtendedRecord, ModelInstanceRecord
from db.daos.model_instance_log import ModelInstanceLogRecord
from db.daos.work_request import WorkRequestRecord
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

from src.objects.work_request import WorkRequest, WorkRequestModel


class ModelInstance:
    model_id: str
    work_request_id: int
    instance_id: str | None
    instance_details: K8sPod | None
    state: str
    termination_reason: str | None
    # NOTE: [cutting-corners] this should be made into a proper object
    job_submission_process: dict[str, Any] | None
    last_updated: str | None

    def __init__(
        self,
        model_id: str,
        work_request_id: int,
        instance_id: str | None,
        instance_details: K8sPod | None,
        state: str,
        termination_reason: str | None,
        # NOTE: [cutting-corners] this should be made into a proper object
        job_submission_process: dict[str, Any] | None,
        last_updated: str | None,
    ):
        self.model_id = model_id
        self.work_request_id = work_request_id
        self.instance_id = instance_id
        self.instance_details = instance_details
        self.state = state
        self.termination_reason = termination_reason
        self.job_submission_process = job_submission_process
        self.last_updated = last_updated

    @staticmethod
    def from_record(
        record: ModelInstanceRecord | ModelInstanceExtendedRecord,
    ) -> "ModelInstance":
        return ModelInstance(
            record.model_id,
            record.work_request_id,
            record.instance_id,
            (
                None
                if record.instance_details is None
                else K8sPod.from_object(loads(record.instance_details))
            ),
            record.state,
            record.termination_reason,
            (
                None
                if record.job_submission_process is None
                else loads(record.job_submission_process)
            ),
            record.last_updated,
        )

    # TODO: to_record, if needed


class ModelInstanceModel(BaseModel):
    model_id: str
    work_request_id: int
    instance_id: str | None
    instance_details: K8sPodModel | None
    state: str
    termination_reason: str | None
    # NOTE: [cutting-corners] this should be made into a proper object
    job_submission_process: dict[str, Any] | None
    last_updated: str | None

    @staticmethod
    def from_object(obj: ModelInstance) -> "ModelInstanceModel":
        return ModelInstanceModel(
            model_id=obj.model_id,
            work_request_id=obj.work_request_id,
            instance_id=obj.instance_id,
            instance_details=K8sPodModel.from_object(obj.instance_details),
            state=obj.state,
            termination_reason=obj.termination_reason,
            job_submission_process=obj.job_submission_process,
            last_updated=obj.last_updated,
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
                else K8sPod.from_object(loads(record.instance_details))
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


class ExtendedModelInstance:
    model_instance: ModelInstance
    last_event: InstanceLogEntry | None
    work_request: WorkRequest | None
    metrics: InstanceMetrics | None
    resource_profile: ModelInstanceResourceProfile | None
    resource_recommendations: ModelInstanceRecommendations | None

    def __init__(
        self,
        model_instance: ModelInstance,
        last_event: InstanceLogEntry | None,
        work_request: WorkRequest | None,
        metrics: InstanceMetrics | None = None,
        resource_profile: ModelInstanceResourceProfile | None = None,
        resource_recommendations: ModelInstanceRecommendations | None = None,
    ) -> None:
        self.model_instance = model_instance
        self.last_event = last_event
        self.work_request = work_request
        self.metrics = metrics
        self.resource_profile = resource_profile
        self.resource_recommendations = resource_recommendations

    @staticmethod
    def from_extended_record(
        record: ModelInstanceExtendedRecord,
    ) -> "ExtendedModelInstance":
        return ExtendedModelInstance(
            ModelInstance.from_record(record),
            (
                None
                if record.last_event is None
                else InstanceLogEntry.from_record(
                    ModelInstanceLogRecord(loads(record.last_event))
                )
            ),
            (
                None
                if record.work_request is None
                else WorkRequest.init_from_record(
                    WorkRequestRecord(loads(record.work_request))
                )
            ),
        )


class ExtendedModelInstanceModel(BaseModel):
    model_instance: ModelInstanceModel
    last_event: InstanceLogEntryModel | None
    work_request: WorkRequestModel | None
    metrics: InstanceMetricsModel | None
    resource_profile: ModelInstanceResourceProfileModel | None
    resource_recommendations: ModelInstanceRecommendationsModel | None

    @staticmethod
    def from_object(obj: ExtendedModelInstance) -> "ExtendedModelInstanceModel":
        return ExtendedModelInstanceModel(
            model_instance=ModelInstanceModel.from_object(obj.model_instance),
            last_event=(
                None
                if obj.last_event is None
                else InstanceLogEntryModel.from_object(obj.last_event)
            ),
            work_request=(
                None
                if obj.work_request is None
                else WorkRequestModel.from_workrequest(obj.work_request)
            ),
            metrics=(
                None
                if obj.metrics is None
                else InstanceMetricsModel.from_object(obj.metrics)
            ),
            resource_profile=(
                None
                if obj.resource_profile is None
                else ModelInstanceResourceProfileModel.from_object(obj.resource_profile)
            ),
            resource_recommendations=(
                None
                if obj.resource_recommendations is None
                else ModelInstanceRecommendationsModel.from_object(
                    obj.resource_recommendations
                )
            ),
        )
