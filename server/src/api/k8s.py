from fastapi import APIRouter, Request

from controllers.k8s import K8sController
from library.fastapi_root import FastAPIRoot
from library.api_utils import api_handler

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/k8s", tags=["k8s"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("/instances")
def load_instances(
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    return {
        "items": list(
            map(lambda x: x.to_object(), K8sController.instance().load_model_pods())
        )
    }


@router.get("/{model_id}/instances")
def load_instances_by_model(
    model_id: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    return {
        "items": list(
            map(
                lambda x: x.to_object(),
                K8sController.instance().load_model_pods(model_id),
            )
        )
    }
