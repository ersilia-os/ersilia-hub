from json import loads
from math import ceil, floor
from sys import exc_info, stdout
from threading import Event, Lock, Thread
import traceback
from typing import Dict, List, Tuple, Union
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.thread_safe_cache import ThreadSafeCache
from python_framework.logger import ContextLogger, LogLevel
from python_framework.time import utc_now, is_date_in_range_from_now, TimeWindow, Time
from python_framework.config_utils import load_environment_variable

from objects.instance_recommendations import (
    ModelInstanceRecommendations,
    ModelInstanceResourceProfile,
    RecommendationEngineState,
    ResourceId,
    ResourceProfile,
    ResourceProfileConfig,
    ResourceProfileId,
    ResourceProfileState,
    ResourceRecommendation,
)
from objects.metrics import InstanceMetrics, PersistedInstanceMetrics, RunningAverages
from objects.k8s import K8sPodResources
from controllers.model import ModelController
from controllers.model_instance_handler import ModelInstanceController
from objects.model import Model, ModelUpdate
from objects.instance import ModelInstance

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
        "max": 85,
        "minValue": 10
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
        "max": 85,
        "minValue": 200
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
        "max": 80,
        "minValue": 100
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
        "max": 80,
        "minValue": 300
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


class RecommendationEngineKillInstance(KillInstance):
    def kill(self):
        RecommendationEngine.instance().kill()


