from enum import Enum
from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class UserPermissionRecord(DAORecord):
    userid: str
    permissions: str
    last_updated: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.userid = result["userid"]
        self.permissions = result["permissions"]
        self.last_updated = (
            None
            if "lastupdated" not in result or result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "permissions": self.permissions,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "permissions": self.permissions,
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
        }


class UserPermissionInsertQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        permissions: str,
    ):
        super().__init__(UserPermissionRecord)

        self.userid = userid
        self.permissions = permissions

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_Permissions": self.permissions,
        }

        sql = """
            INSERT INTO UserPermission (
                UserId,
                Permissions,
                LastUpdated
            )
            VALUES (
                :query_UserId,
                :query_Permissions,
                CURRENT_TIMESTAMP
            )
            RETURNING
                UserId,
                Permissions::text,
                LastUpdated::text
        """

        return sql, field_map


class UserPermissionUpdateQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        permissions: str,
    ):
        super().__init__(UserPermissionRecord)

        self.userid = userid
        self.permissions = permissions

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_Permissions": self.permissions,
        }

        sql = """
            UPDATE UserPermission 
            SET Permissions = :query_Permissions,
                LastUpdated = CURRENT_TIMESTAMP
            WHERE
                UserId = :query_UserId
            RETURNING
                UserId,
                Permissions::text,
                LastUpdated::text
        """

        return sql, field_map


class UserPermissionSelectQuery(DAOQuery):
    def __init__(self, userid: Union[str, None] = None):
        super().__init__(UserPermissionRecord)

        self.userid = userid

    def to_sql(self):
        where_clause = []
        field_map = {}

        if self.userid is not None:
            where_clause.append("UserId = :query_UserId")
            field_map["query_UserId"] = self.userid

        sql = """
            SELECT 
                UserId,
                Permissions::text,
                LastUpdated::text
            FROM UserPermission 
            %s
        """ % (
            "" if len(where_clause) == 0 else "WHERE " + " AND ".join(where_clause)
        )

        return sql, field_map


class UserPermissionDeleteQuery(DAOQuery):
    def __init__(self, userid: str):
        super().__init__(UserPermissionRecord)

        self.userid = userid

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
        }

        sql = """
            DELETE FROM UserPermission 
            WHERE UserId = :query_UserId
            RETURNING
                UserId,
                Permissions::text,
                LastUpdated::text
        """

        return sql, field_map


class UserPermissionDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_QUERY_KEY: UserPermissionSelectQuery,
        BaseDAO.INSERT_QUERY_KEY: UserPermissionInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: UserPermissionUpdateQuery,
        BaseDAO.DELETE_QUERY_KEY: UserPermissionDeleteQuery,
    }
