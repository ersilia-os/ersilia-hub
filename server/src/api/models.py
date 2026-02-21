import traceback
from sys import exc_info, stdout

from controllers.model import ModelController
from controllers.model_input_cache import ModelInputCache
from fastapi import APIRouter, HTTPException, Request
from library.api_utils import api_handler
from library.fastapi_root import FastAPIRoot
from objects.model import (
    ModelApiModel,
    ModelIdentificationDetailsModel,
    ModelScalingInfoModel,
    ModelUpdateApiModel,
)
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


@router.get("/{model_id}/model-hub-details")
def get_model_hub_details(
    model_id: str, api_request: Request
) -> ModelIdentificationDetailsModel:
    auth_details, tracking_details = api_handler(api_request)

    try:
        model_details = ModelController.instance().get_details_from_model_hub(model_id)

        if model_details is None:
            raise Exception("No ModelHub details found")

        return ModelIdentificationDetailsModel.from_object(model_details)
    except:
        traceback.print_exc(file=stdout)

        raise HTTPException(
            status_code=500,
            detail="Failed to get ModelHub details, err = [%s]" % repr(exc_info()),
        )


@router.get("/{model_id}/ersilia-catalog-details")
def get_ersilia_catalog_details(
    model_id: str, api_request: Request
) -> ModelIdentificationDetailsModel:
    auth_details, tracking_details = api_handler(api_request)

    try:
        model_details = ModelController.instance().get_details_from_ersilia_catalog(
            model_id
        )

        if model_details is None:
            raise Exception("No Ersilia Catalog details found")

        return ModelIdentificationDetailsModel.from_object(model_details)
    except:
        traceback.print_exc(file=stdout)

        raise HTTPException(
            status_code=500,
            detail="Failed to get Ersilia Catalog details, err = [%s]"
            % repr(exc_info()),
        )


@router.get("/{model_id}/identification-details")
def get_identification_details(
    model_id: str, api_request: Request
) -> ModelIdentificationDetailsModel:
    auth_details, tracking_details = api_handler(api_request)

    # retry once
    retry_count = 0

    while retry_count <= 1:
        try:
            model_details = ModelController.instance().get_details_from_ersilia_catalog(
                model_id
            )

            if model_details is None:
                raise Exception("No Ersilia Catalog details found")

            return ModelIdentificationDetailsModel.from_object(model_details)
        except:
            traceback.print_exc(file=stdout)

        retry_count += 1

    # try once using ModelHub
    try:
        model_details = ModelController.instance().get_details_from_model_hub(model_id)

        if model_details is None:
            raise Exception("No ModelHub details found")

        return ModelIdentificationDetailsModel.from_object(model_details)
    except:
        traceback.print_exc(file=stdout)

    raise HTTPException(
        status_code=500,
        detail="Failed to get model identification details",
    )


@router.delete("/{model_id}/cache")
def delete_model_cache(model_id: str, api_request: Request):
    auth_details, tracking_details = api_handler(api_request)

    try:
        if not ModelInputCache.instance().clear_model_cached_results(model_id):
            raise Exception("execution failed")

        return {"result": "SUCCESS"}
    except:
        traceback.print_exc(file=stdout)

        raise HTTPException(
            status_code=500,
            detail="Failed to clear model cache, err = [%s]" % repr(exc_info()),
        )
