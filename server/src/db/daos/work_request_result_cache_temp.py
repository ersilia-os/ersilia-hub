from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord


class WorkRequestResultCacheTempRecord(DAORecord):
    work_request_id: int
    input_hash: str
    input: str
    result: str

    def __init__(self, result: dict):
        super().__init__(result)

        self.work_request_id = result["workrequestid"]
        self.input_hash = result["inputhash"]
        self.input = result["input"]
        self.result = result["result"]

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "work_request_id": self.work_request_id,
            "input_hash": self.input_hash,
            "input": self.input,
            "result": self.result,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "work_request_id": self.work_request_id,
        }


class WorkRequestResultCacheTempSelectBatchQuery(DAOQuery):
    work_request_id: int
    batch_size: int
    batch_offset: int

    def __init__(
        self, work_request_id: int, batch_size: int = 250, batch_offset: int = 0
    ):
        super().__init__(WorkRequestResultCacheTempRecord)

        self.work_request_id = work_request_id
        self.batch_size = batch_size
        self.batch_offset = batch_offset

    def to_sql(self):
        field_map = {
            "query_WorkRequestId": self.work_request_id,
        }

        sql = """
            SELECT
                WorkRequestId,
                InputHash,
                Input,
                Result
            FROM WorkRequestResultCacheTemp
            WHERE WorkRequestId = :query_WorkRequestId
            LIMIT %d
            OFFSET %d
        """ % (self.batch_size, self.batch_offset)

        return sql, field_map


class WorkRequestResultCacheTempInsertQuery(DAOQuery):
    def __init__(
        self,
        work_request_id: int,
        input_hash: str,
        input: str,
        result: str,
    ):
        super().__init__(WorkRequestResultCacheTempRecord)

        self.work_request_id = work_request_id
        self.input_hash = input_hash
        self.input = input
        self.result = result

    def to_sql(self):
        field_map = {
            "query_WorkRequestId": self.work_request_id,
            "query_InputHash": self.input_hash,
            "query_Input": self.input,
            "query_Result": self.result,
        }

        sql = """
            INSERT INTO WorkRequestResultCacheTemp (
                WorkRequestId,
                InputHash,
                Input,
                Result
            )
            VALUES (
                :query_WorkRequestId,
                :query_InputHash,
                :query_Input,
                :query_Result
            )
            ON CONFLICT
            DO NOTHING -- simply ignore conflicts, cache value SHOULD always be the same
            RETURNING
                WorkRequestId,
                InputHash,
                Input,
                Result
        """

        return sql, field_map


class WorkRequestResultCacheTempDeleteQuery(DAOQuery):
    def __init__(
        self,
        work_request_id: int,
    ):
        super().__init__(WorkRequestResultCacheTempRecord)

        self.work_request_id = work_request_id

    def to_sql(self):
        field_map = {
            "query_WorkRequestId": self.work_request_id,
        }

        sql = """
            DELETE FROM WorkRequestResultCacheTemp
            WHERE WorkRequestId = :query_WorkRequestId,
            RETURNING
                WorkRequestId,
                InputHash
        """

        return sql, field_map


class WorkRequestResultCacheTempDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: WorkRequestResultCacheTempSelectBatchQuery,
        BaseDAO.INSERT_QUERY_KEY: WorkRequestResultCacheTempInsertQuery,
        BaseDAO.DELETE_QUERY_KEY: WorkRequestResultCacheTempDeleteQuery,
    }
