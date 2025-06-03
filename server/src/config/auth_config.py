from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel


USER_SESSION_MAX_AGE_SECONDS_DEFAULT = "300"  # 5 minutes
ANONYMOUS_SESSION_MAX_AGE_SECONDS_DEFAULT = "172800"  # 48 hours
TOTAL_ANONYMOUS_USERS_DEFAULT = "100"


class AuthConfig:

    __instance: "AuthConfig" = None

    password_salt: str
    user_session_max_age_seconds: int
    anonymous_session_max_age_seconds: int
    total_anonymous_users: int

    def __init__(
        self,
        password_salt: str,
        user_session_max_age_seconds: int,
        anonymous_session_max_age_seconds: int,
        total_anonymous_users: int,
    ) -> None:
        self.password_salt = password_salt
        self.user_session_max_age_seconds = user_session_max_age_seconds
        self.anonymous_session_max_age_seconds = anonymous_session_max_age_seconds
        self.total_anonymous_users = total_anonymous_users

    @staticmethod
    def instance() -> "AuthConfig":
        if AuthConfig.__instance is None:
            AuthConfig.initialize()

        return AuthConfig.__instance

    @staticmethod
    def initialize() -> "AuthConfig":
        if AuthConfig.__instance is not None:
            return AuthConfig.__instance

        ContextLogger.sys_log(LogLevel.INFO, "[AuthConfig] initializing...")

        AuthConfig.__instance = AuthConfig(
            load_environment_variable("PASSWORD_SALT", error_on_none=True),
            int(
                load_environment_variable(
                    "USER_SESSION_MAX_AGE_SECONDS",
                    default=USER_SESSION_MAX_AGE_SECONDS_DEFAULT,
                )
            ),
            int(
                load_environment_variable(
                    "ANONYMOUS_SESSION_MAX_AGE_SECONDS",
                    default=ANONYMOUS_SESSION_MAX_AGE_SECONDS_DEFAULT,
                )
            ),
            int(
                load_environment_variable(
                    "TOTAL_ANONYMOUS_USERS",
                    default=TOTAL_ANONYMOUS_USERS_DEFAULT,
                )
            ),
        )

        ContextLogger.sys_log(LogLevel.INFO, "[AuthConfig] initialized.")
