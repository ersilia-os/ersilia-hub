import traceback
from sys import stdout
from typing import Annotated, List

from controllers.model_instance_handler import ModelInstanceController
from controllers.model_instance_log import ModelInstanceLogController
from controllers.recommendation_engine import RecommendationEngine
from controllers.s3_integration import S3IntegrationController
from fastapi import APIRouter, HTTPException, Query, Request
from library.api_utils import api_handler
from library.fastapi_root import FastAPIRoot
from objects.instance import (
    ExtendedModelInstance,
    ExtendedModelInstanceModel,
    InstanceAction,
    InstanceActionModel,
    InstanceLogsFilters,
    InstancesLoadFilters,
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

    instances: List[ExtendedModelInstance] = (
        ModelInstanceController.instance().load_instances(
            model_ids=(None if filters.model_id is None else [filters.model_id]),
            instance_ids=(
                None if filters.instance_id is None else [filters.instance_id]
            ),
            states=filters.states,
            not_states=filters.not_states,
            extended_state=(
                filters.load_resource_profiles or filters.load_recommendations
            ),
        )
    )

    if filters.load_resource_profiles or filters.load_recommendations:
        for instance in instances:
            if (
                instance.metrics is None
                or instance.model_instance.instance_details is None
                or instance.model_instance.instance_details.resources is None
            ):
                continue

            instance.resource_profile = (
                RecommendationEngine.instance().profile_resources_batch(
                    [instance.metrics],
                    instance.model_instance.instance_details.resources,
                )
            )

    if filters.load_recommendations:
        for instance in instances:
            if (
                instance.resource_profile is None
                or instance.model_instance.instance_details is None
            ):
                continue

            instance.resource_recommendations = (
                RecommendationEngine.instance().calculate_recommendations(
                    instance.resource_profile
                )
            )
            instance.resource_recommendations.model_id = (
                instance.model_instance.instance_details.get_annotation(
                    ErsiliaLabels.MODEL_ID
                )
            )
            instance.resource_recommendations.profiled_instances = [
                instance.model_instance.instance_details.name
            ]

    return {"items": list(map(ExtendedModelInstanceModel.from_object, instances))}


@router.get("job-logs")
def load_instance_job_logs(
    filters: Annotated[InstanceLogsFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if filters.work_request_id is None or filters.model_id is None:
        raise HTTPException(400, detail="Missing work_request_id or model_id filter")

    logs: list[str] | None = None

    try:
        # check if instance is active, load via k8s controller
        instance = ModelInstanceController.instance().get_instance(
            filters.model_id, filters.work_request_id
        )

        _logs_str: str | None = None

        if instance is not None:
            _logs_str = instance.get_pod_logs()
        else:
            _logs_str = S3IntegrationController.instance().download_instance_logs(
                filters.model_id, filters.work_request_id
            )

        if _logs_str is None:
            return HTTPException(404, "No logs found for instance")

        logs = _logs_str.split("\n")

        if filters.tail is not None and filters.tail > 0:
            logs = logs[len(logs) - filters.tail :]
        elif filters.head is not None and filters.head > 0:
            logs = logs[: filters.head]
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

    if action.work_request_id is None or action.model_id is None:
        raise HTTPException(400, detail="Missing work_request_id or model_id filter")

    instance = ModelInstanceController.instance().get_instance(
        action.model_id, action.work_request_id
    )

    if instance is None:
        raise HTTPException(404, detail="Instance not found")

    if action.action == InstanceAction.STOP_INSTANCE.name:
        instance.kill()

        return {"result": "Instance termination requested"}

    raise HTTPException(400, detail=f"Unknown action {action.action}")


@router.get("history")
def load_instance_history(
    filters: Annotated[InstancesLoadFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if filters.work_request_id is None or filters.model_id is None:
        raise HTTPException(400, detail="Missing work_request_id or model_id filter")

    try:
        instance_log = ModelInstanceLogController.instance().load_instance_logs(
            filters.model_id, filters.work_request_id
        )
    except:
        traceback.print_exc(file=stdout)

        raise HTTPException(500, detail="Failed to load logs for instance")

    return {"history": instance_log}
