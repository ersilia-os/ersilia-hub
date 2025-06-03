from enum import Enum
from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class UserSessionQuery(Enum):
    CHECK = "CHECK"


class UserSessionRecord(DAORecord):
    userid: str
    session_id: str
    session_token: str
    auth_type: str
    session_max_age_seconds: int
    session_start_time: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.userid = result["userid"]
        self.session_id = result["sessionid"]
        self.session_token = result["sessiontoken"]
        self.auth_type = result["authtype"]
        self.session_max_age_seconds = result["sessionmaxageseconds"]
        self.session_start_time = (
            None
            if "sessionstarttime" not in result or result["sessionstarttime"] is None
            else timestamp_to_utc_timestamp(result["sessionstarttime"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "session_id": self.session_id,
            "session_token": self.session_token,
            "auth_type": self.auth_type,
            "session_max_age_seconds": self.session_max_age_seconds,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "session_id": self.session_id,
            "session_token": self.session_token,
            "session_max_age_seconds": self.session_max_age_seconds,
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "userid": self.userid,
            "session_id": self.session_id,
        }


class UserSessionCheckRecord(DAORecord):

    userid: str
    session_id: str
    session_token: str
    valid: bool

    def __init__(self, result: dict):
        super().__init__(result)

        self.userid = None if "userid" not in result else result["userid"]
        self.session_id = None if "sessionid" not in result else result["sessionid"]
        self.session_token = (
            None if "sessiontoken" not in result else result["sessiontoken"]
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


class UserSessionCheckQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        session_id: str,
        session_token: str,
    ):
        super().__init__(UserSessionCheckRecord)

        self.userid = userid
        self.session_id = session_id
        self.session_token = session_token

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_SessionId": self.session_id,
            "query_SessionToken": self.session_token,
        }

        sql = """
            SELECT (
                SessionToken = :query_SessionToken
                AND SessionStartTime + (INTERVAL '1 SECONDS' * SessionMaxAgeSeconds) > CURRENT_TIMESTAMP
            ) as valid
            FROM UserSession
            WHERE UserId = :query_UserId
            AND SessionId = :query_SessionId
        """

        return sql, field_map


class UserSessionInsertQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        session_id: str,
        session_token: str,
        auth_type: str,
        session_max_age_seconds: int,
    ):
        super().__init__(UserSessionRecord)

        self.userid = userid
        self.session_id = session_id
        self.session_token = session_token
        self.auth_type = auth_type
        self.session_max_age_seconds = session_max_age_seconds

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_SessionId": self.session_id,
            "query_SessionToken": self.session_token,
            "query_AuthType": self.auth_type,
            "query_SessionMaxAgeSeconds": self.session_max_age_seconds,
        }

        sql = """
            INSERT INTO UserSession (
                UserId,
                SessionId,
                SessionToken,
                AuthType,
                SessionMaxAgeSeconds,
                SessionStartTime
            )
            VALUES (
                :query_UserId,
                :query_SessionId,
                :query_SessionToken,
                :query_AuthType,
                :query_SessionMaxAgeSeconds,
                CURRENT_TIMESTAMP
            )
            RETURNING
                UserId,
                SessionId,
                SessionToken,
                AuthType,
                SessionMaxAgeSeconds,
                SessionStartTime::text
        """

        return sql, field_map


class UserSessionUpdateQuery(DAOQuery):
    def __init__(
        self,
        userid: str,
        session_id: str,
        session_token: str,
        session_max_age_seconds: int,
    ):
        super().__init__(UserSessionRecord)

        self.userid = userid
        self.session_id = session_id
        self.session_token = session_token
        self.session_max_age_seconds = session_max_age_seconds

    def to_sql(self):
        field_map = {
            "query_UserId": self.userid,
            "query_SessionId": self.session_id,
            "query_SessionToken": self.session_token,
            "query_SessionMaxAgeSeconds": self.session_max_age_seconds,
        }

        sql = """
            UPDATE UserSession 
            SET SessionToken = :query_SessionToken,
                SessionMaxAgeSeconds = :query_SessionMaxAgeSeconds,
                SessionStartTime = CURRENT_TIMESTAMP
            WHERE
                UserId = :query_UserId
                AND SessionId = :query_SessionId
            RETURNING
                UserId,
                SessionId,
                SessionToken,
                AuthType,
                SessionMaxAgeSeconds,
                SessionStartTime::text
        """

        return sql, field_map


class UserSessionSelectQuery(DAOQuery):
    def __init__(
        self, userid: Union[str, None] = None, session_id: Union[str, None] = None
    ):
        super().__init__(UserSessionRecord)

        self.userid = userid
        self.session_id = session_id

    def to_sql(self):
        where_clause = []
        field_map = {}

        if self.userid is not None:
            where_clause.append("UserId = :query_UserId")
            field_map["query_UserId"] = self.userid

        if self.session_id is not None:
            where_clause.append("SessionId = :query_SessionId")
            field_map["query_SessionId"] = self.session_id

        sql = """
            SELECT 
                UserId,
                SessionId,
                SessionToken,
                AuthType,
                SessionMaxAgeSeconds,
                SessionStartTime::text
            FROM UserSession 
            %s
        """ % (
            "" if len(where_clause) == 0 else "WHERE " + " AND ".join(where_clause)
        )

        return sql, field_map


class UserSessionDeleteQuery(DAOQuery):
    def __init__(self, userid: str, session_id: Union[str, None] = None):
        super().__init__(UserSessionRecord)

        self.userid = userid
        self.session_id = session_id

    def to_sql(self):
        where_clause = ["UserId = :query_UserId"]
        field_map = {
            "query_UserId": self.userid,
        }

        if self.session_id is not None:
            where_clause.append("SessionId = :query_SessionId")
            field_map["query_SessionId"] = self.session_id

        sql = """
            DELETE FROM UserSession 
            WHERE %s
            RETURNING
                UserId,
                SessionId,
                SessionToken,
                AuthType,
                SessionMaxAgeSeconds,
                SessionStartTime::text
        """ % " AND ".join(
            where_clause
        )

        return sql, field_map


class UserSessionDAO(BaseDAO.DAO):
    queries = {
        UserSessionQuery.CHECK: UserSessionCheckQuery,
        BaseDAO.SELECT_QUERY_KEY: UserSessionSelectQuery,
        BaseDAO.INSERT_QUERY_KEY: UserSessionInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: UserSessionUpdateQuery,
        BaseDAO.DELETE_QUERY_KEY: UserSessionDeleteQuery,
    }
