from csv import Error
from enum import Enum
from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class UserQuery(Enum):
    SELECT_FILTERED = "SELECT_FILTERED"


class UserRecord(DAORecord):
    id: str
    username: str
    first_name: str
    last_name: str
    email: Union[str, None]
    sign_up_date: Union[str, None]
    last_updated: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.id = result["id"]
        self.username = result["username"]
        self.first_name = result["firstname"]
        self.last_name = result["lastname"]
        self.email = result["email"]
        self.sign_up_date = (
            None
            if result["signupdate"] is None
            else timestamp_to_utc_timestamp(result["signupdate"])
        )
        self.last_updated = (
            None
            if result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "username": self.username,
        }


class UserSelectAllQuery(DAOQuery):
    def __init__(self):
        super().__init__(UserRecord)

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate::text,
                LastUpdated::text
            FROM ErsiliaUser
            ORDER BY Username ASC
        """

        return sql, field_map


class UserSelectFilteredQuery(DAOQuery):
    def __init__(
        self,
        username: str = None,
        username_prefix: str = None,
        firstname_prefix: str = None,
        lastname_prefix: str = None,
        email_prefix: str = None,
    ):
        super().__init__(UserRecord)

        self.username = username
        self.username_prefix = username_prefix
        self.firstname_prefix = firstname_prefix
        self.lastname_prefix = lastname_prefix
        self.email_prefix = email_prefix

    def to_sql(self):
        field_map = {}
        custom_filters = []

        if self.username is not None:
            custom_filters.append("Username = :query_Username")
            field_map["query_Username"] = self.username

        if self.username_prefix is not None:
            custom_filters.append(f"Username LIKE '{self.username_prefix}%'")

        if self.firstname_prefix is not None:
            custom_filters.append(f"FirstName LIKE '{self.firstname_prefix}%'")

        if self.lastname_prefix is not None:
            custom_filters.append(f"LastName LIKE '{self.lastname_prefix}%'")

        if self.email_prefix is not None:
            custom_filters.append(f"Email LIKE '{self.email_prefix}%'")

        sql = """
            SELECT
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate::text,
                LastUpdated::text
            FROM ErsiliaUser
            %s 
            ORDER BY Username ASC
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
        )

        return sql, field_map


class UserSelectQuery(DAOQuery):
    def __init__(self, id: str):
        super().__init__(UserRecord)

        self.id = id

    def to_sql(self):
        field_map = {"query_Id": self.id}

        sql = """
            SELECT
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate::text,
                LastUpdated::text
            FROM ErsiliaUser
            WHERE Id = :query_Id
        """

        return sql, field_map


class UserInsertQuery(DAOQuery):
    def __init__(
        self,
        id: str,
        username: str,
        first_name: str,
        last_name: str,
        email: Union[str, None],
    ):
        super().__init__(UserRecord)

        self.id = id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def to_sql(self):
        field_map = {
            "query_Id": self.id,
            "query_Username": self.username,
            "query_FirstName": self.first_name,
            "query_LastName": self.last_name,
            "query_Email": self.email,
        }

        sql = """
            INSERT INTO ErsiliaUser (
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate,
                LastUpdated
            )
            VALUES (
                :query_Id,
                :query_Username,
                :query_FirstName,
                :query_LastName,
                :query_Email,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            RETURNING
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate::text,
                LastUpdated::text
        """

        return sql, field_map


class UserDeleteQuery(DAOQuery):
    def __init__(
        self,
        id: str = None,
        username: str = None,
    ):
        super().__init__(UserRecord)

        self.id = id
        self.username = username

    def to_sql(self):
        delete_filter = ""

        if self.id is not None and len(self.id) > 0:
            delete_filter = f"Id = '{self.id}'"
        elif self.username is not None and len(self.username) > 0:
            delete_filter = f"Username = '{self.username}'"
        else:
            raise Error("missing 'id' or 'username' field")

        sql = (
            """
            DELETE FROM ErsiliaUser
            WHERE %s
            RETURNING
                Id,
                Username,
                FirstName,
                LastName,
                Email,
                SignUpDate::text,
                LastUpdated::text
        """
            % delete_filter
        )

        return sql, {}


class UserDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: UserSelectAllQuery,
        BaseDAO.SELECT_QUERY_KEY: UserSelectQuery,
        BaseDAO.INSERT_QUERY_KEY: UserInsertQuery,
        BaseDAO.DELETE_QUERY_KEY: UserDeleteQuery,
        UserQuery.SELECT_FILTERED: UserSelectFilteredQuery,
    }
