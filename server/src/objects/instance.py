from pydantic import BaseModel
from server.src.objects.k8s import K8sPod
from server.src.objects.metrics import RunningAverages


class ModelInstance:

    k8s_pod: K8sPod
    running_averages: RunningAverages

    def __init__(
        self,
        k8s_pod: K8sPod,
        running_averages: RunningAverages,
    ):
        self.k8s_pod = k8s_pod
        self.running_averages = running_averages

    def to_object(self) -> "ModelInstanceModel":
        return ModelInstanceModel(
            k8s_pod=self.k8s_pod, running_averages=self.running_averages
        )


class ModelInstanceModel(BaseModel):

    # TODO: add Model classes for these and do a transform
    k8s_pod: K8sPod
    running_averages: RunningAverages
