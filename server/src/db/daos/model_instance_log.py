from typing import Dict, List, Union

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


class ModelInstanceLogSelectFilteredQuery(DAOQuery):
    def __init__(
        self,
        model_ids: List[str] = None,
        instance_ids: List[str] = None,
        correlation_ids: List[str] = None,
        log_events: List[str] = None,
        limit: int = 100,
        log_date_from: str = None,
        log_date_to: str = None,
    ):
        super().__init__(ModelInstanceLogRecord)

        self.model_ids = model_ids
        self.instance_ids = instance_ids
        self.correlation_ids = correlation_ids
        self.log_events = log_events
        self.limit = limit
        self.log_date_from = log_date_from
        self.log_date_to = log_date_to

    def to_sql(self):
        field_map = {}
        custom_filters = []

        if self.model_ids is not None and len(self.model_ids) > 0:
            custom_filters.append(
                "ModelId IN (%s)" % ",".join(map(lambda x: "'%s'" % x, self.model_ids))
            )

        if self.instance_ids is not None and len(self.instance_ids) > 0:
            custom_filters.append(
                "InstanceId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.instance_ids))
            )

        if self.correlation_ids is not None and len(self.correlation_ids) > 0:
            custom_filters.append(
                "CorrelationId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.correlation_ids))
            )

        if self.log_events is not None and len(self.log_events) > 0:
            custom_filters.append(
                "LogEvent IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.log_events))
            )

        if self.log_date_from is not None and self.log_date_to is not None:
            custom_filters.append(
                "LogTimestamp BETWEEN :query_LogDateFrom AND :query_LogDateTo"
            )
            field_map["query_LogDateFrom"] = self.log_date_from
            field_map["query_LogDateTo"] = self.log_date_to
        elif self.log_date_from is not None:
            custom_filters.append("LogTimestamp >= :query_LogDateFrom")
            field_map["query_LogDateFrom"] = self.log_date_from
        elif self.log_date_to is not None:
            custom_filters.append("LogTimestamp <= :query_LogDateTo")
            field_map["query_LogDateTo"] = self.log_date_to

        sql = """
            SELECT
                ModelId,
                InstanceId,
                CorrelationId,
                InstanceDetails::text,
                LogEvent,
                LogTimestamp::text
            FROM ModelInstanceLog
            %s
            ORDER BY LogTimestamp DESC, InstanceId ASC
            LIMIT %d
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
            self.limit,
        )

        return sql, field_map


class ModelInstanceLogDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.INSERT_QUERY_KEY: ModelInstanceLogInsertQuery,
        BaseDAO.SELECT_ALL_QUERY_KEY: ModelInstanceLogSelectFilteredQuery,
    }
