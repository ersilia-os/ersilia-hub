from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class ModelInputCacheRecord(DAORecord):
    model_id: str
    input_hash: str
    input: str | None
    result: str
    user_id: str | None
    last_updated: str

    def __init__(self, result: dict):
        super().__init__(result)

        self.model_id = result["modelid"]
        self.input_hash = result["inputhash"]
        self.input = None if "input" not in result else result["input"]
        self.result = result["result"]
        self.user_id = None if "userid" not in result else result["userid"]
        self.last_updated = (
            None
            if result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "model_id": self.model_id,
            "input_hash": self.input_hash,
            "input": self.input,
            "result": self.result,
            "user_id": self.user_id,
            "last_updated": self.last_updated,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()

class ModelInputCacheSelectBatchQuery(DAOQuery):

    model_id: str
    input_hashes: list[str]
    result_only: bool

    def __init__(self, model_id: str, input_hashes: list[str], result_only: bool = False):
        super().__init__(ModelInputCacheRecord)

        self.model_id = model_id
        self.input_hashes = input_hashes
        self.result_only = result_only

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                ModelId,
                InputHash,
                Result
                %s
            FROM ModelInputCache
            WHERE ModelId = :query_ModelId
            AND InputHash IN (%s)
        """ % (
                "" if self.result_only else ", Input, UserId, LastUpdated",
                ",".join(list(map(lambda input_hash: f"'{input_hash}'", self.input_hashes)))
            )

        return sql, field_map


class ModelInputCacheInsertQuery(DAOQuery):
    def __init__(
        self,
        model_id: str,
        input_hash: str,
        input: str,
        result: str,
        user_id: str,
    ):
        super().__init__(ModelInputCacheRecord)

        self.model_id = model_id
        self.input_hash = input_hash
        self.input = input
        self.result = result
        self.user_id = user_id

    def to_sql(self):
        field_map = {
            "query_ModelId": self.model_id,
            "query_InputHash": self.input_hash,
            "query_Input": self.input,
            "query_Result": self.result,
            "query_UserId": self.user_id,
        }

        sql = """
            INSERT INTO WorkRequest (
                ModelId,
                InputHash,
                Input,
                Result,
                UserId,
                LastUpdated
            )
            VALUES (
                :query_ModelId,
                :query_InputHash,
                :query_Input,
                :query_Result,
                :query_UserId,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT
            DO NOTHING -- simply ignore conflicts, cache value SHOULD always be the same
            RETURNING
                ModelId,
                InputHash,
                Input,
                Result,
                UserId,
                LastUpdated::text
        """

        return sql, field_map

class ModelInputCacheDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: ModelInputCacheSelectBatchQuery,
        BaseDAO.INSERT_QUERY_KEY: ModelInputCacheInsertQuery,
    }
