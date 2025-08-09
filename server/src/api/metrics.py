from typing import Annotated
from fastapi import APIRouter, Query, Request

from library.fastapi_root import FastAPIRoot
from library.api_utils import api_handler
from objects.rbac import Permission
from controllers.instance_metrics import InstanceMetricsController
from objects.metrics import InstanceMetricsLoadFilters, InstanceMetricsModel

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("/instances")
def load_instances(
    filters: Annotated[InstanceMetricsLoadFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    metrics = []

    if filters.active:
        metrics.extend(
            map(
                InstanceMetricsModel.from_object,
                InstanceMetricsController.instance().load_active(
                    model_id=filters.model_id
                ),
            )
        )

    # TODO: add persisted here

    return {"items": metrics}
