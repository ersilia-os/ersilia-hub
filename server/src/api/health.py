from fastapi import APIRouter
from library.fastapi_root import FastAPIRoot

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(tags=["health"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################

#
# TODO: add DB, AWS and k8s checks to below
#


@router.get("/healthz")
def healthz():
    return {"status": "ok"}


@router.get("/readyz")
def healthz():
    return {"status": "ok"}


@router.get("/livez")
def healthz():
    return {"status": "ok"}
