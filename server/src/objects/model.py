from enum import Enum
from json import dumps, loads
from typing import Any, Dict, Union
from db.daos.model import ModelRecord
from pydantic import BaseModel

from objects.k8s import K8sPodResources
from objects.k8s_model import K8sPodResourcesModel


class ModelExecutionMode(Enum):

    SYNC = "SYNC"
    ASYNC = "ASYNC"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif self.__class__ is other.__class__:
            return self.value == other.value

        return self.value == other

    def __str__(self):
        return self.name

    def __hash__(self):
        return str(self.name).__hash__()


class ModelDetails:

    template_version: str
    description: str
    size_megabytes: int
    disable_memory_limit: bool
    max_instances: int
    execution_mode: ModelExecutionMode
    k8s_resources: K8sPodResources

    def __init__(
        self,
        template_version: str,
        description: str,
        size_megabytes: int,
        disable_memory_limit: bool,
        max_instances: int,
        execution_mode: ModelExecutionMode,
        k8s_resources: K8sPodResources | None = None,
    ):
        self.template_version = template_version
        self.description = description
        self.size_megabytes = size_megabytes
        self.disable_memory_limit = disable_memory_limit
        self.max_instances = max_instances
        self.execution_mode = execution_mode
        self.k8s_resources = (
            K8sPodResources(
                cpu_request=10,
                cpu_limit=500,
                memory_request=100,
                memory_limit=size_megabytes,
            )
            if k8s_resources is None
            else k8s_resources
        )

    def copy(self) -> "ModelDetails":
        return ModelDetails(
            self.template_version,
            self.description,
            self.size_megabytes,
            self.disable_memory_limit,
            self.max_instances,
            self.execution_mode,
            self.k8s_resources,
        )

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "ModelDetails":
        return ModelDetails(
            obj["templateVersion"],
            obj["description"],
            obj["sizeMegabytes"],
            obj["disableMemoryLimit"],
            obj["maxInstances"],
            (
                ModelExecutionMode.ASYNC
                if "executionMode" not in obj or obj["executionMode"] is None
                else obj["executionMode"]
            ),
            (
                None
                if "k8sResources" not in obj
                else K8sPodResources.from_object(obj["k8sResources"])
            ),
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "templateVersion": self.template_version,
            "description": self.description,
            "sizeMegabytes": self.size_megabytes,
            "disableMemoryLimit": self.disable_memory_limit,
            "maxInstances": self.max_instances,
            "executionMode": str(self.execution_mode),
            "k8sResources": self.k8s_resources.to_object(),
        }

    def __str__(self):
        return dumps(self.to_object())

    def __repr__(self):
        return self.__str__()


class ModelDetailsApiModel(BaseModel):

    template_version: str
    description: str
    size_megabytes: int
    disable_memory_limit: bool
    max_instances: int
    execution_mode: str
    k8s_resources: K8sPodResourcesModel | None = None

    @staticmethod
    def from_object(model_details: ModelDetails) -> "ModelDetailsApiModel":
        return ModelDetailsApiModel(
            template_version=model_details.template_version,
            description=model_details.description,
            size_megabytes=model_details.size_megabytes,
            disable_memory_limit=model_details.disable_memory_limit,
            max_instances=model_details.max_instances,
            execution_mode=str(model_details.execution_mode),
            k8s_resources=K8sPodResourcesModel.from_object(model_details.k8s_resources),
        )

    def to_object(self) -> ModelDetails:
        return ModelDetails(
            self.template_version,
            self.description,
            self.size_megabytes,
            self.disable_memory_limit,
            self.max_instances,
            self.execution_mode,
            None if self.k8s_resources is None else self.k8s_resources.to_object(),
        )


class Model:

    id: str
    enabled: bool
    details: ModelDetails
    last_updated: Union[str, None]

    def __init__(
        self,
        id: str,
        enabled: bool,
        details: ModelDetails,
        last_updated: Union[str, None] = None,
    ):
        self.id = id
        self.enabled = enabled
        self.details = details
        self.last_updated = last_updated

    def copy(self) -> "Model":
        return Model(
            self.id,
            self.enabled,
            self.details.copy(),
            self.last_updated,
        )

    @staticmethod
    def init_from_record(record: ModelRecord) -> "Model":
        return Model(
            record.id,
            record.enabled,
            ModelDetails.from_object(loads(record.details)),
            record.last_updated,
        )

    def to_record(self) -> ModelRecord:
        return ModelRecord.init(
            id=self.id,
            enabled=self.enabled,
            details=dumps(self.details.to_object()),
            lastupdated=self.last_updated,
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "details": self.details.to_object(),
            "lastUpdated": self.last_updated,
        }

    def apply_update(self, model_update: "ModelUpdate"):
        self.details = model_update.details
        self.enabled = model_update.enabled

    def __str__(self):
        return dumps(self.to_object())

    def __repr__(self):
        return self.__str__()


class ModelApiModel(BaseModel):

    id: str
    enabled: bool
    details: ModelDetailsApiModel
    last_updated: str | None = None

    @staticmethod
    def from_object(model: Model) -> "ModelApiModel":
        return ModelApiModel(
            id=model.id,
            enabled=model.enabled,
            details=ModelDetailsApiModel.from_object(model.details),
            last_updated=model.last_updated,
        )

    def to_object(self) -> Model:
        return Model(
            self.id,
            self.enabled,
            self.details.to_object(),
            self.last_updated,
        )


class ModelScalingInfo:

    enabled: bool
    current_instances: int
    max_instances: int

    def __init__(
        self,
        enabled: bool,
        current_instances: int,
        max_instances: int,
    ):
        self.enabled = enabled
        self.current_instances = current_instances
        self.max_instances = max_instances

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "ModelDetails":
        return ModelDetails(
            obj["enabled"],
            obj["currentInstances"],
            obj["maxInstances"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "currentInstances": self.current_instances,
            "maxInstances": self.max_instances,
        }

    def __str__(self):
        return dumps(self.to_object())

    def __repr__(self):
        return self.__str__()


class ModelScalingInfoModel(BaseModel):

    enabled: bool
    current_instances: int
    max_instances: int

    @staticmethod
    def from_object(object: ModelScalingInfo) -> "ModelScalingInfoModel":
        return ModelScalingInfoModel(
            enabled=object.enabled,
            current_instances=object.current_instances,
            max_instances=object.max_instances,
        )


class ModelUpdate:

    id: str
    details: ModelDetails
    enabled: bool

    def __init__(
        self,
        id: str,
        details: ModelDetails,
        enabled: bool,
    ):
        self.id = id
        self.details = details
        self.enabled = enabled


class ModelUpdateApiModel(BaseModel):

    id: str
    details: ModelDetailsApiModel
    enabled: bool

    def to_object(self) -> ModelUpdate:
        return ModelUpdate(self.id, self.details.to_object(), self.enabled)


class ModelInstance(BaseModel):

    model_id: str
    request_id: str

    def to_object(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "request_id": self.request_id,
        }
