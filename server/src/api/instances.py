from typing import Annotated, List
from fastapi import APIRouter, HTTPException, Query, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler
from objects.rbac import Permission
from controllers.model_instance_handler import ModelInstanceController
from objects.instance import InstancesLoadFilters, ModelInstance, ModelInstanceModel
from server.src.controllers.recommendation_engine import RecommendationEngine

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

    return {"items": list(map(ModelInstanceModel.from_object, instances))}
