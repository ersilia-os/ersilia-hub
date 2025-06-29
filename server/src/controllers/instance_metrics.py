from sys import exc_info, stdout
import traceback
from typing import List, Union

from objects.metrics import PersistedInstanceMetrics, PodMetricValue, InstanceMetrics
from python_framework.thread_safe_cache import ThreadSafeCache
from re import compile
from platform import node
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from config.application_config import ApplicationConfig
from db.daos.instance_metrics import (
    InstanceMetricsDAO,
    InstanceMetricsRecord,
)


class InstanceMetricsController:

    POD_METRICS_REGEX = compile(
        r"^\s*(container_cpu_usage_seconds_total|container_memory_working_set_bytes)\{([^}]+)\}\s+([0-9.e+]*)\s+(\d+)\s*$"
    )
    # groups: 1 = metric_name, 2 = labels list, 3 = value, 4 = timestamp

    _instance: "InstanceMetricsController" = None
    _logger_key: str = None

    _instance_metrics: ThreadSafeCache[str, InstanceMetrics]

    def __init__(self):
        self._logger_key = "InstanceMetricsController"

        self._instance_metrics = ThreadSafeCache()

        _hostpod = node()
        self._instance_metrics[f"ersilia-core_{_hostpod}"] = InstanceMetrics(
            "core", _hostpod, "ersilia-core"
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
    def initialize() -> "InstanceMetricsController":
        if InstanceMetricsController._instance is not None:
            return InstanceMetricsController._instance

        InstanceMetricsController._instance = InstanceMetricsController()

        return InstanceMetricsController._instance

    @staticmethod
    def instance() -> "InstanceMetricsController":
        return InstanceMetricsController._instance

    def ingest_metrics_batch(self, metrics_batch: List[str]):
        metric_values = self._parse_metrics_batch(metrics_batch)

        for value in metric_values:
            key = f"{value.namespace}_{value.pod}"

            if key not in self._instance_metrics:
                continue

            # ContextLogger.trace(
            #     self._logger_key,
            #     "pushing metric [%s] to [%s]" % (value.metric_name, key),
            # )
            self._instance_metrics[key].push_metric_value(value)

    def register_instance(self, namespace: str, instance_id: str, model_id: str):
        key = f"{namespace}_{instance_id}"

        if key in self._instance_metrics:
            return

        self._instance_metrics[key] = InstanceMetrics(model_id, instance_id, namespace)

    def remove_instance(self, namespace: str, instance_id: str):
        key = f"{namespace}_{instance_id}"

        if key not in self._instance_metrics:
            return

        del self._instance_metrics[key]

    def get_instance(
        self, namespace: str, instance_id: str
    ) -> Union[None, InstanceMetrics]:
        key = f"{namespace}_{instance_id}"

        if key not in self._instance_metrics:
            return None

        return self._instance_metrics[key]

    def _parse_metrics_batch(self, metrics_batch: List[str]) -> List[PodMetricValue]:
        # ContextLogger.trace(self._logger_key, "parsing metrics batch...")
        metric_values: List[PodMetricValue] = []

        for line in metrics_batch:
            line_match = InstanceMetricsController.POD_METRICS_REGEX.fullmatch(line)
            # ContextLogger.trace(self._logger_key, f"metrics line [{line}]")
            # ContextLogger.trace(
            #     self._logger_key,
            #     "metrics line match groups [%s]"
            #     % (None if line_match is None else str(line_match.groups())),
            # )

            if line_match is None or len(line_match.groups()) < 4:
                continue

            labels = {}

            for k, v in map(lambda x: x.split("="), line_match.group(2).split(",")):
                labels[k] = v.replace('"', "")

            # ContextLogger.trace(self._logger_key, "labels: [%s]" % labels)

            try:
                if (
                    f"{labels['namespace']}_{labels['pod']}"
                    not in self._instance_metrics
                ):
                    # ContextLogger.trace(self._logger_key, "instance not registered")
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
                # ContextLogger.trace(self._logger_key, "failed to parse PodMetricValue")
                continue

            metric_values.append(metric_value)

        # ContextLogger.trace(
        #     self._logger_key, "returning [%d] parsed metrics" % len(metric_values)
        # )

        return metric_values

    def persist_metrics(
        self,
        namespace: str = None,
        instance_id: str = None,
        instance_metrics: InstanceMetrics = None,
    ) -> Union[PersistedInstanceMetrics, None]:
        _metrics: InstanceMetrics = instance_metrics

        if namespace is not None and instance_id is not None:
            key = f"{namespace}_{instance_id}"

            if key in self._instance_metrics:
                _metrics = self._instance_metrics[key]

        if _metrics is None:
            ContextLogger.error(
                self._logger_key, "Failed to persist InstanceMetrics, no Pod found"
            )
            return False

        ContextLogger.debug(
            self._logger_key,
            "Persisting InstanceMetrics for [%s @ %s]..."
            % (_metrics.model_id, _metrics.instance_id),
        )

        try:
            persisted_metrics = PersistedInstanceMetrics(
                _metrics.model_id,
                _metrics.instance_id,
                _metrics.cpu_running_averages,
                _metrics.memory_running_averages,
            )

            results: List[InstanceMetricsRecord] = InstanceMetricsDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **persisted_metrics.to_record().generate_insert_query_args(),
            )

            if results is None or len(results) == 0:
                raise Exception("Insert returned zero records")

            persisted_metrics = PersistedInstanceMetrics.init_from_record(results[0])

            ContextLogger.debug(
                self._logger_key,
                "PersistedInstanceMetrics inserted for [%s @ %s]"
                % (persisted_metrics.model_id, persisted_metrics.instance_id),
            )

            return persisted_metrics
        except:
            error_str = "Failed to insert PersistedInstanceMetrics, error = [%s]" % (
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return None
