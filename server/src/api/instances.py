import traceback
from sys import stdout
from typing import Annotated, List

from controllers.model_instance_handler import ModelInstanceController
from controllers.recommendation_engine import RecommendationEngine
from controllers.s3_integration import S3IntegrationController
from fastapi import APIRouter, HTTPException, Query, Request
from library.api_utils import api_handler
from library.fastapi_root import FastAPIRoot
from objects.instance import (
    InstanceAction,
    InstanceActionModel,
    InstancesLoadFilters,
    ModelInstance,
    ModelInstanceModel,
)
from objects.k8s import ErsiliaLabels
from objects.rbac import Permission

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/instances", tags=["instances"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("")
def load_instances(
    filters: Annotated[InstancesLoadFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    instances: List[ModelInstance] = []

    if filters.active:
        instances.extend(
            ModelInstanceController.instance().load_active_instances(
                model_ids=(None if filters.model_id is None else [filters.model_id])
            ),
        )

    if filters.persisted:
        instances.extend(
            ModelInstanceController.instance().load_persisted_instances(
                model_ids=(None if filters.model_id is None else [filters.model_id]),
                instance_id=(
                    None if filters.instance_id is None else [filters.instance_id]
                ),
            ),
        )

    if filters.load_resource_profiles or filters.load_recommendations:
        for instance in instances:
            if instance.metrics is None or instance.k8s_pod.resources is None:
                continue

            instance.resource_profile = (
                RecommendationEngine.instance().profile_resources_batch(
                    [instance.metrics], instance.k8s_pod.resources
                )
            )

    if filters.load_recommendations:
        for instance in instances:
            if instance.resource_profile is None:
                continue

            instance.resource_recommendations = (
                RecommendationEngine.instance().calculate_recommendations(
                    instance.resource_profile
                )
            )
            instance.resource_recommendations.model_id = (
                instance.k8s_pod.get_annotation(ErsiliaLabels.MODEL_ID)
            )
            instance.resource_recommendations.profiled_instances = [
                instance.k8s_pod.name
            ]

    return {"items": list(map(ModelInstanceModel.from_object, instances))}


@router.get("logs")
def load_instance_logs(
    filters: Annotated[InstancesLoadFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if filters.instance_id is None or filters.model_id is None:
        raise HTTPException(400, detail="Missing instance_id or model_id filter")

    logs: str | None = None

    try:
        # check if instance is active, load via k8s controller
        instance = ModelInstanceController.instance().get_instance(
            filters.model_id, filters.instance_id
        )

        if instance is not None:
            logs = instance.get_pod_logs()
        else:
            logs = S3IntegrationController.instance().download_instance_logs(
                filters.model_id, filters.instance_id
            )
    except:
        traceback.print_exc(file=stdout)

        raise HTTPException(500, detail="Failed to load logs for instance")

    return {"logs": logs}


@router.post("actions")
def instance_actions(
    action: InstanceActionModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if action.instance_id is None or action.model_id is None:
        raise HTTPException(400, detail="Missing instance_id or model_id filter")

    instance = ModelInstanceController.instance().get_instance(
        action.model_id, action.instance_id
    )

    if instance is None:
        raise HTTPException(404, detail="Instance not found")

    if action.action == InstanceAction.STOP_INSTANCE.name:
        instance.kill()

        return {"result": "Instance termination requested"}

    raise HTTPException(400, detail=f"Unknown action {action.action}")
