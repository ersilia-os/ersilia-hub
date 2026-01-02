from sys import exc_info
from typing import Annotated

from controllers.auth import AuthController
from controllers.user_admin import UserAdminController
from fastapi import APIRouter, HTTPException, Query, Request
from library.api_utils import api_handler
from library.fastapi_root import FastAPIRoot
from objects.rbac import Permission
from objects.user import (
    User,
    UserModel,
    UserPasswordUpdateModel,
    UserPermissionsUpdateModel,
    UsersFilterModel,
)
from python_framework.logger import ContextLogger, LogLevel

###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/users", tags=["user-admin"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.get("/")
def load_filtered(
    filters: Annotated[UsersFilterModel, Query()],
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, requires_auth=True, required_permissions=[Permission.ADMIN]
    )

    try:
        users = UserAdminController.instance().load_users(
            filters.username,
            filters.firstname_prefix,
            filters.lastname_prefix,
            filters.username_prefix,
            filters.email_prefix,
        )
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to load filtered users, error = [{repr(exc_info())}]",
        )
        raise HTTPException(500, detail="Failed to load users")

    return {"items": list(map(UserModel.from_object, users))}


@router.get("/{userid}")
def load(
    userid: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=True)
    user: User | None = None

    try:
        user = UserAdminController.instance().load_user(userid)
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR, f"Failed to load user, error = [{repr(exc_info())}]"
        )
        raise HTTPException(500, detail="Failed to load user")

    if user is None:
        raise HTTPException(400, detail="User not found")

    return UserModel.from_object(user)


@router.put("/{userid}/password")
def update_password(
    userid: str,
    update: UserPasswordUpdateModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=True)

    if update.force:
        if not AuthController.instance().user_has_permission(
            auth_details.user_session.userid, [Permission.ADMIN]
        ):
            raise HTTPException(403, detail="Unauthorised")
    else:
        if userid != auth_details.user_session.userid:
            raise HTTPException(403, detail="Unauthorised")

    try:
        UserAdminController.instance().update_user_password(
            userid,
            update.new_password,
            current_password=update.current_password,
            force=update.force,
        )
    except:
        raise HTTPException(500, detail="Failed to update user password")

    return {"result": "SUCCESS"}


@router.put("/{userid}/permissions")
def update_permissions(
    userid: str,
    update: UserPermissionsUpdateModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(
        api_request, requires_auth=True, required_permissions=[Permission.ADMIN]
    )

    try:
        AuthController.instance().upsert_user_permissions(
            userid,
            update.permissions,
        )
    except:
        raise HTTPException(500, detail="Failed to update user password")

    return {"result": "SUCCESS"}


@router.delete("/{userid}/contributions")
def delete_user_contributions(
    userid: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=True)

    if (
        userid != auth_details.user_session.userid
        and not AuthController.instance().user_has_permission(
            auth_details.user_session.userid, [Permission.ADMIN]
        )
    ):
        raise HTTPException(403, detail="Unauthorised")

    try:
        UserAdminController.instance().clear_user_contributions(userid)
    except:
        raise HTTPException(500, detail="Failed to clear user contributions")

    return {"result": "SUCCESS"}


@router.delete("/{userid}/data")
def delete_user_data(
    userid: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=True)

    if (
        userid != auth_details.user_session.userid
        and not AuthController.instance().user_has_permission(
            auth_details.user_session.userid, [Permission.ADMIN]
        )
    ):
        raise HTTPException(403, detail="Unauthorised")

    try:
        UserAdminController.instance().clear_user_data(userid)
    except:
        raise HTTPException(500, detail="Failed to clear user data")

    return {"result": "SUCCESS"}


@router.delete("/{userid}")
def delete_user(
    userid: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=True)

    if (
        userid != auth_details.user_session.userid
        and not AuthController.instance().user_has_permission(
            auth_details.user_session.userid, [Permission.ADMIN]
        )
    ):
        raise HTTPException(403, detail="Unauthorised")

    try:
        UserAdminController.instance().delete_user(userid)
    except:
        raise HTTPException(500, detail="Failed to delete user")

    return {"result": "SUCCESS"}
