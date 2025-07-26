from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler
from objects.rbac import Permission
from controllers.model_instance_handler import ModelInstanceController
from objects.instance import InstancesLoadFilters, ModelInstanceModel

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

    metrics = []

    if filters.active:
        metrics.extend(
            map(
                ModelInstanceModel.from_object,
                ModelInstanceController.instance().load_active_instances(
                    model_ids=(None if filters.model_id is None else [filters.model_id])
                ),
            )
        )

    if filters.persisted:
        metrics.extend(
            map(
                ModelInstanceModel.from_object,
                ModelInstanceController.instance().load_persisted_instances(
                    model_ids=(
                        None if filters.model_id is None else [filters.model_id]
                    ),
                    instance_id=(
                        None if filters.instance_id is None else [filters.instance_id]
                    ),
                ),
            )
        )

    return {"items": metrics}
