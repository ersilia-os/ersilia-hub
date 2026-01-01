from enum import Enum
from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord


class UserAuthQuery(Enum):
    CHECK = "CHECK"


class UserAuthRecord(DAORecord):
    userid: str
    password_hash: str

    def __init__(self, result: dict):
        super().__init__(result)

        self.userid = result["userid"]
        self.password_hash = (
            None if "passwordhash" not in result else result["passwordhash"]
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "password_hash": self.password_hash,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "password_hash": self.password_hash,
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class UserAuthCheckRecord(DAORecord):
    userid: str
    password_hash: str
    valid: bool

    def __init__(self, result: dict):
        super().__init__(result)

        self.userid = None if "userid" not in result else result["userid"]
        self.password_hash = (
            None if "passwordhash" not in result else result["passwordhash"]
        )
        self.valid = "valid" in result and result["valid"] == 1

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class UserAuthCheckQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        password_hash: str,
    ):
        super().__init__(UserAuthCheckRecord)

        self.userid = userid
        self.password_hash = password_hash

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_PasswordHash": self.password_hash,
        }

        sql = """
            SELECT PasswordHash = :query_PasswordHash as valid
            FROM UserAuth
            WHERE UserId = :query_UserId
        """

        return sql, field_map


class UserAuthInsertQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        password_hash: str,
    ):
        super().__init__(UserAuthRecord)

        self.userid = userid
        self.password_hash = password_hash

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_PasswordHash": self.password_hash,
        }

        sql = """
            INSERT INTO UserAuth (
                UserId,
                PasswordHash
            )
            VALUES (
                :query_UserId,
                :query_PasswordHash
            )
            RETURNING
                UserId
        """

        return sql, field_map


class UserAuthUpdateQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        password_hash: str,
    ):
        super().__init__(UserAuthRecord)

        self.userid = userid
        self.password_hash = password_hash

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_PasswordHash": self.password_hash,
        }

        sql = """
            UPDATE UserAuth
            SET PasswordHash = :query_PasswordHash
            WHERE UserId = :query_UserId
            RETURNING
                UserId
        """

        return sql, field_map


class UserAuthDAO(BaseDAO.DAO):
    queries = {
        UserAuthQuery.CHECK: UserAuthCheckQuery,
        BaseDAO.INSERT_QUERY_KEY: UserAuthInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: UserAuthUpdateQuery,
    }
