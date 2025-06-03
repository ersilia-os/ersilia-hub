from sys import exc_info

from fastapi import APIRouter, HTTPException, Request

from library.fastapi_root import FastAPIRoot

from library.api_utils import api_handler, validate_session_id
from controllers.auth import AuthController
from objects.user import User, UserModel, UserSession, UserSignUpModel
from python_framework.logger import ContextLogger, LogLevel

from objects.api import AuthType, EncodedAuthModel, LoginResponseModel


###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/auth", tags=["auth"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.post("/signup")
def signup(
    user_signup: UserSignUpModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=False)

    has_existing_user = False

    try:
        existing_user = AuthController.instance().load_user_by_name(
            user_signup.user.username
        )
        has_existing_user = existing_user is not None
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR, f"Failed to load user, error = [{repr(exc_info())}]"
        )
        raise HTTPException(500, detail="Failed to validate username")

    if has_existing_user is not None:
        raise HTTPException(400, detail="Username already in use")

    new_user: User = None

    try:
        new_user = AuthController.instance().create_user(
            user_signup.user.to_object(), user_signup.password
        )
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR, f"Failed to create user, error = [{repr(exc_info())}]"
        )

    if new_user is None:
        raise HTTPException(500, detail="Failed to create user")

    return UserModel.from_object(new_user)


@router.post("/anonymous-login/{session_id}")
def anon_login(
    session_id: str,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=False)

    validate_session_id(session_id)

    user: User = None
    user_session: UserSession = None

    try:
        user, user_session = AuthController.instance().create_anonymous_session(
            session_id
        )
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to create user session for session_id [{session_id}], error = [{repr(exc_info())}]",
        )
        raise HTTPException(500, detail="Failed to start anonymous session")

    if user_session is None or user is None:
        raise HTTPException(500, detail="Failed to start anonymous session")

    return LoginResponseModel(
        session=user_session.to_model(), user=UserModel.from_object(user)
    )


@router.post("/login")
def login(
    encoded_auth: EncodedAuthModel,
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request, requires_auth=False)
    username: str = None
    password: str = None

    has_error = False

    try:
        username, password = encoded_auth.decode_auth_encoding()
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to validate encoded auth, error = [{repr(exc_info())}]",
        )
        has_error = True

    if (
        has_error
        or username is None
        or len(username) == 0
        or password is None
        or len(password) < 5
    ):
        raise HTTPException(400, detail="Invalid username or password")

    existing_user: User = None

    try:
        existing_user = AuthController.instance().load_user_by_name(username)
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR, f"Failed to load user, error = [{repr(exc_info())}]"
        )
        raise HTTPException(400, detail="Invalid username or password")

    if existing_user is None:
        raise HTTPException(400, detail="Invalid username or password")

    password_valid = False

    try:
        password_valid = AuthController.instance().validate_user_password(
            existing_user, password
        )
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to validate user password for [{username}], error = [{repr(exc_info())}]",
        )
        raise HTTPException(400, detail="Invalid username or password")

    if not password_valid:
        raise HTTPException(400, detail="Invalid username or password")

    user_session: UserSession = None

    try:
        user_session = AuthController.instance().create_user_session(existing_user.id)
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to create user session for [{username}], error = [{repr(exc_info())}]",
        )
        raise HTTPException(500, detail="Failed to login")

    if user_session is None:
        raise HTTPException(500, detail="Failed to login")

    return LoginResponseModel(
        session=user_session.to_model(), user=UserModel.from_object(existing_user)
    )


@router.post("/logout")
def logout(
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    if (
        auth_details is None
        or auth_details.user_session.userid is None
        or auth_details.user_session.session_id is None
    ):
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to logout since there is no session details",
        )
        raise HTTPException(400, detail="Failed to logout")

    try:
        if AuthController.instance().clear_user_session(
            auth_details.user_session.userid,
            auth_details.user_session.session_id,
            only_clear_token=auth_details.auth_type == AuthType.ErsiliaAnonymous,
        ):
            return {"status": "ok"}
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to clear user session for userid = [{auth_details.user_session.userid}], session_id = [{auth_details.user_session.session_id}], error = [{repr(exc_info())}]",
        )

    raise HTTPException(500, detail="Failed to logout")


@router.post("/session/refresh")
def refresh_session(
    api_request: Request,
):
    auth_details, tracking_details = api_handler(api_request)

    updated_session: UserSession = None

    try:
        updated_session = AuthController.instance().refresh_session(
            auth_details.user_session
        )
    except:
        ContextLogger.sys_log(
            LogLevel.ERROR,
            f"Failed to update user session for userid = [{auth_details.user_session.userid}], session_id = [{auth_details.user_session.session_id}], error = [{repr(exc_info())}]",
        )

    if updated_session is None:
        raise HTTPException(500, detail="Failed to refresh session")

    return updated_session.to_model()
