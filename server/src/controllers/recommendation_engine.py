from json import loads
from typing import List
from python_framework.thread_safe_cache import ThreadSafeCache
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from objects.instance_recommendations import (
    ModelInstanceRecommendations,
    ModelInstanceResourceProfile,
    ResourceProfileConfig,
)
from objects.metrics import InstanceMetrics

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
    profile_configs: List[ResourceProfileConfig]

    def __init__(self):
        self._logger_key = "RecommendationEngine"

        self.model_recommendations = ThreadSafeCache()
        self.profile_configs = list(
            map(ResourceProfileConfig.from_object, loads(PROFILE_CONFIGS))
        )

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

    def profile_resources(
        self, metrics: InstanceMetrics
    ) -> ModelInstanceResourceProfile:
        # TODO
        pass

    def calculate_recommendations(
        self, resource_profile: ModelInstanceResourceProfile
    ) -> ModelInstanceRecommendations:
        # TODO
        pass
