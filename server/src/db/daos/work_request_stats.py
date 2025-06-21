from enum import Enum
from typing import Dict, List, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class WorkRequestStatsQuery(Enum):
    FILTERED_STATS = "FILTERED_STATS"


class WorkRequestStatsRecord(DAORecord):
    model_id: str
    input_size: int
    total_count: int
    success_count: int
    fail_count: int

    ###

    total_all_request_start_time: float
    max_all_request_start_time: float
    min_all_request_start_time: float
    avg_all_request_start_time: float

    total_all_request_time: float
    max_all_request_time: float
    min_all_request_time: float
    avg_all_request_time: float

    total_all_job_execution_time: float
    max_all_job_execution_time: float
    min_all_job_execution_time: float
    avg_all_job_execution_time: float

    ###

    total_success_request_start_time: float
    max_success_request_start_time: float
    min_success_request_start_time: float
    avg_success_request_start_time: float

    total_success_request_time: float
    max_success_request_time: float
    min_success_request_time: float
    avg_success_request_time: float

    total_success_job_execution_time: float
    max_success_job_execution_time: float
    min_success_job_execution_time: float
    avg_success_job_execution_time: float

    ###

    total_fail_request_start_time: float
    max_fail_request_start_time: float
    min_fail_request_start_time: float
    avg_fail_request_start_time: float

    total_fail_request_time: float
    max_fail_request_time: float
    min_fail_request_time: float
    avg_fail_request_time: float

    total_fail_job_execution_time: float
    max_fail_job_execution_time: float
    min_fail_job_execution_time: float
    avg_fail_job_execution_time: float

    def __init__(self, result: dict):
        super().__init__(result)

        self.model_id = result["model_id"]
        self.input_size = result["input_size"]
        self.total_count = result["total_count"]
        self.success_count = result["success_count"]
        self.failed_count = result["failed_count"]
        self.active_count = result["active_count"]

        key: str = None

        for key, value in result:
            if (
                key.endswith("request_start_time")
                or key.endswith("request_time")
                or key.endswith("job_execution_time")
            ):
                self.__setattr__(key, value)

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class WorkRequestFilteredStatsQuery(DAOQuery):

    def __init__(
        self,
        model_ids: List[str] | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        request_date_from: str | None = None,
        request_date_to: str | None = None,
        request_statuses: List[str] | None = None,
        input_size_ge: int | None = None,
        input_size_le: int | None = None,
        group_by: List[str] = None,
    ):
        super().__init__(WorkRequestStatsRecord)

        self.model_ids = model_ids
        self.user_id = user_id
        self.session_id = session_id
        self.request_date_from = request_date_from
        self.request_date_to = request_date_to
        self.request_statuses = request_statuses
        self.input_size_ge = input_size_ge
        self.input_size_le = input_size_le
        self.group_by = group_by

    def to_sql(self):
        field_map = {}
        custom_filters = []
        custom_group_by = ["ModelId"]
        success_join = ["TotalStats.model_id = SuccessStats.s_model_id"]
        failed_join = ["TotalStats.model_id = FailedStats.f_model_id"]

        if self.model_ids is not None:
            custom_filters.append(
                "ModelId IN (%s)" % ",".join(map(lambda x: "'%s'" % x, self.model_ids))
            )

        if self.user_id is not None:
            custom_filters.append("UserId = :query_UserId")
            field_map["query_UserId"] = self.user_id

        if self.session_id is not None:
            custom_filters.append(
                'Metadata @> \'{"sessionId": "%s"}\'' % self.session_id
            )

        if self.request_date_from is not None and self.request_date_to is not None:
            custom_filters.append(
                "RequestDate BETWEEN :query_RequestDateFrom AND :query_RequestDateTo"
            )
            field_map["query_RequestDateFrom"] = self.request_date_from
            field_map["query_RequestDateTo"] = self.request_date_to
        elif self.request_date_from is not None:
            custom_filters.append("RequestDate >= :query_RequestDateFrom")
            field_map["query_RequestDateFrom"] = self.request_date_from
        elif self.request_date_to is not None:
            custom_filters.append("RequestDate <= :query_RequestDateTo")
            field_map["query_RequestDateTo"] = self.request_date_to

        if self.request_statuses is not None and len(self.request_statuses) > 0:
            custom_filters.append(
                "RequestStatus IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.request_statuses))
            )

        if self.input_size_ge is not None and self.input_size_ge > 0:
            custom_filters.append("InputSize >= :query_InputSizeGE")
            field_map["query_InputSizeGE"] = self.input_size_ge
        elif self.input_size_le is not None and self.input_size_le > 0:
            custom_filters.append("InputSize <= :query_InputSizeLE")
            field_map["query_InputSizeLE"] = self.input_size_le

        if self.group_by is not None and len(self.group_by) > 0:
            for entry in self.group_by:
                if entry == "InputSize":
                    custom_group_by.append(entry)
                    success_join.append(
                        "TotalStats.input_size = SuccessStats.s_input_size"
                    )
                    failed_join.append(
                        "TotalStats.input_size = FailedStats.f_input_size"
                    )

        sql = """
            WITH FilteredRequests AS (
                SELECT
                    ModelId,
                    InputSize,
                    RequestDate,
                    RequestStatus,
                    PodReadyTimestamp,
                    JobSubmissionTimestamp,
                    ProcessedTimestamp,
                    EXTRACT(EPOCH FROM (ProcessedTimestamp - RequestDate)) AS request_time,
                    EXTRACT(EPOCH FROM (JobSubmissionTimestamp - RequestDate)) AS request_start_time,
                    EXTRACT(EPOCH FROM (ProcessedTimestamp - JobSubmissionTimestamp)) AS job_execution_time
                FROM WorkRequest
                %(custom_filters)s
            ),

            TotalStats AS (
                SELECT
                    ModelId as model_id,
                    InputSize as input_size,
                    count(*) AS total_count,
                    sum(request_time) as total_all_request_time,
                    max(request_time) as max_all_request_time,
                    min(request_time) as min_all_request_time,
                    avg(request_time) as avg_all_request_time,
                    sum(request_start_time) as total_all_request_start_time,
                    max(request_start_time) as max_all_request_start_time,
                    min(request_start_time) as min_all_request_start_time,
                    avg(request_start_time) as avg_all_request_start_time,
                    sum(job_execution_time) as total_all_job_execution_time,
                    max(job_execution_time) as max_all_job_execution_time,
                    min(job_execution_time) as min_all_job_execution_time,
                    avg(job_execution_time) as avg_all_job_execution_time
                FROM FilteredRequests
                GROUP BY %(custom_group_by)s
            ),

            SuccessStats AS (
                SELECT
                    ModelId as s_model_id,
                    InputSize as s_input_size,
                    count(*) AS success_count,
                    sum(request_time) as total_success_request_time,
                    max(request_time) as max_success_request_time,
                    min(request_time) as min_success_request_time,
                    avg(request_time) as avg_success_request_time,
                    sum(request_start_time) as total_success_request_start_time,
                    max(request_start_time) as max_success_request_start_time,
                    min(request_start_time) as min_success_request_start_time,
                    avg(request_start_time) as avg_success_request_start_time,
                    sum(job_execution_time) as total_success_job_execution_time,
                    max(job_execution_time) as max_success_job_execution_time,
                    min(job_execution_time) as min_success_job_execution_time,
                    avg(job_execution_time) as avg_success_job_execution_time
                FROM FilteredRequests
                WHERE RequestStatus = 'COMPLETED'
                GROUP BY %(custom_group_by)s
            ),

            FailedStats AS (
                SELECT
                    ModelId as f_model_id,
                    InputSize as f_input_size,
                    count(*) AS failed_count,
                    sum(request_time) as total_fail_request_time,
                    max(request_time) as max_fail_request_time,
                    min(request_time) as min_fail_request_time,
                    avg(request_time) as avg_fail_request_time,
                    sum(request_start_time) as total_fail_request_start_time,
                    max(request_start_time) as max_fail_request_start_time,
                    min(request_start_time) as min_fail_request_start_time,
                    avg(request_start_time) as avg_fail_request_start_time,
                    sum(job_execution_time) as total_fail_job_execution_time,
                    max(job_execution_time) as max_fail_job_execution_time,
                    min(job_execution_time) as min_fail_job_execution_time,
                    avg(job_execution_time) as avg_fail_job_execution_time
                FROM FilteredRequests
                WHERE RequestStatus = 'FAILED'
                GROUP BY %(custom_group_by)s
            )

            SELECT
                TotalStats.*,
                SuccessStats.*,
                FailedStats.*
            FROM TotalStats
            LEFT JOIN SuccessStats
                ON %(success_join)s
            LEFT JOIN FailedStats
                ON %(failed_join)s
        """ % {
            "custom_filters": (
                ""
                if len(custom_filters) == 0
                else "WHERE " + " AND ".join(custom_filters)
            ),
            "custom_group_by": ", ".join(custom_group_by),
            "success_join": " AND ".join(success_join),
            "failed_join": " AND ".join(failed_join),
        }

        return sql, field_map


class WorkRequestStatsDAO(BaseDAO.DAO):
    queries = {
        WorkRequestStatsQuery.FILTERED_STATS: WorkRequestFilteredStatsQuery,
    }
