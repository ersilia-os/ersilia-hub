from enum import Enum
from math import ceil, floor
from typing import Any, Dict

from pydantic import BaseModel
from python_framework.time import utc_now


class ResourceProfile:

    min_usage: float
    min_allocatable: float
    min_usage_percentage: int

    max_usage: float
    max_allocatable: float
    max_usage_percentage: int

    def __init__(
        self,
        min_usage: float,
        min_allocatable: float,
        max_usage: float,
        max_allocatable: float,
    ):
        self.min_usage = 0.0 if min_usage is None else min_usage
        self.min_allocatable = 0.0 if min_allocatable is None else min_allocatable
        self.max_usage = 0.0 if max_usage is None else max_usage
        self.max_allocatable = 0.0 if max_allocatable is None else max_allocatable

        self.min_usage_percentage = (
            0
            if self.min_allocatable <= 0.0
            else int(floor(self.min_usage / self.min_allocatable * 100))
        )

        self.max_usage_percentage = (
            0
            if self.max_allocatable <= 0.0
            else int(ceil(self.max_usage / self.max_allocatable * 100))
        )


class ResourceProfileModel(BaseModel):

    min_usage: float
    max_usage: float
    min_allocatable: float
    max_allocatable: float
    min_usage_percentage: int
    max_usage_percentage: int

    @staticmethod
    def from_object(
        obj: ResourceProfile,
    ) -> "ResourceProfileModel":
        return ResourceProfileModel(
            min_usage=obj.min_usage,
            max_usage=obj.max_usage,
            min_allocatable=obj.min_allocatable,
            max_allocatable=obj.max_allocatable,
            min_usage_percentage=obj.min_usage_percentage,
            max_usage_percentage=obj.max_usage_percentage,
        )


class ModelInstanceResourceProfile:

    cpu: ResourceProfile
    memory: ResourceProfile

    def __init__(
        self,
        cpu: ResourceProfile,
        memory: ResourceProfile,
    ):
        self.cpu = cpu
        self.memory = memory


class ModelInstanceResourceProfileModel(BaseModel):

    cpu: ResourceProfileModel
    memory: ResourceProfileModel

    @staticmethod
    def from_object(
        obj: ModelInstanceResourceProfile,
    ) -> "ModelInstanceResourceProfileModel":
        if obj is None:
            return None

        return ModelInstanceResourceProfileModel(
            cpu=ResourceProfileModel.from_object(obj.cpu),
            memory=ResourceProfileModel.from_object(obj.memory),
        )


class ResourceProfileId(Enum):

    CPU_MIN = "CPU_MIN"
    CPU_MAX = "CPU_MAX"
    MEMORY_MIN = "MEMORY_MIN"
    MEMORY_MAX = "MEMORY_MAX"

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


class ResourceProfileState(Enum):

    VERY_UNDER = "VERY_UNDER"
    UNDER = "UNDER"
    RECOMMENDED = "RECOMMENDED"
    OVER = "OVER"
    VERY_OVER = "VERY_OVER"

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


class ResourceProfileConfig:
    """
    Resource Profiling "bracket" for each resource type, e.g. CPU_MIN, RECOMMENDED or CPU_MAX, OVER, etc.
    """

    id: ResourceProfileId
    state: ResourceProfileState
    min: int
    max: int

    def __init__(
        self,
        id: ResourceProfileId,
        state: ResourceProfileState,
        min: int,
        max: int,
    ):
        self.id = id
        self.state = state
        self.min = min
        self.max = max

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "ResourceProfileConfig":
        return ResourceProfileConfig(
            obj["id"],
            obj["state"],
            obj["min"],
            obj["max"],
        )

    def __str__(self):
        return f"ResourceProfileConfig[id = {self.id}, state = {self.state}, min = {self.min}, max = {self.max}]"

    def __repr__(self):
        return str(self)