class RecommendationEngine(Thread):

    _instance: "RecommendationEngine" = None
    _logger_key: str = None
    _kill_event: Event

    last_updated: str | None
    refresh_window: TimeWindow
    model_recommendations: ThreadSafeCache[str, ModelInstanceRecommendations]
    model_recommendation_locks: ThreadSafeCache[str, Lock]
    profile_configs: Dict[str, List[ResourceProfileConfig]]

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "RecommendationEngine"
        self._kill_event = Event()

        self.last_updated = None
        self.refresh_window = TimeWindow(Time(0, 0, 0, 0), Time(4, 0, 0, 0))
        self.model_recommendations = ThreadSafeCache()
        self.model_recommendation_locks = ThreadSafeCache()

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

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    @staticmethod
    def initialize() -> "RecommendationEngine":
        if RecommendationEngine._instance is not None:
            return RecommendationEngine._instance

        RecommendationEngine._instance = RecommendationEngine()
        GracefulKiller.register_kill_instance(RecommendationEngineKillInstance())

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
            if metrics is None:
                continue

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
        self,
        profile_id: ResourceProfileId,
        profile_min: int,
        profile_max: int,
        resource_value: float,
    ) -> Tuple[int, int]:
        """
        Calculate the min and max values, based on given percentages and value.
        The given resource_value should fall in the center of the bracket.
        """
        # this is the percentage of the "center", i.e. the resource value
        profile_range_diff = profile_max - profile_min

        # min and max values is the percentage "diff" from the middle
        recommended_min_value = int(floor(100 * resource_value / profile_min))
        recommended_max_value = int(ceil(100 * resource_value / profile_max))

        recommended_profile = list(
            filter(
                lambda x: x.state == ResourceProfileState.RECOMMENDED,
                self.profile_configs[profile_id],
            )
        )[0]

        if recommended_min_value < recommended_profile.min_value:
            recommended_min_value = recommended_profile.min_value
            adjusted_max_value = recommended_min_value + (
                recommended_min_value * profile_range_diff / 100
            )

            if recommended_max_value < adjusted_max_value:
                recommended_max_value = adjusted_max_value

        recommended_value = int(
            ceil(
                recommended_min_value
                + (recommended_max_value - recommended_min_value) / 2
            )
        )

        # apply

        return recommended_min_value, recommended_max_value, recommended_value

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
            current_allocation_percentage=0,
            current_allocation_profile_state=None,
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
            recommendation.recommended_value,
        ) = self._calculate_profile_values(
            profile_id,
            recommendation.recommended_profile.min,
            recommendation.recommended_profile.max,
            recommendation.current_usage_value,
        )

        if recommendation.current_allocation_value < recommendation.recommended_value:
            recommendation.current_allocation_percentage = -(
                100
                - int(
                    recommendation.current_allocation_value
                    / recommendation.recommended_value
                    * 100
                )
            )
        elif recommendation.current_allocation_value > recommendation.recommended_value:
            recommendation.current_allocation_percentage = (
                int(
                    recommendation.current_allocation_value
                    / recommendation.recommended_value
                    * 100
                )
                - 100
            )
        else:
            recommendation.current_allocation_percentage = 0

        for profile_config in self.profile_configs[profile_id]:
            if (
                recommendation.current_usage_percentage >= profile_config.min
                and recommendation.current_usage_percentage < profile_config.max
            ):
                recommendation.current_profile_state = profile_config
                break

        recommendation.current_allocation_profile_state = ResourceProfileConfig(
            profile_id, ResourceProfileState.RECOMMENDED, -1, -1, None
        )

        # hardcoded brackets: (,-35], (-35, 10], (-10, 10), [10, 35), [35,)
        if recommendation.current_allocation_percentage <= -35:
            recommendation.current_allocation_profile_state.state = (
                ResourceProfileState.VERY_UNDER
            )
        elif recommendation.current_allocation_percentage <= -10:
            recommendation.current_allocation_profile_state.state = (
                ResourceProfileState.UNDER
            )
        elif recommendation.current_allocation_percentage >= 35:
            recommendation.current_allocation_profile_state.state = (
                ResourceProfileState.VERY_OVER
            )
        elif recommendation.current_allocation_percentage >= 10:
            recommendation.current_allocation_profile_state.state = (
                ResourceProfileState.OVER
            )
        elif (
            recommendation.current_allocation_percentage > -10
            and recommendation.current_allocation_percentage < 10
        ):
            recommendation.current_allocation_profile_state.state = (
                ResourceProfileState.RECOMMENDED
            )

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

    def _update_model_recommendation_resource_profile(
        self, model_id: str, new_k8s_resources: K8sPodResources
    ):
        if not self._acquire_model_recommendation_lock(model_id):
            raise Exception("Failed to acquire model recommendation lock")

        try:
            recommendations = self.model_recommendations[model_id].copy()
            current_profiles = recommendations.extract_resource_profiles()

            #  update profile values
            current_profiles[ResourceId.CPU].min_allocatable = (
                new_k8s_resources.cpu_request
            )
            current_profiles[ResourceId.CPU].max_allocatable = (
                new_k8s_resources.cpu_limit
            )
            current_profiles[ResourceId.CPU].calculate()
            current_profiles[ResourceId.MEMORY].min_allocatable = (
                new_k8s_resources.memory_request
            )
            current_profiles[ResourceId.MEMORY].max_allocatable = (
                new_k8s_resources.memory_limit
            )
            current_profiles[ResourceId.CPU].calculate()

            recommendations.cpu_min = self._calculate_profile_recommendations(
                ResourceProfileId.CPU_MIN, current_profiles[ResourceId.CPU]
            )
            recommendations.cpu_max = self._calculate_profile_recommendations(
                ResourceProfileId.CPU_MAX, current_profiles[ResourceId.CPU]
            )
            recommendations.memory_min = self._calculate_profile_recommendations(
                ResourceProfileId.MEMORY_MIN, current_profiles[ResourceId.MEMORY]
            )
            recommendations.memory_max = self._calculate_profile_recommendations(
                ResourceProfileId.MEMORY_MAX, current_profiles[ResourceId.MEMORY]
            )

            # update current_profile state
            for profile_id in [
                ResourceProfileId.CPU_MIN,
                ResourceProfileId.CPU_MAX,
                ResourceProfileId.MEMORY_MIN,
                ResourceProfileId.MEMORY_MAX,
            ]:
                recommendation = recommendations.get_profile_recommendation(profile_id)

                for profile_config in self.profile_configs[profile_id]:
                    if (
                        recommendation.current_usage_percentage >= profile_config.min
                        and recommendation.current_usage_percentage < profile_config.max
                    ):
                        recommendation.current_profile_state = profile_config
                        break

            recommendations.last_updated = utc_now()
            # apply update
            self.model_recommendations[model_id] = recommendations
        except:
            error_str = f"Failed to update model recommendation resource profile, model [{model_id}] - error [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

            raise Exception(error_str)
        finally:
            self.model_recommendation_locks[model_id].release()

    def _acquire_model_recommendation_lock(
        self, model_id: str, timeout: float = 120.0
    ) -> bool:
        if model_id not in self.model_recommendation_locks:
            lock = Lock()
            lock.acquire()
            self.model_recommendation_locks[model_id] = lock

            return True
        else:
            return self.model_recommendation_locks[model_id].acquire(timeout=timeout)

    def _release_model_recommendation_lock(self, model_id: str):
        if model_id not in self.model_recommendation_locks:
            return

        self.model_recommendation_locks[model_id].release()

    def _filter_profilable_instances(
        self, instances: List[ModelInstance]
    ) -> List[ModelInstance]:
        filtered_instances = []

        for instance in instances:
            if instance.metrics is None:
                continue

            filtered_instances.append(instance)

        return filtered_instances

    def refresh_model_recommendations(self, model_id: str):
        ContextLogger.info(
            self._logger_key, f"refreshing recommendations for model [{model_id}]..."
        )

        if not self._acquire_model_recommendation_lock(model_id):
            raise Exception("Failed to acquire model recommendation lock")

        try:
            instances = self._filter_profilable_instances(
                ModelInstanceController.instance().load_persisted_instances([model_id])
            )

            if len(instances) == 0:
                ContextLogger.warn(
                    self._logger_key,
                    f"no profilable instances found for model [{model_id}]",
                )

            model = ModelController.instance().get_model(model_id)

            resource_profile = self.profile_resources_batch(
                list(map(lambda x: x.metrics, instances)), model.details.k8s_resources
            )
            resource_recommendations = self.calculate_recommendations(resource_profile)
            resource_recommendations.model_id = model_id
            resource_recommendations.profiled_instances = list(
                map(lambda x: x.k8s_pod.name, instances)
            )

            self.model_recommendations[model_id] = resource_recommendations
        except:
            error_str = f"Failed to refresh model recommendations, model [{model_id}] - error [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

            raise Exception(error_str)
        finally:
            self.model_recommendation_locks[model_id].release()

    def refresh_all_recommendations(self):
        models = ModelController.instance().get_models()

        # remove deleted models
        for model_id in self.model_recommendations.keys():
            if not any(map(lambda x: x.id == model_id, models)):
                del self.model_recommendations[model_id]

        for model in models:
            try:
                self.refresh_model_recommendations(model.id)
            except:
                ContextLogger.error(
                    self._logger_key,
                    f"Failed to refresh model [{model.id}] recommendations - error [{repr(exc_info())}]",
                )
                traceback.print_exc(file=stdout)

        self.last_updated = utc_now()

    def refresh_missing_recommendations(self):
        models = ModelController.instance().get_models()

        for model in models:
            if model.id not in self.model_recommendations:
                try:
                    self.refresh_model_recommendations(model.id)
                except:
                    ContextLogger.error(
                        self._logger_key,
                        f"Failed to refresh model [{model.id}] recommendations - error [{repr(exc_info())}]",
                    )
                    traceback.print_exc(file=stdout)

    def apply_recommendations(
        self,
        recommendations: ModelInstanceRecommendations,
        apply_profiles: List[ResourceProfileId] = None,
    ) -> ModelInstanceRecommendations:
        _apply_profiles = (
            [
                ResourceProfileId.CPU_MIN,
                ResourceProfileId.CPU_MAX,
                ResourceProfileId.MEMORY_MIN,
                ResourceProfileId.MEMORY_MAX,
            ]
            if apply_profiles is None
            else apply_profiles
        )

        if recommendations.model_id is None:
            error_str = f"Missing model_id on recommendatons"
            ContextLogger.error(self._logger_key, error_str)
            raise Exception(error_str)

        model: Model = ModelController.instance().get_model(recommendations.model_id)

        if model is None:
            error_str = f"Unknown model [{recommendations.model_id}]"
            ContextLogger.error(self._logger_key, error_str)
            raise Exception(error_str)

        ContextLogger.info(
            self._logger_key,
            f"Applying recommendations to model [{recommendations.model_id}], profiles [{_apply_profiles}]...",
        )

        model_update = ModelUpdate(model.id, model.details.copy(), model.enabled)

        for profile in _apply_profiles:
            if profile == ResourceProfileId.CPU_MIN:
                model_update.details.k8s_resources.cpu_request = (
                    recommendations.cpu_min.recommended_value
                )
            elif profile == ResourceProfileId.CPU_MAX:
                model_update.details.k8s_resources.cpu_limit = (
                    recommendations.cpu_max.recommended_value
                )
            elif profile == ResourceProfileId.MEMORY_MIN:
                model_update.details.k8s_resources.memory_request = (
                    recommendations.memory_min.recommended_value
                )
            elif profile == ResourceProfileId.MEMORY_MAX:
                model_update.details.k8s_resources.memory_limit = (
                    recommendations.memory_max.recommended_value
                )

        updated_model = ModelController.instance().update_model(model_update)

        if updated_model is None:
            error_str = (
                f"Failed to apply recommendations to model [{recommendations.model_id}]"
            )
            ContextLogger.error(self._logger_key, error_str)
            raise Exception(error_str)

        self._update_model_recommendation_resource_profile(
            updated_model.id, updated_model.details.k8s_resources
        )

        ContextLogger.info(
            self._logger_key,
            f"Recommendations applied to model [{recommendations.model_id}], profiles [{_apply_profiles}].",
        )

        return self.model_recommendations[recommendations.model_id]

    def load_recommendations(
        self, model_ids: List[str] = None
    ) -> RecommendationEngineState:
        if model_ids is None:
            return RecommendationEngineState(
                last_updated=self.last_updated,
                model_recommendations=dict(self.model_recommendations.items()),
            )

        state = RecommendationEngineState(
            last_updated=self.last_updated, model_recommendations={}
        )

        for key, value in self.model_recommendations.items():
            if key in model_ids:
                state.model_recommendations[key] = value

        return state

    def run(self):
        ContextLogger.info(self._logger_key, "Engine started")

        # wait 45 seconds before running first full recommendation
        if self._wait_or_kill(45):
            ContextLogger.info(self._logger_key, "Engine killed before startup")
            return

        try:
            self.refresh_all_recommendations()
        except:
            ContextLogger.error(
                self._logger_key,
                f"failure in refreshing recommendations: {repr(exc_info())}",
            )
            traceback.print_exc(file=stdout)

        while True:
            if self._wait_or_kill(600):
                break

            # refresh all recommendations nightly:
            # - always refresh if not refreshed previously
            # - don't refresh if refreshed in the last 2 hours
            # - only refresh within time window
            if (
                self.last_updated is None or (
                    not is_date_in_range_from_now(self.last_updated, "-2h")
                    and self.refresh_window.is_time_in_window(Time.from_utc_timestamp(utc_now()))
                )
            ):
                self.refresh_all_recommendations()
                continue

            self.refresh_missing_recommendations()

        ContextLogger.info(self._logger_key, "Engine stopped")
