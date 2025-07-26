from enum import Enum
from typing import Dict, List, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class InstanceMetricsQuery(Enum):
    SELECT_FILTERED = "SELECT_FILTERED"


class InstanceMetricsRecord(DAORecord):
    modelid: str
    instanceid: str
    namespace: str
    cpu_running_averages: str
    memory_running_averages: str
    timestamp: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.modelid = result["modelid"]
        self.instanceid = result["instanceid"]
        self.namespace = result["namespace"]
        self.cpu_running_averages = result["cpurunningaverages"]
        self.memory_running_averages = result["memoryrunningaverages"]
        self.timestamp = (
            None
            if "tmstamp" not in result or result["tmstamp"] is None
            else timestamp_to_utc_timestamp(result["tmstamp"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "modelid": self.modelid,
            "instanceid": self.instanceid,
            "namespace": self.namespace,
            "cpu_running_averages": self.cpu_running_averages,
            "memory_running_averages": self.memory_running_averages,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class InstanceMetricsInsertQuery(DAOQuery):
    def __init__(
        self,
        modelid: str,
        instanceid: str,
        namespace: str,
        cpu_running_averages: str,
        memory_running_averages: str,
    ):
        super().__init__(InstanceMetricsRecord)

        self.modelid = modelid
        self.instanceid = instanceid
        self.namespace = namespace
        self.cpu_running_averages = cpu_running_averages
        self.memory_running_averages = memory_running_averages

    def to_sql(self):
        field_map = {
            "query_ModelId": self.modelid,
            "query_InstanceId": self.instanceid,
            "query_Namespace": self.namespace,
            "query_CpuRunningAverages": self.cpu_running_averages,
            "query_MemoryRunningAverages": self.memory_running_averages,
        }

        sql = """
            INSERT INTO InstanceMetrics (
                ModelId,
                InstanceId,
                Namespace,
                CpuRunningAverages,
                MemoryRunningAverages,
                TMstamp
            )
            VALUES (
                :query_ModelId,
                :query_InstanceId,
                :query_Namespace,
                :query_CpuRunningAverages,
                :query_MemoryRunningAverages,
                CURRENT_TIMESTAMP
            )
            RETURNING
                ModelId,
                InstanceId,
                Namespace,
                CpuRunningAverages::text,
                MemoryRunningAverages::text,
                TMstamp::text
        """

        return sql, field_map


class InstanceMetricsSelectFilteredQuery(DAOQuery):
    def __init__(
        self,
        model_ids: List[str] = None,
        instance_ids: List[str] = None,
        limit: int = 100,
        date_from: str = None,
        date_to: str = None,
    ):
        super().__init__(InstanceMetricsRecord)

        self.model_ids = model_ids
        self.instance_ids = instance_ids
        self.limit = limit
        self.date_from = date_from
        self.date_to = date_to

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

        if self.date_from is not None and self.date_to is not None:
            custom_filters.append("TMstamp BETWEEN :query_DateFrom AND :query_DateTo")
            field_map["query_DateFrom"] = self.date_from
            field_map["query_DateTo"] = self.date_to
        elif self.date_from is not None:
            custom_filters.append("TMstamp >= :query_DateFrom")
            field_map["query_DateFrom"] = self.date_from
        elif self.date_to is not None:
            custom_filters.append("TMstamp <= :query_DateTo")
            field_map["query_DateTo"] = self.date_to

        sql = """
            SELECT
                ModelId,
                InstanceId,
                Namespace,
                CpuRunningAverages::text,
                MemoryRunningAverages::text,
                TMstamp::text
            FROM InstanceMetrics
            %s
            ORDER BY TMStamp DESC, InstanceId ASC
            LIMIT %d
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
            self.limit,
        )

        print("sql:", sql)
        print("field_map:", field_map)

        return sql, field_map


class InstanceMetricsDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.INSERT_QUERY_KEY: InstanceMetricsInsertQuery,
        InstanceMetricsQuery.SELECT_FILTERED: InstanceMetricsSelectFilteredQuery,
    }
