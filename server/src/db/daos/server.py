from enum import Enum
from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp

class ServerQuery(Enum):
    SELECT_UNHEALTHY = "SELECT_UNHEALTHY"

class ServerRecord(DAORecord):
    server_id: str
    is_healthy: bool
    startup_time: str
    last_check_in: str

    def __init__(self, result: dict):
        super().__init__(result)

        self.server_id = result["serverid"]
        self.is_healthy = (
            result["ishealthy"]
            if type(result["ishealthy"]) == bool
            else (
                result["ishealthy"] == 1
                if type(result["ishealthy"]) == int
                else result["ishealthy"].upper() == "TRUE"
            )
        )
        self.startup_time = (
            None
            if "startuptime" not in result or result["startuptime"] is None
            else timestamp_to_utc_timestamp(result["startuptime"])
        )
        self.last_check_in = (
            None
            if result["lastcheckin"] is None
            else timestamp_to_utc_timestamp(result["lastcheckin"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "server_id": self.server_id,
            "is_healthy": self.is_healthy,
            "startup_time": self.startup_time,
            "last_check_in": self.last_check_in,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "server_id": self.server_id,
            "is_healthy": self.is_healthy,
            "last_check_in": self.last_check_in
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "server_id": self.server_id
        }


class ServerSelectAllQuery(DAOQuery):
    def __init__(self):
        super().__init__(ServerRecord)

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                ServerId,
                IsHealthy,
                StartupTime::text,
                LastCheckIn::text
            FROM Server
            ORDER BY StartupTime ASC
        """

        return sql, field_map

class ServerSelectUnhealthyQuery(DAOQuery):
    def __init__(self):
        super().__init__(ServerRecord)

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                ServerId,
                IsHealthy,
                StartupTime::text,
                LastCheckIn::text
            FROM Server
            WHERE IsHealthy != 1
            AND LastCheckIn < CURRENT_TIMESTAMP - INTERVAL '5 MIN'
            ORDER BY StartupTime ASC
        """

        return sql, field_map

class ServerInsertQuery(DAOQuery):
    def __init__(
        self,
        server_id: str,
        is_healthy: bool,
        startup_time: str,
        last_check_in: str
    ):
        super().__init__(ServerRecord)

        self.server_id = server_id
        self.is_healthy = is_healthy
        self.startup_time = startup_time
        self.last_check_in = last_check_in

    def to_sql(self):
        field_map = {
            "query_ServerId": self.server_id,
            "query_IsHealthy": 1 if self.is_healthy else 0,
            "query_StartupTime": self.startup_time,
            "query_LastCheckIn": self.last_check_in,
        }

        sql = """
            INSERT INTO Server (
                ServerId,
                IsHealthy,
                StartupTime,
                LastCheckIn
            )
            VALUES (
                :query_ServerId,
                :query_IsHealthy,
                :query_StartupTime,
                :query_LastCheckIn
            )
            RETURNING
                ServerId,
                IsHealthy,
                StartupTime::text,
                LastCheckIn::text
        """

        return sql, field_map


class ServerUpdateQuery(DAOQuery):
    def __init__(
        self,
        server_id: str,
        is_healthy: bool,
        last_check_in: str
    ):
        super().__init__(ServerRecord)

        self.server_id = server_id
        self.is_healthy = is_healthy
        self.last_check_in = last_check_in

    def to_sql(self):
        field_map = {
            "query_ServerId": self.server_id,
            "query_IsHealthy": 1 if self.is_healthy else 0,
            "query_LastCheckIn": self.last_check_in,
        }

        sql = """
            UPDATE Server 
            SET
                IsHealthy = :query_IsHealthy,
                LastCheckIn = :query_LastCheckIn,
            WHERE ServerId = :query_ServerId
            RETURNING
                ServerId,
                IsHealthy,
                StartupTime::text,
                LastCheckIn::text
        """

        return sql, field_map

class ServerDeleteQuery(DAOQuery):
    def __init__(
        self,
        server_id: str,
    ):
        super().__init__(ServerRecord)

        self.server_id = server_id

    def to_sql(self):
        field_map = {
            "query_ServerId": self.server_id,
        }

        sql = """
            DELETE FROM Server
            WHERE ServerId = :query_ServerId
            RETURNING
                ServerId,
                IsHealthy,
                StartupTime::text,
                LastCheckIn::text
        """

        return sql, field_map

class ServerDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: ServerSelectAllQuery,
        BaseDAO.INSERT_QUERY_KEY: ServerInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: ServerUpdateQuery,
        BaseDAO.DELETE_QUERY_KEY: ServerDeleteQuery,
        ServerQuery.SELECT_UNHEALTHY: ServerSelectUnhealthyQuery,
    }
