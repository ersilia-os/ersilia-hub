from sys import exc_info, stdout
import traceback
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler
from objects.rbac import Permission
from controllers.recommendation_engine import RecommendationEngine
from objects.instance_recommendations import (
    ApplyRecommendationsModel,
    ModelInstanceRecommendationsModel,
    RecommendationEngineStateModel,
    RecommendationsLoadFilters,
)
from python_framework.logger import ContextLogger, LogLevel

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("")
def load_recommendations(
    filters: Annotated[RecommendationsLoadFilters, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    recommendations = RecommendationEngine.instance().load_recommendations(
        filters.model_ids
    )

    return RecommendationEngineStateModel.from_object(recommendations)


@router.post("/apply")
def apply_recommendations(
    application: ApplyRecommendationsModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if application is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    try:
        updated_recommendations = RecommendationEngine.instance().apply_recommendations(
            application.recommendations, application.profiles
        )

        return ModelInstanceRecommendationsModel.from_object(updated_recommendations)
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            "Failed to apply model recommendations, error = [%s]" % repr(exc_info()),
        )
        traceback.print_exc(file=stdout)
        raise HTTPException(
            status_code=500,
            detail="Failed to apply model recommendations",
        )
