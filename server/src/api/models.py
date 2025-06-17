from sys import stdout
import traceback

from controllers.model import ModelController
from fastapi import APIRouter, HTTPException, Request

from library.fastapi_root import FastAPIRoot
from objects.model import ModelApiModel, ModelScalingInfoModel, ModelUpdateApiModel

from library.api_utils import api_handler
from objects.rbac import Permission

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/models", tags=["models"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("")
def load_models(
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    return {
        "items": list(
            map(
                lambda x: ModelApiModel.from_object(x),
                ModelController.instance().get_models(),
            )
        )
    }


@router.get("/{model_id}")
def load_model(
    model_id: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    model = ModelController.instance().get_model(model_id)

    if model is None:
        raise HTTPException(
            status_code=404, detail="Model with id [%s] not found" % model_id
        )

    return ModelApiModel.from_object(model)


@router.get("/{model_id}/scaling-info")
def load_model_scaling_info(
    model_id: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    scaling_info = ModelController.instance().get_model_scaling_info(model_id)

    if scaling_info is None:
        raise HTTPException(
            status_code=404, detail="Model with id [%s] not found" % model_id
        )

    return ModelScalingInfoModel.from_object(scaling_info)


@router.post("")
def create_model(
    model: ModelApiModel,
    api_request: Request,
) -> ModelApiModel:
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if model is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    if ModelController.instance().model_exists(model.id):
        raise HTTPException(
            status_code=409, detail="Model id [%s] already exists" % model.id
        )

    persisted_model = None

    try:
        persisted_model = ModelController.instance().create_model(model.to_object())
    except:
        traceback.print_exc(file=stdout)

    if persisted_model is None:
        raise HTTPException(
            status_code=500, detail="Failed to create model, check server logs"
        )

    return ModelApiModel.from_object(persisted_model)


@router.put("/{model_id}")
def update_model(
    model_id: str,
    model_update: ModelUpdateApiModel,
    api_request: Request,
) -> ModelApiModel:
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    if model_update is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    if not ModelController.instance().model_exists(model_id):
        raise HTTPException(
            status_code=400, detail="Model id [%s] does not exist" % model_id
        )

    persisted_model = None

    try:
        model_update.id = model_id
        persisted_model = ModelController.instance().update_model(
            model_update.to_object()
        )
    except:
        traceback.print_exc(file=stdout)

    if persisted_model is None:
        raise HTTPException(
            status_code=500, detail="Failed to update model, check server logs"
        )

    return ModelApiModel.from_object(persisted_model)
