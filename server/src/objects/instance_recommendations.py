from math import ceil, floor

from pydantic import BaseModel


class ModelInstanceResourceProfile:

    min_usage: float
    max_usage: float
    min_allocatable: float
    max_allocatable: float

    min_usage_percentage: int
    max_usage_percentage: int

    def __init__(
        self,
        min_usage: float,
        max_usage: float,
        min_allocatable: float,
        max_allocatable: float,
    ):
        self.min_usage = 0.0 if min_usage is None else min_usage
        self.max_usage = 0.0 if max_usage is None else max_usage
        self.min_allocatable = 0.0 if min_allocatable is None else min_allocatable
        self.max_allocatable = 0.0 if max_allocatable is None else max_allocatable

        self.min_usage_percentage = (
            0
            if self.min_allocatable <= 0.0
            else floor(self.min_usage / self.min_allocatable)
        )

        self.max_usage_percentage = (
            0
            if self.max_allocatable <= 0.0
            else ceil(self.max_usage / self.max_allocatable)
        )


class ModelInstanceResourceProfileModel(BaseModel):

    min_usage: float
    max_usage: float
    min_allocatable: float
    max_allocatable: float
    min_usage_percentage: int
    max_usage_percentage: int

    @staticmethod
    def from_object(
        obj: ModelInstanceResourceProfile,
    ) -> "ModelInstanceResourceProfileModel":
        return ModelInstanceResourceProfileModel(
            min_usage=obj.min_usage,
            max_usage=obj.max_usage,
            min_allocatable=obj.min_allocatable,
            max_allocatable=obj.max_allocatable,
            min_usage_percentage=obj.min_usage_percentage,
            max_usage_percentage=obj.max_usage_percentage,
        )
