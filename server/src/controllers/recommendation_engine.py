from json import loads
from math import ceil, floor
from typing import Dict, List, Tuple, Union
from python_framework.thread_safe_cache import ThreadSafeCache
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from objects.instance_recommendations import (
    ModelInstanceRecommendations,
    ModelInstanceResourceProfile,
    ResourceProfile,
    ResourceProfileConfig,
    ResourceProfileId,
    ResourceProfileState,
    ResourceRecommendation,
)
from objects.metrics import InstanceMetrics, PersistedInstanceMetrics, RunningAverages
from objects.k8s import K8sPodResources

PROFILE_CONFIGS = """
[
    {
        "id": "CPU_MIN",
        "state": "VERY_UNDER",
        "min": 0,
        "max": 40
    },
    {
        "id": "CPU_MIN",
        "state": "UNDER",
        "min": 40,
        "max": 65
    },
    {
        "id": "CPU_MIN",
        "state": "RECOMMENDED",
        "min": 65,
        "max": 85
    },
    {
        "id": "CPU_MIN",
        "state": "OVER",
        "min": 85,
        "max": 95
    },
    {
        "id": "CPU_MIN",
        "state": "VERY_OVER",
        "min": 95,
        "max": 10000
    },
    {
        "id": "CPU_MAX",
        "state": "VERY_UNDER",
        "min": 0,
        "max": 40
    },
    {
        "id": "CPU_MAX",
        "state": "UNDER",
        "min": 40,
        "max": 65
    },
    {
        "id": "CPU_MAX",
        "state": "RECOMMENDED",
        "min": 65,
        "max": 85
    },
    {
        "id": "CPU_MAX",
        "state": "OVER",
        "min": 85,
        "max": 95
    },
    {
        "id": "CPU_MAX",
        "state": "VERY_OVER",
        "min": 95,
        "max": 10000
    },
    {
        "id": "MEMORY_MIN",
        "state": "VERY_UNDER",
        "min": 0,
        "max": 40
    },
    {
        "id": "MEMORY_MIN",
        "state": "UNDER",
        "min": 40,
        "max": 65
    },
    {
        "id": "MEMORY_MIN",
        "state": "RECOMMENDED",
        "min": 65,
        "max": 80
    },
    {
        "id": "MEMORY_MIN",
        "state": "OVER",
        "min": 80,
        "max": 90
    },
    {
        "id": "MEMORY_MIN",
        "state": "VERY_OVER",
        "min": 90,
        "max": 10000
    },
    {
        "id": "MEMORY_MAX",
        "state": "VERY_UNDER",
        "min": 0,
        "max": 40
    },
    {
        "id": "MEMORY_MAX",
        "state": "UNDER",
        "min": 40,
        "max": 65
    },
    {
        "id": "MEMORY_MAX",
        "state": "RECOMMENDED",
        "min": 65,
        "max": 80
    },
    {
        "id": "MEMORY_MAX",
        "state": "OVER",
        "min": 80,
        "max": 90
    },
    {
        "id": "MEMORY_MAX",
        "state": "VERY_OVER",
        "min": 90,
        "max": 10000
    }
]
"""


