from threading import Event, Thread

from python_framework.thread_safe_cache import ThreadSafeCache
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from controllers.k8s import K8sController
from controllers.instance_metrics import InstanceMetricsController
from objects.k8s import K8sNode


class NodeMonitor(Thread):

    node: K8sNode
    metrics_collection_rate: int
    _logger_key: str

    _kill_event: Event

    def __init__(self, node: K8sNode, metrics_collection_rate: int = 3):
        Thread.__init__(self)

        self._kill_event = Event()
        self._logger_key = f"NodeMonitor[{node.name}]"

        self.node = node
        self.metrics_collection_rate = metrics_collection_rate

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_NodeMonitor", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def on_node_started(self):
        pass

    def on_node_terminated(self):
        pass

    def _scrape_metrics(self):
        metrics = K8sController.instance().scrape_node_metrics(self.node.name)

        if metrics is None or len(metrics) == 0:
            ContextLogger.warn(self._logger_key, "No metrics returned by node")
            return

        InstanceMetricsController.instance().ingest_metrics_batch(metrics)

    def run(self):
        ContextLogger.info(self._logger_key, "Monitor started")
        self.on_node_started()

        while True:
            self._scrape_metrics()

            if self._wait_or_kill(self.metrics_collection_rate):
                break

        self.on_node_terminated()

        ContextLogger.info(self._logger_key, "Monitor stopped")

        del ContextLogger.instance().context_logger_map[self._logger_key]


class NodeMonitorControllerKillInstance(KillInstance):
    def kill(self):
        NodeMonitorController.instance().kill()


class NodeMonitorController(Thread):

    _instance: "NodeMonitorController" = None
    _logger_key: str = None
    _kill_event: Event

    node_monitors: ThreadSafeCache[str, NodeMonitor]

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "NodeMonitorController"
        self._kill_event = Event()

        self.node_monitors = ThreadSafeCache()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "NodeMonitorController":
        if NodeMonitorController._instance is not None:
            return NodeMonitorController._instance

        NodeMonitorController._instance = NodeMonitorController()
        GracefulKiller.instance().register_kill_instance(
            NodeMonitorControllerKillInstance()
        )

        return NodeMonitorController._instance

    @staticmethod
    def instance() -> "NodeMonitorController":
        return NodeMonitorController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _update_active_nodes(self):
        new_nodes = K8sController.instance().list_nodes()

        # add new nodes
        for node in new_nodes:
            if node.name in self.node_monitors:
                continue

            node_monitor = NodeMonitor(node)
            self.node_monitors[node.name] = node_monitor
            node_monitor.start()

        # remove terminated nodes
        for node in self.node_monitors.values():
            node_found = False

            for new_node in new_nodes:
                if node.node.name == new_node.name:
                    node_found = True
                    break

            if not node_found:
                self.node_monitors[node.node.name].kill()
                del self.node_monitors[node.node.name]

    def terminate_monitors(self, wait=False):
        for monitor in self.node_monitors.values():
            monitor.kill()

        if wait:
            for monitor in self.node_monitors.values():
                monitor.join()

    def run(self):
        ContextLogger.info(self._logger_key, "controller started")

        while True:
            if self._wait_or_kill(10):
                break

            self._update_active_nodes()

        self.terminate_monitors()

        ContextLogger.info(self._logger_key, "controller stopped.")
