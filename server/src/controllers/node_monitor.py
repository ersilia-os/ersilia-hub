from threading import Thread


class NodeMonitor(Thread):

    node_name: str

    def __init__(self, node_name: str):
        super().__init__(self)

        self.node_name = node_name

    def run(self):
        # TODO: collect metrics and push to PodMetricsController
        pass


class NodeMonitorController(Thread):

    # TODO: logger + singleton stuff
    # TODO: thread + event stuff

    def __init__(self):
        super().__init__(self)