class RecommendationEngine:

    _instance: "RecommendationEngine" = None
    _logger_key: str = None

    model_recommendations: ThreadSafeCache[str, ModelInstanceRecommendations]
    profile_configs: Dict[str, List[ResourceProfileConfig]]

    def __init__(self):
        self._logger_key = "RecommendationEngine"

        self.model_recommendations = ThreadSafeCache()

        self.profile_configs = {}

        for profile_config in list(
            map(ResourceProfileConfig.from_object, loads(PROFILE_CONFIGS))
        ):
            if profile_config.id not in self.profile_configs:
                self.profile_configs[profile_config.id] = [profile_config]
            else:
                self.profile_configs[profile_config.id].append(profile_config)

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "RecommendationEngine":
        if RecommendationEngine._instance is not None:
            return RecommendationEngine._instance

        RecommendationEngine._instance = RecommendationEngine()

        return RecommendationEngine._instance

    @staticmethod
    def instance() -> "RecommendationEngine":
        return RecommendationEngine._instance

    def profile_resources_batch(
        self,
        metrics_batch: List[Union[InstanceMetrics, PersistedInstanceMetrics]],
        k8s_resources: K8sPodResources,
    ) -> ModelInstanceResourceProfile:
        batched_cpu_running_averages = RunningAverages()
        batched_memory_running_averages = RunningAverages()

        for metrics in metrics_batch:
            if metrics.cpu_running_averages.min >= 0 and (
                batched_cpu_running_averages.min == -1
                or metrics.cpu_running_averages.min < batched_cpu_running_averages.min
            ):
                batched_cpu_running_averages.min = metrics.cpu_running_averages.min

            if metrics.cpu_running_averages.max >= 0 and (
                batched_cpu_running_averages.max == -1
                or metrics.cpu_running_averages.max > batched_cpu_running_averages.max
            ):
                batched_cpu_running_averages.max = metrics.cpu_running_averages.max

            if metrics.memory_running_averages.min >= 0 and (
                batched_memory_running_averages.min == -1
                or metrics.memory_running_averages.min
                < batched_memory_running_averages.min
            ):
                batched_memory_running_averages.min = (
                    metrics.memory_running_averages.min
                )

            if metrics.memory_running_averages.max >= 0 and (
                batched_memory_running_averages.max == -1
                or metrics.memory_running_averages.max
                > batched_memory_running_averages.max
            ):
                batched_memory_running_averages.max = (
                    metrics.memory_running_averages.max
                )

        return ModelInstanceResourceProfile(
            ResourceProfile(
                min_usage=batched_cpu_running_averages.min,
                min_allocatable=(
                    -1.0
                    if k8s_resources.cpu_request is None
                    else float(k8s_resources.cpu_request)
                ),
                max_usage=batched_cpu_running_averages.max,
                max_allocatable=(
                    -1.0
                    if k8s_resources.cpu_limit is None
                    else float(k8s_resources.cpu_limit)
                ),
            ),
            # convert bytes to megabytes
            ResourceProfile(
                min_usage=batched_memory_running_averages.min / 1024 / 1024,
                min_allocatable=(
                    -1.0
                    if k8s_resources.memory_request is None
                    else float(k8s_resources.memory_request)
                ),
                max_usage=batched_memory_running_averages.max / 1024 / 1024,
                max_allocatable=(
                    -1.0
                    if k8s_resources.memory_limit is None
                    else float(k8s_resources.memory_limit)
                ),
            ),
        )

    def _calculate_profile_values(
        self, profile_min: int, profile_max: int, resource_value: float
    ) -> Tuple[int, int]:
        """
        Calculate the min and max values, based on given percentages and value.
        The given resource_value should fall in the center of the bracket.
        """
        # this is the percentage of the "center", i.e. the resource value
        profile_mid = profile_min + (profile_max - profile_min) / 2
        profile_min_diff = profile_mid - profile_min
        profile_max_diff = profile_max - profile_mid

        # min and max values is the percentage "diff" from the middle
        return (
            int(floor(resource_value - (resource_value * profile_min_diff / 100))),
            int(ceil(resource_value + (resource_value * profile_max_diff / 100))),
        )

    def _calculate_profile_recommendations(
        self, profile_id: ResourceProfileId, resource_profile: ResourceProfile
    ) -> ResourceRecommendation:
        recommendation = ResourceRecommendation(
            profile_id=profile_id,
            current_usage_value=0,
            current_allocation_value=0,
            current_usage_percentage=0,
            current_profile_state=None,
            recommended_profile=list(
                filter(
                    lambda x: x.state == ResourceProfileState.RECOMMENDED,
                    self.profile_configs[profile_id],
                )
            )[0],
            recommended_min_value=0.0,
            recommended_max_value=0.0,
        )

        if profile_id in [ResourceProfileId.CPU_MAX, ResourceProfileId.MEMORY_MAX]:
            recommendation.current_usage_value = resource_profile.max_usage
            recommendation.current_allocation_value = resource_profile.max_allocatable
            recommendation.current_usage_percentage = (
                resource_profile.max_usage_percentage
            )
        elif profile_id in [ResourceProfileId.CPU_MIN, ResourceProfileId.MEMORY_MIN]:
            recommendation.current_usage_value = resource_profile.min_usage
            recommendation.current_allocation_value = resource_profile.min_allocatable
            recommendation.current_usage_percentage = (
                resource_profile.min_usage_percentage
            )

        (
            recommendation.recommended_min_value,
            recommendation.recommended_max_value,
        ) = self._calculate_profile_values(
            recommendation.recommended_profile.min,
            recommendation.recommended_profile.max,
            recommendation.current_usage_value,
        )

        for profile_config in self.profile_configs[profile_id]:
            if (
                recommendation.current_usage_percentage >= profile_config.min
                and recommendation.current_usage_percentage < profile_config.max
            ):
                recommendation.current_profile_state = profile_config
                break

        return recommendation

    def calculate_recommendations(
        self, resource_profile: ModelInstanceResourceProfile
    ) -> ModelInstanceRecommendations:
        return ModelInstanceRecommendations(
            cpu_min=self._calculate_profile_recommendations(
                ResourceProfileId.CPU_MIN, resource_profile.cpu
            ),
            cpu_max=self._calculate_profile_recommendations(
                ResourceProfileId.CPU_MAX, resource_profile.cpu
            ),
            memory_min=self._calculate_profile_recommendations(
                ResourceProfileId.MEMORY_MIN, resource_profile.memory
            ),
            memory_max=self._calculate_profile_recommendations(
                ResourceProfileId.MEMORY_MAX, resource_profile.memory
            ),
        )
