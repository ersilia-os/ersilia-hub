from threading import Thread
from typing import List

from objects.metrics import PodMetricValue, PodMetrics
from python_framework.thread_safe_cache import ThreadSafeCache
from re import compile
from platform import node
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable


class PodMetricsController:

    POD_METRICS_REGEX = compile(
        r"^\s*(container_cpu_usage_seconds_total|container_memory_working_set_bytes)\{([^}]+)\}\s+([0-9.e+]*)\s+(\d+)\s*$"
    )
    # groups: 1 = metric_name, 2 = labels list, 3 = value, 4 = timestamp

    _instance: "PodMetricsController" = None
    _logger_key: str = None

    _pod_metrics: ThreadSafeCache[str, PodMetrics]

    def __init__(self):
        super().__init__(self)

        self._logger_key = "PodMetricsController"

        self._pod_metrics = ThreadSafeCache()

        _hostpod = node()
        self._pod_metrics[f"ersilia-core_{_hostpod}"] = PodMetrics(
            _hostpod, "ersilia-core"
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
    def initialize() -> "PodMetricsController":
        if PodMetricsController._instance is not None:
            return PodMetricsController._instance

        PodMetricsController._instance = PodMetricsController()

        return PodMetricsController._instance

    @staticmethod
    def instance() -> "PodMetricsController":
        return PodMetricsController._instance

    def ingest_metrics_batch(self, metrics_batch: List[str]):
        metric_values = self._parse_metrics_batch(metrics_batch)

        for value in metric_values:
            key = f"{value.namespace}_{value.pod}"

            if key not in self._pod_metrics:
                continue

            self._pod_metrics[key].push_metric_value(value)

    def register_pod(self, namespace: str, pod: str):
        key = f"{namespace}_{pod}"

        if key in self._pod_metrics:
            return

        self._pod_metrics[key] = PodMetrics(pod, namespace)

    def remove_pod(self, namespace: str, pod: str):
        key = f"{namespace}_{pod}"

        if key not in self._pod_metrics:
            return

        del self._pod_metrics[key]

    def _parse_metrics_batch(self, metrics_batch: List[str]) -> List[PodMetricValue]:
        metric_values: List[PodMetricValue] = []

        for line in metrics_batch:
            line_match = PodMetricsController.POD_METRICS_REGEX.fullmatch(line)

            if line_match is None or len(line_match.groups()) < 4:
                continue

            labels = dict(map(lambda x: x.split("="), line_match.group(2).split(",")))

            try:
                if f"{labels['namespace']}_{labels['pod']}" not in self._pod_metrics:
                    continue
            except:
                # missing labels
                continue

            metric_value = PodMetricValue.from_parsed_line(
                line_match.group(1),
                labels,
                line_match.group(3),
                line_match.group(4),
            )

            if metric_value is None:
                continue

            metric_values.append(metric_value)

        return metric_values

    def persist_metrics(
        self, namespace: str = None, pod: str = None, pod_metrics: PodMetrics = None
    ) -> bool:
        _pod_metrics: PodMetrics = pod_metrics

        if namespace is not None and pod is not None:
            key = f"{namespace}_{pod}"

            if key in self._pod_metrics:
                _pod_metrics = self._pod_metrics[key]

        if _pod_metrics is None:
            ContextLogger.error(
                self._logger_key, "Failed to persist PodMetrics, no Pod found"
            )
            return False

        # TODO: persist

        return True
