import traceback
from sys import exc_info, stdout
from threading import Event, Thread
from typing import List, Tuple
from uuid import uuid4

import library.auth_utils as AuthUtils
from config.application_config import ApplicationConfig
from config.auth_config import AuthConfig
from controllers.user_admin import UserAdminController
from db.daos.user_auth import (
    UserAuthCheckRecord,
    UserAuthDAO,
    UserAuthQuery,
)
from db.daos.user_permission import UserPermissionDAO, UserPermissionRecord
from db.daos.user_session import (
    UserSessionCheckRecord,
    UserSessionDAO,
    UserSessionQuery,
    UserSessionRecord,
)
from library.process_lock import ProcessLock
from objects.rbac import Permission, UserPermission
from objects.user import AuthType, User, UserSession
from python_framework.config_utils import load_environment_variable
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.thread_safe_cache import ThreadSafeCache


class AuthControllerKillInstance(KillInstance):
    def kill(self):
        AuthController.instance().kill()


class AuthController(Thread):
    CACHE_REFRESH_WAIT_TIME = 30

    _instance: "AuthController" = None

    _logger_key: str = None
    _kill_event: Event

    _process_lock: ProcessLock
    _user_permissions: ThreadSafeCache[str, UserPermission]

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "AuthController"
        self._kill_event = Event()

        self._process_lock = ProcessLock()
        self._user_permissions = ThreadSafeCache()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "AuthController":
        if AuthController._instance is not None:
            return AuthController._instance

        AuthController._instance = AuthController()
        GracefulKiller.instance().register_kill_instance(AuthControllerKillInstance())

        return AuthController._instance

    @staticmethod
    def instance() -> "AuthController":
        return AuthController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _release_lock(self, lock_id: str) -> None:
        self._process_lock.release_lock(lock_id)

    # NOTE: THIS IS NOT SAFE ACROSS MULTIPLE INSTANCES
    def _acquire_lock(self, lock_id: str, timeout: float = -1) -> bool:
        return self._process_lock.acquire_lock(lock_id, timeout=timeout)

    def validate_user_password(self, user: User, password: str) -> bool:
        try:
            ContextLogger.trace(
                self._logger_key, f"Validating user password for [{user.username}]..."
            )

            results: List[UserAuthCheckRecord] = UserAuthDAO.execute_query(
                UserAuthQuery.CHECK,
                ApplicationConfig.instance().database_config,
                query_kwargs={
                    "userid": user.id,
                    "password_hash": AuthUtils.generate_password_hash(user, password),
                },
            )

            if len(results) == 0 or not results[0].valid:
                return False

            return True
        except:
            error = f"Failed to validate user password for [{user.username}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            return False

    def _new_user_session(
        self,
        userid: str,
        auth_type: AuthType,
        session_max_age_seconds: int,
        session_id: str = None,
    ) -> UserSession:
        try:
            results: List[UserSessionRecord] = UserSessionDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **UserSessionRecord.init(
                    userid=userid,
                    sessionid=str(uuid4()) if session_id is None else session_id,
                    sessiontoken=AuthUtils.generate_session_token(userid),
                    authtype=str(auth_type),
                    sessionmaxageseconds=session_max_age_seconds,
                ).generate_insert_query_args(),
            )

            if len(results) == 0:
                raise Exception("No record inserted")

            return UserSession.init_from_record(results[0])
        except:
            error = f"Failed to create user session for userid = [{userid}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

    def _load_user_sessions(
        self, userid: str = None, session_id: str = None
    ) -> List[UserSession]:
        try:
            results: List[UserSessionRecord] = UserSessionDAO.execute_select(
                ApplicationConfig.instance().database_config,
                userid=userid,
                session_id=session_id,
            )

            return list(map(UserSession.init_from_record, results))
        except:
            error = f"Failed to load user sessions for userid = [{userid}], session_id = [{session_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

    def create_anonymous_session(self, session_id: str) -> Tuple[User, UserSession]:
        existing_sessions = self._load_user_sessions(session_id=session_id)

        new_session: UserSession = None
        user: User = None

        if len(existing_sessions) == 0:
            userid = AuthUtils.get_random_anonymous_userid()
            new_session = self._new_user_session(
                userid,
                auth_type=AuthType.ErsiliaAnonymous,
                session_max_age_seconds=AuthConfig.instance().anonymous_session_max_age_seconds,
                session_id=session_id,
            )
        else:
            new_session = self.refresh_session(existing_sessions[0])

        user = UserAdminController.instance().load_user(new_session.userid)

        return user, new_session

    def create_user_session(self, userid: str, session_id: str = None) -> UserSession:
        ContextLogger.trace(
            self._logger_key,
            f"Creating session for user [{userid}], session_id = [{session_id}]...",
        )

        lock_acquired: bool = False

        try:
            lock_acquired = self._acquire_lock(userid, timeout=10)
        except:
            pass

        if not lock_acquired:
            raise Exception(
                f"Failed to acquire lock for user session creation, userid = [{userid}]",
            )

        user_session: UserSession = None

        try:
            user_session = self._new_user_session(
                userid,
                auth_type=AuthType.ErsiliaUser,
                session_max_age_seconds=AuthConfig.instance().user_session_max_age_seconds,
                session_id=session_id,
            )
        except:
            # we allow failure once, maybe a duplicate session exists
            pass

        if user_session is None:
            self.clear_user_session(userid, session_id=session_id, already_locked=True)

            try:
                return self._new_user_session(
                    userid,
                    auth_type=AuthType.ErsiliaUser,
                    session_max_age_seconds=AuthConfig.instance().user_session_max_age_seconds,
                    session_id=session_id,
                )
            except:
                error = (
                    f"Failed to create user session after 2 tries, userid = [{userid}]"
                )
                ContextLogger.error(self._logger_key, error)

                raise Exception(error)
            finally:
                self._release_lock(userid)
        else:
            self._release_lock(userid)

            return user_session

    def clear_user_session(
        self,
        userid: str,
        session_id: str = None,
        already_locked: bool = False,
        only_clear_token: bool = False,
    ) -> bool:
        ContextLogger.trace(
            self._logger_key,
            f"Clearing session for user [{userid}], session_id = [{session_id}]...",
        )

        lock_acquired: bool = False

        if not already_locked:
            try:
                lock_acquired = self._acquire_lock(userid, timeout=10)
            except:
                pass

            if not lock_acquired:
                ContextLogger.warn(
                    self._logger_key,
                    f"Failed to acquire lock for user session clearing, userid = [{userid}]",
                )
                return False

        try:
            if only_clear_token:
                results: List[UserSessionRecord] = UserSessionDAO.execute_update(
                    ApplicationConfig.instance().database_config,
                    userid=userid,
                    session_id=session_id,
                    session_token="",
                    session_max_age_seconds=0,
                )

                if len(results) == 0:
                    return False
            else:
                results: List[UserSessionRecord] = UserSessionDAO.execute_delete(
                    ApplicationConfig.instance().database_config,
                    userid=userid,
                    session_id=session_id,
                )

            return True
        except:
            ContextLogger.warn(
                self._logger_key,
                f"Failed to clear user session, userid = [{userid}], error = [{repr(exc_info())}]",
            )

            return False
        finally:
            if lock_acquired:
                self._release_lock(userid)

    def validate_session(self, session: UserSession) -> bool:
        ContextLogger.trace(
            self._logger_key,
            f"Validating session for userid = [{session.userid}], session_id = [{session.session_id}]...",
        )

        if (
            session.userid is None
            or len(session.userid) < 36
            or session.session_id is None
            or len(session.session_id) < 36
            or session.session_token is None
            or len(session.session_token) < 10
            or session.session_start_time is None
            or len(session.session_start_time) < 20  # YYYY-MM-DDTHH:mm:ssZ (at least)
        ):
            ContextLogger.warn(
                self._logger_key, f"Session data invalid for [{session.userid}]."
            )

            return False

        try:
            results: List[UserSessionCheckRecord] = UserSessionDAO.execute_query(
                UserSessionQuery.CHECK,
                ApplicationConfig.instance().database_config,
                query_kwargs={
                    "userid": session.userid,
                    "session_id": session.session_id,
                    "session_token": session.session_token,
                },
            )

            if len(results) == 0 or not results[0].valid:
                return False

            return True
        except:
            error = f"Failed to validate user session for [{session.session_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            return False

    def refresh_session(self, session: UserSession) -> UserSession:
        ContextLogger.trace(
            self._logger_key,
            f"Refreshing session for user [{session.userid}], session_id = [{session.session_id}]...",
        )

        lock_acquired: bool = False

        try:
            lock_acquired = self._acquire_lock(session.userid, timeout=10)
        except:
            pass

        if not lock_acquired:
            raise Exception(
                f"Failed to acquire lock for user session refresh, userid = [{session.userid}]",
            )

        try:
            session.session_token = AuthUtils.generate_session_token(session.userid)
            session.session_max_age_seconds = (
                AuthConfig.instance().user_session_max_age_seconds
                if session.auth_type == AuthType.ErsiliaUser
                else AuthConfig.instance().anonymous_session_max_age_seconds
            )

            results: List[UserSessionRecord] = UserSessionDAO.execute_update(
                ApplicationConfig.instance().database_config,
                **session.to_record().generate_update_query_args(),
            )

            if len(results) == 0:
                raise Exception("No record inserted")

            return UserSession.init_from_record(results[0])
        except:
            error = f"Failed to refresh user session for userid = [{session.userid}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)
        finally:
            self._release_lock(session.userid)

    def user_has_permission(self, userid: str, any_of: List[Permission]) -> bool:
        if (
            userid not in self._user_permissions
            or self._user_permissions[userid] is None
        ):
            return False

        return any(
            map(lambda p: p in self._user_permissions[userid].permissions, any_of)
        )

    def get_user_permissions(self, userid: str) -> UserPermission:
        if (
            userid not in self._user_permissions
            or self._user_permissions[userid] is None
        ):
            return None

        return self._user_permissions[userid]

    def _update_permissions_cache(self):
        ContextLogger.debug(self._logger_key, "Updating permissions cache...")

        try:
            results: List[UserPermissionRecord] = UserPermissionDAO.execute_select(
                ApplicationConfig.instance().database_config,
            )

            if results is None or len(results) == 0:
                return

            new_cache = {}

            for record in results:
                new_cache[record.userid] = UserPermission.init_from_record(record)

            self._user_permissions = ThreadSafeCache(new_cache)
        except:
            ContextLogger.error(
                self._logger_key,
                f"Failed to load UserPermissions, error = [{repr(exc_info())}]",
            )

            return

        ContextLogger.debug(self._logger_key, "Permissions cache updated.")

    def _update_caches(self):
        self._update_permissions_cache()

    def upsert_user_permissions(self, userid: str, permissions: list[Permission]):
        ContextLogger.debug(
            self._logger_key, "Updating user permissions for [%s]..." % userid
        )

        try:
            results: List[UserPermissionRecord] = UserPermissionDAO.execute_upsert(
                ApplicationConfig.instance().database_config,
                userid=userid,
                permissions=list(map(str, permissions)),
            )

            if results is None or len(results) == 0:
                return

            self._user_permissions[userid] = UserPermission.init_from_record(results[0])
        except:
            error = f"Failed to upsert UserPermissions for userid = [{userid}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)

            raise Exception(error)

        ContextLogger.debug(self._logger_key, "User Permissions updated.")

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        while True:
            try:
                self._update_caches()
            except:
                error_str = "Failed to update caches, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

            if self._wait_or_kill(AuthController.CACHE_REFRESH_WAIT_TIME):
                break

        ContextLogger.info(self._logger_key, "Controller stopped")
