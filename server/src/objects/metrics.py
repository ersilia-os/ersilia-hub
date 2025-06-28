from json import dumps, loads
from typing import Any, Dict

from library.data_buffer import DataBuffer, NodeData
from python_framework.advanced_threading import synchronized_method

from server.src.db.daos.instance_metrics import InstanceMetricsRecord


class PodMetricValue(NodeData):
    metric_name: str
    namespace: str
    pod: str
    value: float

    def __init__(
        self,
        metric_name: str,
        namespace: str,
        pod: str,
        value: float,
        timestamp: float,
    ):
        super().__init__(timestamp)

        self.metric_name = metric_name
        self.namespace = namespace
        self.pod = pod
        self.value = value

    def data(self) -> float:
        return self.value

    def repr_data(self) -> str:
        return str(self.value)

    @staticmethod
    def from_parsed_line(
        metric_name: str, labels: Dict[str, str], value: str, timestamp: str
    ) -> "PodMetricValue":
        try:
            return PodMetricValue(
                metric_name,
                labels["namespace"],
                labels["pod"],
                float(value),
                int(timestamp),
            )
        except:
            return None


class RunningAverages:

    count: int
    total: float
    min: float
    max: float
    avg: float

    count_60s: int
    total_60s: float
    min_60s: float
    max_60s: float
    avg_60s: float

    def __init__(
        self,
        count: int = 0,
        total: float = 0,
        min: float = -1,
        max: float = -1,
        avg: float = -1,
        count_60s: int = 0,
        total_60s: float = 0,
        min_60s: float = -1,
        max_60s: float = -1,
        avg_60s: float = -1,
    ):
        self.count = count
        self.total = total
        self.min = min
        self.max = max
        self.avg = avg

        self.count_60s = count_60s
        self.total_60s = total_60s
        self.min_60s = min_60s
        self.max_60s = max_60s
        self.avg_60s = avg_60s

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "RunningAverages":
        return RunningAverages(
            obj["count"],
            obj["total"],
            obj["min"],
            obj["max"],
            obj["avg"],
            obj["count_60s"],
            obj["total_60s"],
            obj["min_60s"],
            obj["max_60s"],
            obj["avg_60s"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "total": self.total,
            "min": self.min,
            "max": self.max,
            "avg": self.avg,
            "count_60s": self.count_60s,
            "total_60s": self.total_60s,
            "min_60s": self.min_60s,
            "max_60s": self.max_60s,
            "avg_60s": self.avg_60s,
        }

    def update(self, new_value: PodMetricValue, buffer: DataBuffer):
        self.count += 1
        self.total += new_value.value

        if self.min == -1 or self.min > new_value.value:
            self.min = new_value.value

        if self.max == -1 or self.max < new_value.value:
            self.max = new_value.value

        self.avg = self.total / self.count

        new_count_60s = 0
        new_total_60s = 0
        new_min_60s = -1
        new_max_60s = -1

        x: PodMetricValue
        for x in buffer.slice_values(60):
            new_count_60s += 1
            new_total_60s += x.value

            if new_max_60s == -1 or x.value > new_max_60s:
                new_max_60s = x.value

            if new_min_60s == -1 or x.value < new_min_60s:
                new_min_60s = x.value

        self.count_60s = new_count_60s
        self.total_60s = new_total_60s
        self.max_60s = new_max_60s
        self.min_60s = new_min_60s
        self.avg_60s = self.total_60s / self.count_60s


# Very targetted set of Pod Metrics
class InstanceMetrics:
    model_id: str
    instance_id: str
    namespace: str

    cpu_usage_seconds_total: DataBuffer
    cpu_running_averages: RunningAverages
    memory_working_set_bytes: DataBuffer
    memory_running_averages: RunningAverages

    def __init__(self, model_id: str, instance_id: str, namespace: str):
        self.model_id = model_id
        self.instance_id = instance_id
        self.namespace = namespace

        self.cpu_usage_seconds_total = DataBuffer()
        self.cpu_running_averages = RunningAverages()
        self.memory_working_set_bytes = DataBuffer()
        self.memory_running_averages = RunningAverages()

    @synchronized_method
    def push_metric_value(self, value: PodMetricValue):
        if value.metric_name == "container_cpu_usage_seconds_total":
            self.cpu_usage_seconds_total.append(value)
            self.cpu_running_averages.update(value, self.cpu_usage_seconds_total)
        elif value.metric_name == "container_memory_working_set_bytes":
            self.memory_working_set_bytes.append(value)
            self.memory_running_averages.update(value, self.memory_working_set_bytes)


class PersistedInstanceMetrics:

    model_id: str
    instance_id: str
    cpu_running_averages: RunningAverages
    memory_running_averages: RunningAverages
    timestamp: str

    def __init__(
        self,
        model_id: str,
        instance_id: str,
        cpu_running_averages: RunningAverages,
        memory_running_averages: RunningAverages,
        timestamp: str = None,
    ):
        self.model_id = model_id
        self.instance_id = instance_id
        self.cpu_running_averages = cpu_running_averages
        self.memory_running_averages = memory_running_averages
        self.timestamp = timestamp

    @staticmethod
    def init_from_record(record: InstanceMetricsRecord) -> "PersistedInstanceMetrics":
        return PersistedInstanceMetrics(
            record.modelid,
            record.instanceid,
            RunningAverages.from_object(loads(record.cpu_running_averages)),
            RunningAverages.from_object(loads(record.memory_running_averages)),
            record.timestamp,
        )

    def to_record(self) -> InstanceMetricsRecord:
        return InstanceMetricsRecord.init(
            modelid=self.model_id,
            instanceid=self.instance_id,
            cpurunningaverages=dumps(self.cpu_running_averages.to_object()),
            memoryrunningaverages=dumps(self.memory_running_averages.to_object()),
        )
