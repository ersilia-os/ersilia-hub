from random import choices, randint, random
from string import ascii_lowercase, ascii_uppercase, digits
from sys import exc_info, stdout
import traceback
from typing import Dict, List, Tuple, Union
from uuid import uuid4
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from library.process_lock import ProcessLock
from threading import Thread, Event
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.time import date_from_string, is_date_in_range_from_now

from python_framework.thread_safe_cache import ThreadSafeCache

from config.application_config import ApplicationConfig
from config.auth_config import AuthConfig
from db.daos.user import UserDAO, UserQuery, UserRecord
from db.daos.user_auth import (
    UserAuthCheckRecord,
    UserAuthDAO,
    UserAuthQuery,
    UserAuthRecord,
)
from db.daos.user_session import (
    UserSessionCheckRecord,
    UserSessionDAO,
    UserSessionQuery,
    UserSessionRecord,
)
from objects.user import AuthType, User, UserSession
from hashlib import md5


class AuthControllerKillInstance(KillInstance):
    def kill(self):
        AuthController.instance().kill()


class AuthController(Thread):

    CACHE_REFRESH_WAIT_TIME = 30

    _instance: "AuthController" = None

    _logger_key: str = None
    _kill_event: Event

    _process_lock: ProcessLock

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "AuthController"
        self._kill_event = Event()

        self._process_lock = ProcessLock()

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

    # NOTE: used for validation + login
    def load_user_by_name(self, username: str) -> Union[User, None]:
        ContextLogger.debug(
            self._logger_key, f"Loading user with name [{username}] from DB..."
        )
        results: List[UserRecord] = UserDAO.execute_query(
            UserQuery.SELECT_FILTERED,
            ApplicationConfig.instance().database_config,
            query_kwargs={"username": username},
        )

        if len(results) == 0:
            ContextLogger.debug(
                self._logger_key, f"No user found with name [{username}]."
            )

            return None
        else:
            ContextLogger.debug(self._logger_key, f"User found with name [{username}].")

            return User.init_from_record(results[0])

    def _generate_password_hash(self, user: User, password: str) -> str:
        user_datepart = date_from_string(user.sign_up_date).strftime("%Y-%m-%dT%H")
        digest = md5(
            f"{user.username}_{password}_{user_datepart}_{AuthConfig.instance().password_salt}".encode()
        )

        return digest.hexdigest()

    def create_user(self, user: User, password: str) -> Union[User, None]:
        ContextLogger.debug(
            self._logger_key, f"Creating user with name [{user.username}]..."
        )

        lock_acquired: bool = False

        try:
            lock_acquired = self._acquire_lock(user.username, timeout=10)
        except:
            pass

        if not lock_acquired:
            ContextLogger.warn(
                self._logger_key,
                f"Failed to acquire lock for user creation, username = [{user.username}]",
            )

            return None

        user.id = str(uuid4())

        persisted_user: User = None

        try:
            results: List[UserRecord] = UserDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **user.to_record().generate_insert_query_args(),
            )

            if len(results) == 0:
                raise Exception("No record inserted")

            persisted_user = User.init_from_record(results[0])
        except:
            error = f"Failed to create user with id = [{user.id}], name = [{user.username}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

        try:
            results: List[UserAuthRecord] = UserAuthDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **UserAuthRecord.init(
                    userid=persisted_user.id,
                    passwordhash=self._generate_password_hash(persisted_user, password),
                ).generate_insert_query_args(),
            )

            if len(results) == 0:
                raise Exception("No record inserted")
        except:
            error = f"Failed to persist user auth details for userid = [{user.id}], name = [{user.username}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)
        finally:
            self._release_lock(user.username)

        return persisted_user

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
                    "password_hash": self._generate_password_hash(user, password),
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

    def _generate_session_token(self, userid: str) -> str:
        random_token = "".join(
            choices(ascii_uppercase + digits + ascii_lowercase, k=24)
        )
        digest = md5(f"{userid}_{random_token}".encode())

        return digest.hexdigest()

    def get_random_anonymous_userid(self) -> str:
        anon_user_number = randint(0, AuthConfig.instance().total_anonymous_users)

        return "%s00000-0000-0000-0000-000000000000" % ("%03d" % anon_user_number)

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
                    sessiontoken=self._generate_session_token(userid),
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

    def load_user(self, userid: str) -> Union[None, User]:
        try:
            results: List[UserRecord] = UserDAO.execute_select(
                ApplicationConfig.instance().database_config,
                id=userid,
            )

            if results is None or len(results) == 0:
                return None

            return User.init_from_record(results[0])
        except:
            error = (
                f"Failed to load user with id [{userid}], error = [{repr(exc_info())}]"
            )
            ContextLogger.error(self._logger_key, error)

            raise Exception(error)

    def create_anonymous_session(self, session_id: str) -> Tuple[User, UserSession]:
        existing_sessions = self._load_user_sessions(session_id=session_id)

        new_session: UserSession = None
        user: User = None

        if len(existing_sessions) == 0:
            userid = self.get_random_anonymous_userid()
            new_session = self._new_user_session(
                userid,
                auth_type=AuthType.ErsiliaAnonymous,
                session_max_age_seconds=AuthConfig.instance().anonymous_session_max_age_seconds,
                session_id=session_id,
            )
        else:
            new_session = self.refresh_session(existing_sessions[0])

        user = self.load_user(new_session.userid)

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
            session.session_token = self._generate_session_token(session.userid)
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

    def _update_caches(self):
        # TODO: eventually add session cache
        pass

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
