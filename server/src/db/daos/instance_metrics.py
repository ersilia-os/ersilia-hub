from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


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


# TODO: select all with filters


class InstanceMetricsDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.INSERT_QUERY_KEY: InstanceMetricsInsertQuery,
    }
