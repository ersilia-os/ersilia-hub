from enum import Enum
from json import dumps, loads
from typing import Any, Dict, Union

from db.daos.model import ModelRecord
from objects.k8s import K8sPodResources
from objects.k8s_model import K8sPodResourcesModel
from pydantic import BaseModel


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


class ModelIdentificationDetails:
    description: str | None
    title: str | None
    interpretation: str | None
    slug: str | None
    source_code: str | None
    publication: str | None
    target_organisms: list[str] | None
    biomedical_areas: list[str] | None

    def __init__(
        self,
        description: str | None = None,
        title: str | None = None,
        interpretation: str | None = None,
        slug: str | None = None,
        source_code: str | None = None,
        publication: str | None = None,
        target_organisms: list[str] | None = None,
        biomedical_areas: list[str] | None = None,
    ) -> None:
        self.description = description
        self.title = title
        self.interpretation = interpretation
        self.slug = slug
        self.source_code = source_code
        self.publication = publication
        self.target_organisms = target_organisms
        self.biomedical_areas = biomedical_areas

    def copy(self) -> "ModelIdentificationDetails":
        return ModelIdentificationDetails(
            self.description,
            self.title,
            self.interpretation,
            self.slug,
            self.source_code,
            self.publication,
            self.target_organisms,
            self.biomedical_areas,
        )

    @staticmethod
    def from_object(obj: dict[str, Any]) -> "ModelIdentificationDetails":
        return ModelIdentificationDetails(
            None if "description" not in obj else obj["description"],
            None if "title" not in obj else obj["title"],
            None if "interpretation" not in obj else obj["interpretation"],
            None if "slug" not in obj else obj["slug"],
            None if "sourceCode" not in obj else obj["sourceCode"],
            None if "publication" not in obj else obj["publication"],
            None if "targetOrganisms" not in obj else obj["targetOrganisms"],
            None if "biomedicalAreas" not in obj else obj["biomedicalAreas"],
        )

    def to_object(self) -> dict[str, Any]:
        return {
            "description": self.description,
            "title": self.title,
            "interpretation": self.interpretation,
            "slug": self.slug,
            "sourceCode": self.source_code,
            "publication": self.publication,
            "targetOrganisms": self.target_organisms,
            "biomedicalAreas": self.biomedical_areas,
        }

    def __str__(self):
        return dumps(self.to_object())

    def __repr__(self):
        return self.__str__()


class ModelDetails:
    template_version: str
    description: str
    size_megabytes: int
    disable_memory_limit: bool
    max_instances: int
    execution_mode: ModelExecutionMode
    k8s_resources: K8sPodResources
    image_tag: str
    cache_enabled: bool
    identification_details: ModelIdentificationDetails | None

    def __init__(
        self,
        template_version: str,
        description: str,
        size_megabytes: int,
        disable_memory_limit: bool,
        max_instances: int,
        execution_mode: ModelExecutionMode,
        k8s_resources: K8sPodResources | None = None,
        image_tag: str = "latest",
        cache_enabled: bool = False,
        identification_details: ModelIdentificationDetails | None = None,
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
        self.image_tag = image_tag
        self.cache_enabled = cache_enabled
        self.identification_details = identification_details

    def copy(self) -> "ModelDetails":
        return ModelDetails(
            self.template_version,
            self.description,
            self.size_megabytes,
            self.disable_memory_limit,
            self.max_instances,
            self.execution_mode,
            self.k8s_resources,
            self.image_tag,
            self.cache_enabled,
            None
            if self.identification_details is None
            else self.identification_details.copy(),
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
            (
                "latest"
                if "imageTag" not in obj or obj["imageTag"] is None
                else obj["imageTag"]
            ),
            (
                False
                if "cacheEnabled" not in obj or obj["cacheEnabled"] is None
                else obj["cacheEnabled"]
            ),
            (
                None
                if "identificationDetails" not in obj
                or obj["identificationDetails"] is None
                else ModelIdentificationDetails.from_object(
                    obj["identificationDetails"]
                )
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
            "imageTag": self.image_tag,
            "cacheEnabled": self.cache_enabled,
            "identificationDetails": (
                None
                if self.identification_details is None
                else self.identification_details.to_object()
            ),
        }

    def __str__(self):
        return dumps(self.to_object())

    def __repr__(self):
        return self.__str__()


class ModelIdentificationDetailsModel(BaseModel):
    description: str | None = None
    title: str | None = None
    interpretation: str | None = None
    slug: str | None = None
    source_code: str | None = None
    publication: str | None = None
    target_organisms: list[str] | None = None
    biomedical_areas: list[str] | None = None

    @staticmethod
    def from_object(
        model_details: ModelIdentificationDetails,
    ) -> "ModelIdentificationDetailsModel":
        return ModelIdentificationDetailsModel(
            description=model_details.description,
            title=model_details.title,
            interpretation=model_details.interpretation,
            slug=model_details.slug,
            source_code=model_details.source_code,
            publication=model_details.publication,
            target_organisms=model_details.target_organisms,
            biomedical_areas=model_details.biomedical_areas,
        )

    def to_object(self) -> ModelIdentificationDetails:
        return ModelIdentificationDetails(
            self.description,
            self.title,
            self.interpretation,
            self.slug,
            self.source_code,
            self.publication,
            self.target_organisms,
            self.biomedical_areas,
        )


class ModelDetailsApiModel(BaseModel):
    template_version: str
    description: str
    disable_memory_limit: bool
    max_instances: int
    execution_mode: str
    k8s_resources: K8sPodResourcesModel | None = None
    image_tag: str
    cache_enabled: bool
    identification_details: ModelIdentificationDetailsModel | None = None

    @staticmethod
    def from_object(model_details: ModelDetails) -> "ModelDetailsApiModel":
        return ModelDetailsApiModel(
            template_version=model_details.template_version,
            description=model_details.description,
            disable_memory_limit=model_details.disable_memory_limit,
            max_instances=model_details.max_instances,
            execution_mode=str(model_details.execution_mode),
            k8s_resources=K8sPodResourcesModel.from_object(model_details.k8s_resources),
            image_tag=model_details.image_tag,
            cache_enabled=model_details.cache_enabled,
            identification_details=(
                None
                if model_details.identification_details is None
                else ModelIdentificationDetailsModel.from_object(
                    model_details.identification_details
                )
            ),
        )

    def to_object(self) -> ModelDetails:
        return ModelDetails(
            self.template_version,
            self.description,
            self.k8s_resources.memory_limit,
            self.disable_memory_limit,
            self.max_instances,
            self.execution_mode,
            None if self.k8s_resources is None else self.k8s_resources.to_object(),
            self.image_tag,
            self.cache_enabled,
            (
                None
                if self.identification_details is None
                else self.identification_details.to_object()
            ),
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

    @staticmethod
    def copy_model(model: Model) -> "ModelUpdate":
        return ModelUpdate(model.id, model.details.copy(), model.enabled)


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
