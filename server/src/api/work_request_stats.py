from typing import Annotated

from controllers.work_request import WorkRequestController

from fastapi import APIRouter, HTTPException, Query, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler

from objects.rbac import Permission
from objects.work_request_stats import (
    WorkRequestStatsFilterData,
    WorkRequestStatsFilters,
    WorkRequestStatsListModel,
)


###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/work-request-stats", tags=["work-requests"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("")
def load_stats(
    filters: Annotated[WorkRequestStatsFilters, Query()],
    api_request: Request,
) -> WorkRequestStatsListModel:
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    filters_dict = filters.to_object()
    stats = WorkRequestController.instance().load_stats(**filters_dict)

    if stats is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to load stats, see server logs",
        )

    return WorkRequestStatsListModel(stats=stats)


@router.get("/filter-data")
def load_filter_data(
    api_request: Request,
) -> WorkRequestStatsFilterData:
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    return WorkRequestController.instance().load_stats_filter_data()
