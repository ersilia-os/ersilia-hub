from pydantic import BaseModel
from objects.k8s import K8sPod
from objects.k8s_model import K8sPodModel
from objects.metrics import RunningAverages, RunningAveragesModel


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


class ModelInstanceModel(BaseModel):

    # TODO: add Model classes for these and do a transform
    k8s_pod: K8sPodModel
    running_averages: RunningAveragesModel

    @staticmethod
    def from_object(obj: ModelInstance) -> "ModelInstanceModel":
        return ModelInstanceModel(
            k8s_pod=K8sPodModel.from_object(obj.k8s_pod),
            running_averages=RunningAveragesModel.from_object(obj.running_averages),
        )
