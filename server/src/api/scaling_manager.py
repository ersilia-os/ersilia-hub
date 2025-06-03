from controllers.scaling_manager import ScalingManager
from fastapi import APIRouter, HTTPException, Request

from library.fastapi_root import FastAPIRoot
from objects.model import ModelInstance
from controllers.model import ModelController
from library.api_utils import api_handler

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/scaling", tags=["scaling"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.post("/acquire-instance")
def acquire_instance(
    request: ModelInstance,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    models = ModelController.instance().get_models()

    if not any(map(lambda x: x.id == request.model_id, models)):
        raise HTTPException(
            status_code=400,
            detail="Invalid request body - No model with id [%s]" % request.model_id,
        )

    instance = ScalingManager.instance().acquire_instance(
        request.model_id, request.request_id
    )

    if instance is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to acquire instance of model with id [%s]"
            % request.model_id,
        )

    return instance.to_object()


@router.post("/release-instance")
def release_instance(
    request: ModelInstance,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    ScalingManager.instance().release_instance(request.model_id, request.request_id)

    return {"result": "success"}
