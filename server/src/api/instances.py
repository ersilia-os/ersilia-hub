from fastapi import APIRouter, HTTPException, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler
from objects.rbac import Permission
from controllers.model_instance_handler import ModelInstanceController
from objects.instance import ModelInstanceModel

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


@router.get("active")
def load_active_instances(
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, required_permissions=[Permission.ADMIN]
    )

    return {
        "items": list(
            map(
                ModelInstanceModel.from_object,
                ModelInstanceController.instance().load_active_instances(),
            )
        )
    }