class ResourceProfileConfigModel(BaseModel):
    id: str
    state: str
    min: int
    max: int

    @staticmethod
    def from_object(obj: ResourceProfileConfig) -> "ResourceProfileConfigModel":
        if obj is None:
            return None

        return ResourceProfileConfigModel(
            id=str(obj.id),
            state=str(obj.state),
            min=obj.min,
            max=obj.max,
        )


class ResourceRecommendation:

    profile_id: ResourceProfileId
    current_usage_value: float
    current_allocation_value: int
    current_usage_percentage: int
    current_profile_state: ResourceProfileConfig
    recommended_profile: ResourceProfileConfig
    recommended_min_value: float
    recommended_max_value: float

    def __init__(
        self,
        profile_id: ResourceProfileId,
        current_usage_value: float,
        current_allocation_value: int,
        current_usage_percentage: int,
        current_profile_state: ResourceProfileConfig,
        recommended_profile: ResourceProfileConfig,
        recommended_min_value: float,
        recommended_max_value: float,
    ):
        self.profile_id = profile_id
        self.current_usage_value = current_usage_value
        self.current_allocation_value = current_allocation_value
        self.current_usage_percentage = current_usage_percentage
        self.current_profile_state = current_profile_state
        self.recommended_profile = recommended_profile
        self.recommended_min_value = recommended_min_value
        self.recommended_max_value = recommended_max_value


class ResourceRecommendationModel(BaseModel):

    profile_id: str
    current_usage_value: float
    current_allocation_value: int
    current_usage_percentage: int
    current_profile_state: ResourceProfileConfigModel | None
    recommended_profile: ResourceProfileConfigModel | None
    recommended_min_value: float
    recommended_max_value: float

    @staticmethod
    def from_object(obj: ResourceRecommendation) -> "ResourceRecommendationModel":
        return ResourceRecommendationModel(
            profile_id=str(obj.profile_id),
            current_usage_value=obj.current_usage_value,
            current_allocation_value=obj.current_allocation_value,
            current_usage_percentage=obj.current_usage_percentage,
            current_profile_state=ResourceProfileConfigModel.from_object(
                obj.current_profile_state
            ),
            recommended_profile=ResourceProfileConfigModel.from_object(
                obj.recommended_profile
            ),
            recommended_min_value=obj.recommended_min_value,
            recommended_max_value=obj.recommended_max_value,
        )


class ModelInstanceRecommendations:

    cpu_min: ResourceRecommendation
    cpu_max: ResourceRecommendation
    memory_min: ResourceRecommendation
    memory_max: ResourceRecommendation
    last_updated: str | None

    def __init__(
        self,
        cpu_min: ResourceRecommendation,
        cpu_max: ResourceRecommendation,
        memory_min: ResourceRecommendation,
        memory_max: ResourceRecommendation,
        last_updated: str | None = None,
    ):
        self.cpu_min = cpu_min
        self.cpu_max = cpu_max
        self.memory_min = memory_min
        self.memory_max = memory_max
        self.last_updated = last_updated if last_updated is not None else utc_now()


class ModelInstanceRecommendationsModel(BaseModel):

    cpu_min: ResourceRecommendationModel
    cpu_max: ResourceRecommendationModel
    memory_min: ResourceRecommendationModel
    memory_max: ResourceRecommendationModel
    last_updated: str | None

    @staticmethod
    def from_object(
        obj: ModelInstanceRecommendations,
    ) -> "ModelInstanceRecommendationsModel":
        if obj is None:
            return None

        return ModelInstanceRecommendationsModel(
            cpu_min=ResourceRecommendationModel.from_object(obj.cpu_min),
            cpu_max=ResourceRecommendationModel.from_object(obj.cpu_max),
            memory_min=ResourceRecommendationModel.from_object(obj.memory_min),
            memory_max=ResourceRecommendationModel.from_object(obj.memory_max),
            last_updated=obj.last_updated,
        )


class RecommendationEngineState:

    last_updated: str
    model_recommendations: Dict[str, ModelInstanceRecommendations]
