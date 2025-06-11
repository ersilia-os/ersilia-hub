from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class ModelInstanceLogRecord(DAORecord):
    modelid: str
    instanceid: str
    correlationid: str
    instance_details: str
    log_event: str
    log_timestamp: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.modelid = result["modelid"]
        self.instanceid = result["instanceid"]
        self.correlationid = result["correlationid"]
        self.instance_details = result["instancedetails"]
        self.log_event = result["logevent"]
        self.log_timestamp = (
            None
            if "logtimestamp" not in result or result["logtimestamp"] is None
            else timestamp_to_utc_timestamp(result["logtimestamp"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "modelid": self.modelid,
            "instanceid": self.instanceid,
            "correlationid": self.correlationid,
            "instance_details": self.instance_details,
            "log_event": self.log_event,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class ModelInstanceLogInsertQuery(DAOQuery):
    def __init__(
        self,
        modelid: str,
        instanceid: str,
        correlationid: str,
        instance_details: str,
        log_event: str,
    ):
        super().__init__(ModelInstanceLogRecord)

        self.modelid = modelid
        self.instanceid = instanceid
        self.correlationid = correlationid
        self.instance_details = instance_details
        self.log_event = log_event

    def to_sql(self):
        field_map = {
            "query_ModelId": self.modelid,
            "query_InstanceId": self.instanceid,
            "query_CorrelationId": self.correlationid,
            "query_InstanceDetails": self.instance_details,
            "query_LogEvent": self.log_event,
        }

        sql = """
            INSERT INTO ModelInstanceLog (
                ModelId,
                InstanceId,
                CorrelationId,
                InstanceDetails,
                LogEvent,
                LogTimestamp
            )
            VALUES (
                :query_ModelId,
                :query_InstanceId,
                :query_CorrelationId,
                :query_InstanceDetails,
                :query_LogEvent,
                CURRENT_TIMESTAMP
            )
            RETURNING
                ModelId,
                InstanceId,
                CorrelationId,
                InstanceDetails::text,
                LogEvent,
                LogTimestamp::text
        """

        return sql, field_map


# TODO: select all with filters


class ModelInstanceLogDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.INSERT_QUERY_KEY: ModelInstanceLogInsertQuery,
    }
