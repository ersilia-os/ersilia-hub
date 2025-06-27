from typing import Dict

from library.data_buffer import DataBuffer, NodeData
from python_framework.advanced_threading import synchronized_method


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

    def __init__(self):
        self.count = 0
        self.total = 0
        self.min = -1
        self.max = -1
        self.avg = -1

        self.count_60s = 0
        self.total_60s = 0
        self.min_60s = -1
        self.max_60s = -1
        self.avg_60s = -1

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
class PodMetrics:
    pod_name: str
    namespace: str

    cpu_usage_seconds_total: DataBuffer
    cpu_running_averages: RunningAverages
    memory_working_set_bytes: DataBuffer
    memory_running_averages: RunningAverages

    def __init__(self, pod_name: str, namespace: str):
        self.pod_name = pod_name
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


#
# TODO:
#   1. read all metrics line-by-line and use regex filter to select relevant lines
#       * KISS:
#           - only care about eos-models namespace for now, so only filter by namespace="eos-models"
#           - only care about container_memory_working_set_bytes and container_cpu_usage_seconds_total metrics
#   2. parse metric using MetricValue.parse
#   3. find PodMetrics instance and push metric value (PodMetrics instance might not exist, in which case we ignore the metric)
#
"""
# HELP container_cpu_usage_seconds_total [STABLE] Cumulative cpu time consumed by the container in core-seconds
# TYPE container_cpu_usage_seconds_total counter
container_cpu_usage_seconds_total{container="aws-eks-nodeagent",namespace="kube-system",pod="aws-node-7k649"} 40.384910049 1750705768415
container_cpu_usage_seconds_total{container="aws-load-balancer-controller",namespace="ersilia-core",pod="ersilia-aws-load-balancer-controller-5f7cfb55d8-jbwqw"} 184.554461619 1750705764519
container_cpu_usage_seconds_total{container="aws-node",namespace="kube-system",pod="aws-node-7k649"} 293.769327238 1750705767923
container_cpu_usage_seconds_total{container="ebs-plugin",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 17.420560624 1750705778923
container_cpu_usage_seconds_total{container="eks-pod-identity-agent",namespace="kube-system",pod="eks-pod-identity-agent-59jlc"} 31.063828566 1750705765533
container_cpu_usage_seconds_total{container="frontend",namespace="ersilia-core",pod="ersilia-hub-frontend-75f4f69b7b-dx49p"} 14.939527083 1750705765012
container_cpu_usage_seconds_total{container="kube-proxy",namespace="kube-system",pod="kube-proxy-t748f"} 27.787800906 1750705772883
container_cpu_usage_seconds_total{container="liveness-probe",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 23.290713446 1750705776426
container_cpu_usage_seconds_total{container="nginx",namespace="ersilia-core",pod="ersilia-nginx-567d564fc-cpfvd"} 44.356054006 1750705766568
container_cpu_usage_seconds_total{container="node-driver-registrar",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 18.065376218 1750705777295
container_cpu_usage_seconds_total{container="postgresql",namespace="ersilia-core",pod="ersilia-hub-postgresql-0"} 753.998393487 1750705769183
container_cpu_usage_seconds_total{container="server",namespace="ersilia-core",pod="ersilia-hub-server-78554c56f7-klmrl"} 422.097108038 1750705767237
# HELP container_memory_working_set_bytes [STABLE] Current working set of the container in bytes
# TYPE container_memory_working_set_bytes gauge
container_memory_working_set_bytes{container="aws-eks-nodeagent",namespace="kube-system",pod="aws-node-7k649"} 1.7391616e+07 1750705768415
container_memory_working_set_bytes{container="aws-load-balancer-controller",namespace="ersilia-core",pod="ersilia-aws-load-balancer-controller-5f7cfb55d8-jbwqw"} 2.4911872e+07 1750705764519
container_memory_working_set_bytes{container="aws-node",namespace="kube-system",pod="aws-node-7k649"} 5.023744e+07 1750705767923
container_memory_working_set_bytes{container="ebs-plugin",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 9.015296e+06 1750705778923
container_memory_working_set_bytes{container="eks-pod-identity-agent",namespace="kube-system",pod="eks-pod-identity-agent-59jlc"} 6.131712e+06 1750705765533
container_memory_working_set_bytes{container="frontend",namespace="ersilia-core",pod="ersilia-hub-frontend-75f4f69b7b-dx49p"} 3.3792e+06 1750705765012
container_memory_working_set_bytes{container="kube-proxy",namespace="kube-system",pod="kube-proxy-t748f"} 1.3893632e+07 1750705772883
container_memory_working_set_bytes{container="liveness-probe",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 7.74144e+06 1750705776426
container_memory_working_set_bytes{container="nginx",namespace="ersilia-core",pod="ersilia-nginx-567d564fc-cpfvd"} 4.206592e+06 1750705766568
container_memory_working_set_bytes{container="node-driver-registrar",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 3.923968e+06 1750705777295
container_memory_working_set_bytes{container="postgresql",namespace="ersilia-core",pod="ersilia-hub-postgresql-0"} 4.7992832e+07 1750705769183
container_memory_working_set_bytes{container="server",namespace="ersilia-core",pod="ersilia-hub-server-78554c56f7-klmrl"} 1.97271552e+08 1750705767237
# HELP container_start_time_seconds [STABLE] Start time of the container since unix epoch in seconds
# TYPE container_start_time_seconds gauge
container_start_time_seconds{container="aws-eks-nodeagent",namespace="kube-system",pod="aws-node-7k649"} 1.7506078418297591e+09
container_start_time_seconds{container="aws-load-balancer-controller",namespace="ersilia-core",pod="ersilia-aws-load-balancer-controller-5f7cfb55d8-jbwqw"} 1.7506078491193974e+09
container_start_time_seconds{container="aws-node",namespace="kube-system",pod="aws-node-7k649"} 1.7506078401348257e+09
container_start_time_seconds{container="ebs-plugin",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 1.7506078453624582e+09
container_start_time_seconds{container="eks-pod-identity-agent",namespace="kube-system",pod="eks-pod-identity-agent-59jlc"} 1.7506078383432264e+09
container_start_time_seconds{container="frontend",namespace="ersilia-core",pod="ersilia-hub-frontend-75f4f69b7b-dx49p"} 1.7506078529384658e+09
container_start_time_seconds{container="kube-proxy",namespace="kube-system",pod="kube-proxy-t748f"} 1.7506078364870462e+09
container_start_time_seconds{container="liveness-probe",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 1.7506078503057349e+09
container_start_time_seconds{container="nginx",namespace="ersilia-core",pod="ersilia-nginx-567d564fc-cpfvd"} 1.7506079464872775e+09
container_start_time_seconds{container="node-driver-registrar",namespace="kube-system",pod="ebs-csi-node-v6cqf"} 1.750607848673934e+09
container_start_time_seconds{container="postgresql",namespace="ersilia-core",pod="ersilia-hub-postgresql-0"} 1.750607876466787e+09
container_start_time_seconds{container="server",namespace="ersilia-core",pod="ersilia-hub-server-78554c56f7-klmrl"} 1.7506079118916554e+09
# HELP node_cpu_usage_seconds_total [STABLE] Cumulative cpu time consumed by the node in core-seconds
# TYPE node_cpu_usage_seconds_total counter
node_cpu_usage_seconds_total 6197.005020909 1750705774670
# HELP node_memory_working_set_bytes [STABLE] Current working set of the node in bytes
# TYPE node_memory_working_set_bytes gauge
node_memory_working_set_bytes 1.137475584e+09 1750705774670
# HELP pod_cpu_usage_seconds_total [STABLE] Cumulative cpu time consumed by the pod in core-seconds
# TYPE pod_cpu_usage_seconds_total counter
pod_cpu_usage_seconds_total{namespace="ersilia-core",pod="ersilia-aws-load-balancer-controller-5f7cfb55d8-jbwqw"} 184.599228293 1750705770631
pod_cpu_usage_seconds_total{namespace="ersilia-core",pod="ersilia-hub-frontend-75f4f69b7b-dx49p"} 14.972143397 1750705768998
pod_cpu_usage_seconds_total{namespace="ersilia-core",pod="ersilia-hub-postgresql-0"} 753.978995701 1750705767087
pod_cpu_usage_seconds_total{namespace="ersilia-core",pod="ersilia-hub-server-78554c56f7-klmrl"} 429.028704332 1750705771400
pod_cpu_usage_seconds_total{namespace="ersilia-core",pod="ersilia-nginx-567d564fc-cpfvd"} 44.421506699 1750705766448
pod_cpu_usage_seconds_total{namespace="kube-system",pod="aws-node-7k649"} 334.256356258 1750705773889
pod_cpu_usage_seconds_total{namespace="kube-system",pod="ebs-csi-node-v6cqf"} 58.781453562 1750705764814
pod_cpu_usage_seconds_total{namespace="kube-system",pod="eks-pod-identity-agent-59jlc"} 31.111945355 1750705778297
pod_cpu_usage_seconds_total{namespace="kube-system",pod="kube-proxy-t748f"} 27.798782029 1750705778912
# HELP pod_memory_working_set_bytes [STABLE] Current working set of the pod in bytes
# TYPE pod_memory_working_set_bytes gauge
pod_memory_working_set_bytes{namespace="ersilia-core",pod="ersilia-aws-load-balancer-controller-5f7cfb55d8-jbwqw"} 2.5088e+07 1750705770631
pod_memory_working_set_bytes{namespace="ersilia-core",pod="ersilia-hub-frontend-75f4f69b7b-dx49p"} 3.555328e+06 1750705768998
pod_memory_working_set_bytes{namespace="ersilia-core",pod="ersilia-hub-postgresql-0"} 4.5621248e+07 1750705767087
pod_memory_working_set_bytes{namespace="ersilia-core",pod="ersilia-hub-server-78554c56f7-klmrl"} 1.97947392e+08 1750705771400
pod_memory_working_set_bytes{namespace="ersilia-core",pod="ersilia-nginx-567d564fc-cpfvd"} 4.4032e+06 1750705766448
pod_memory_working_set_bytes{namespace="kube-system",pod="aws-node-7k649"} 7.2933376e+07 1750705773889
pod_memory_working_set_bytes{namespace="kube-system",pod="ebs-csi-node-v6cqf"} 2.086912e+07 1750705764814
pod_memory_working_set_bytes{namespace="kube-system",pod="eks-pod-identity-agent-59jlc"} 6.377472e+06 1750705778297
pod_memory_working_set_bytes{namespace="kube-system",pod="kube-proxy-t748f"} 1.4065664e+07 1750705778912
# HELP resource_scrape_error [STABLE] 1 if there was an error while getting container metrics, 0 otherwise
# TYPE resource_scrape_error gauge
resource_scrape_error 0
"""
