from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class ModelRecord(DAORecord):
    id: str
    enabled: bool
    details: str
    last_updated: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.id = result["id"]
        self.enabled = (
            result["enabled"]
            if type(result["enabled"]) == bool
            else (
                result["enabled"] == 1
                if type(result["enabled"]) == int
                else result["enabled"].upper() == "TRUE"
            )
        )
        self.details = result["details"]
        self.last_updated = (
            None
            if result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "details": self.details,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "enabled": self.enabled,
            "details": self.details,
            "expected_last_updated": self.last_updated,
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class ModelSelectAllQuery(DAOQuery):
    def __init__(self):
        super().__init__(ModelRecord)

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                Id,
                Enabled,
                Details::text,
                LastUpdated::text
            FROM Model
            ORDER BY Id ASC
        """

        return sql, field_map


class ModelInsertQuery(DAOQuery):
    def __init__(
        self,
        id: str,
        enabled: bool,
        details: str,
    ):
        super().__init__(ModelRecord)

        self.id = id
        self.enabled = enabled
        self.details = details

    def to_sql(self):
        field_map = {
            "query_Id": self.id,
            "query_Enabled": "TRUE" if self.enabled else "FALSE",
            "query_Details": self.details,
        }

        sql = """
            INSERT INTO Model (
                Id,
                Enabled,
                Details,
                LastUpdated
            )
            VALUES (
                :query_Id,
                :query_Enabled,
                :query_Details,
                CURRENT_TIMESTAMP
            )
            RETURNING
                Id,
                Enabled,
                Details::text,
                LastUpdated::text
        """

        return sql, field_map


class ModelUpdateQuery(DAOQuery):
    def __init__(
        self,
        id: str,
        enabled: bool,
        details: str,
        expected_last_updated: str,
    ):
        super().__init__(ModelRecord)

        self.id = id
        self.enabled = enabled
        self.details = details
        self.expected_last_updated = expected_last_updated

    def to_sql(self):
        field_map = {
            "query_Id": self.id,
            "query_Enabled": "TRUE" if self.enabled else "FALSE",
            "query_Details": self.details,
            "query_ExpectedLastUpdated": self.expected_last_updated,
        }

        sql = """
            UPDATE Model 
            SET
                Enabled = :query_Enabled,
                Details = :query_Details,
                LastUpdated = CURRENT_TIMESTAMP
            WHERE Id = :query_Id
            AND LastUpdated = :query_ExpectedLastUpdated
            RETURNING
                Id,
                Enabled,
                Details::text,
                LastUpdated::text
        """

        return sql, field_map


class ModelDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: ModelSelectAllQuery,
        BaseDAO.INSERT_QUERY_KEY: ModelInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: ModelUpdateQuery,
    }
