from re import compile
from typing import List, Tuple
from fastapi import Request, HTTPException

from objects.api import AuthDetails, TrackingDetails

from controllers.auth import AuthController
from objects.rbac import Permission

SESSION_ID_REGEX = compile("[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}")


def api_handler(
    request: Request,
    requires_auth: bool = True,
    skip_validation: bool = False,
    required_permissions: List[Permission] = None,
) -> Tuple[AuthDetails, TrackingDetails]:
    auth_details, tracking_details = api_extract_request_details(request)

    if not skip_validation:
        api_validate_auth(auth_details, requires_auth)

    if (
        requires_auth
        and required_permissions is not None
        and len(required_permissions) > 0
    ):
        if not AuthController.instance().user_has_permission(
            auth_details.user_session.userid, required_permissions
        ):
            raise HTTPException(403, detail="Unauthorised")

    return auth_details, tracking_details


def api_extract_request_details(
    request: Request,
) -> Tuple[AuthDetails, TrackingDetails]:
    return (
        AuthDetails.from_request(request),
        TrackingDetails.from_request(request),
    )


def api_validate_auth(auth_details: AuthDetails, requires_auth: bool = True):
    if not requires_auth:
        return

    if auth_details is None or auth_details.user_session is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    if not AuthController.instance().validate_session(auth_details.user_session):
        raise HTTPException(
            status_code=401,
            detail="Unauthenticated",
        )


def validate_session_id(session_id: str):
    if (
        session_id is None
        or len(session_id) < 36
        or SESSION_ID_REGEX.fullmatch(session_id) is None
    ):
        raise HTTPException(status_code=400, detail="Invalid session id")
