from threading import Thread
from typing import List

from objects.metrics import PodMetricValue, PodMetrics
from python_framework.thread_safe_cache import ThreadSafeCache
from re import compile
from platform import node


class PodMetricsController:

    POD_METRICS_REGEX = compile(
        r"^\s*(container_cpu_usage_seconds_total|container_memory_working_set_bytes)\{([^}]+)\}\s+([0-9.e+]*)\s+(\d+)\s*$"
    )
    # groups: 1 = metric_name, 2 = labels list, 3 = value, 4 = timestamp

    # TODO: singleton stuff

    _pod_metrics: ThreadSafeCache[str, PodMetrics]

    def __init__(self):
        super().__init__(self)

        # TODO: logger stuff

        self._pod_metrics = ThreadSafeCache()

        _hostpod = node()
        self._pod_metrics[f"ersilia-core_{_hostpod}"] = PodMetrics(
            _hostpod, "ersilia-core"
        )

    def ingest_metrics_batch(self, metrics_batch: List[str]):
        metric_values = self._parse_metrics_batch(metrics_batch)

        for value in metric_values:
            key = f"{value.namespace}_{value.pod}"

            if key not in self._pod_metrics:
                continue

            self._pod_metrics[key].push_metric_value(value)

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
