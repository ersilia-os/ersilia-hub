import traceback
from sys import exc_info, stdout
from uuid import uuid4

import library.auth_utils as AuthUtils
from config.application_config import ApplicationConfig
from db.daos.user import UserDAO, UserQuery, UserRecord
from db.daos.user_auth import UserAuthDAO, UserAuthRecord
from library.process_lock import ProcessLock
from objects.user import User
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel

from src.db.daos.model_input_cache import ModelInputCacheDAO
from src.db.daos.shared_record import CountRecord, MapRecord
from src.db.daos.user_permission import UserPermissionDAO, UserPermissionRecord
from src.db.daos.work_request import WorkRequestDAO, WorkRequestQuery


class UserAdminController:
    _instance: "UserAdminController" = None

    _logger_key: str
    _process_lock: ProcessLock

    def __init__(self):
        self._logger_key = "UserAdminController"
        self._process_lock = ProcessLock()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

        ContextLogger.info(self._logger_key, "UserAdmin controller initialized...")

    @staticmethod
    def initialize() -> "UserAdminController":
        if UserAdminController._instance is not None:
            return UserAdminController._instance

        UserAdminController._instance = UserAdminController()

        return UserAdminController._instance

    @staticmethod
    def instance() -> "UserAdminController":
        return UserAdminController._instance

    def _release_lock(self, lock_id: str) -> None:
        self._process_lock.release_lock(lock_id)

    # NOTE: THIS IS NOT SAFE ACROSS MULTIPLE INSTANCES
    def _acquire_lock(self, lock_id: str, timeout: float = -1) -> bool:
        return self._process_lock.acquire_lock(lock_id, timeout=timeout)

    def clear_user_data(self, user_id: str) -> int:
        deleted_workrequest_ids = []

        try:
            # NOTE: we should technically NOT commit this until we have deleted the S3 data, but for now it's fine
            results: list[MapRecord] = WorkRequestDAO.execute_query(
                WorkRequestQuery.DELETE_BY_USER,
                ApplicationConfig.instance().database_config,
                query_kwargs={
                    "userid": user_id,
                },
            )

            if len(results) == 0:
                raise Exception("No records deleted")

            deleted_workrequest_ids = list(map(lambda r: r["id"], results))
        except:
            error = f"Failed to clear user data for userid = [{user_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

        # TODO: clear s3 data

        return len(deleted_workrequest_ids)

    def clear_user_contributions(self, user_id: str) -> int:
        try:
            results: list[CountRecord] = ModelInputCacheDAO.execute_delete(
                ApplicationConfig.instance().database_config,
                user_id=user_id,
            )

            if len(results) == 0:
                raise Exception("No records deleted")

            return results[0].count
        except:
            error = f"Failed to clear user contributions for userid = [{user_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

    def delete_user(self, user_id: str):
        ContextLogger.info(self._logger_key, f"Deleting user [{user_id}]...")

        try:
            ContextLogger.info(self._logger_key, f"Deleting user [{user_id}] data...")
        except:
            raise Exception(exc_info())

        try:
            ContextLogger.info(
                self._logger_key, f"Deleting user [{user_id}] contributions..."
            )
        except:
            raise Exception(exc_info())

        try:
            ContextLogger.info(
                self._logger_key, f"Deleting user [{user_id}] permissions..."
            )
            results: list[UserPermissionRecord] = UserPermissionDAO.execute_delete(
                ApplicationConfig.instance().database_config,
                userid=user_id,
            )
        except:
            error = f"Failed to delete user permissions for [{user_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            raise Exception(error)

        try:
            ContextLogger.info(
                self._logger_key, f"Deleting user [{user_id}] user record..."
            )
            results: list[UserRecord] = UserDAO.execute_delete(
                ApplicationConfig.instance().database_config,
                id=user_id,
            )

            if len(results) == 0:
                raise Exception("No user found")
        except:
            error = f"Failed to delete user record with id = [{user_id}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)

        ContextLogger.info(self._logger_key, f"Deleted user [{user_id}].")

    def create_user(self, user: User, password: str) -> User | None:
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
            results: list[UserRecord] = UserDAO.execute_insert(
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

            self._release_lock(user.username)

            raise Exception(error)

        try:
            results: list[UserAuthRecord] = UserAuthDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                userid=persisted_user.id,
                passwordhash=AuthUtils.generate_password_hash(persisted_user, password),
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

    def load_user(self, userid: str) -> None | User:
        try:
            results: list[UserRecord] = UserDAO.execute_select(
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

    # NOTE: used for validation + login
    def load_user_by_name(self, username: str) -> User | None:
        ContextLogger.debug(
            self._logger_key, f"Loading user with name [{username}] from DB..."
        )

        users: list[User] = self.load_users(username=username)

        if len(users) == 0:
            ContextLogger.debug(
                self._logger_key, f"No user found with name [{username}]."
            )

            return None
        else:
            ContextLogger.debug(self._logger_key, f"User found with name [{username}].")

            return users[0]

    def load_users(
        self,
        username: str | None = None,
        firstname_prefix: str | None = None,
        lastname_prefix: str | None = None,
        username_prefix: str | None = None,
        email_prefix: str | None = None,
    ) -> list[User]:
        results: list[UserRecord] = UserDAO.execute_query(
            UserQuery.SELECT_FILTERED,
            ApplicationConfig.instance().database_config,
            query_kwargs={
                "username": username,
                "username_prefix": username_prefix,
                "firstname_prefix": firstname_prefix,
                "lastname_prefix": lastname_prefix,
                "email_prefix": email_prefix,
            },
        )

        if len(results) == 0:
            return []
        else:
            return list(map(User.init_from_record, results))

    def update_user_password(
        self,
        user_id: str,
        new_password: str,
        current_password: str | None = None,
        force: bool = False,
    ):
        user = self.load_user(user_id)

        if user is None:
            raise Exception(f"Failed to find user with id [{user_id}]")

        if not force:
            # TODO: validate current password
            pass

        try:
            if not self._acquire_lock(user.username):
                raise Exception("Failed to acquire lock on user")

            results: list[UserAuthRecord] = UserAuthDAO.execute_update(
                ApplicationConfig.instance().database_config,
                userid=user_id,
                passwordhash=AuthUtils.generate_password_hash(user, new_password),
            )

            if len(results) == 0:
                raise Exception("No record updated")
        except:
            error = f"Failed to update user password for userid = [{user.id}], name = [{user.username}], error = [{repr(exc_info())}]"
            ContextLogger.error(self._logger_key, error)
            traceback.print_exc(file=stdout)

            raise Exception(error)
        finally:
            self._release_lock(user.username)
