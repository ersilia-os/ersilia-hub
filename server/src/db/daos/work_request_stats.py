from enum import Enum
from typing import Dict, List, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class WorkRequestStatsQuery(Enum):
    FILTERED_STATS = "FILTERED_STATS"


class WorkRequestStatsRecord(DAORecord):
    model_id: str
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
        self.total_count = result["total_count"]
        self.success_count = result["success_count"]
        self.fail_count = result["fail_count"]
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
    ):
        super().__init__(WorkRequestStatsRecord)

        self.model_ids = model_ids
        self.user_id = user_id
        self.session_id = session_id
        self.request_date_from = request_date_from
        self.request_date_to = request_date_to
        self.request_statuses = request_statuses

    def to_sql(self):
        field_map = {}
        custom_filters = []

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

        sql = """
            WITH FilteredRequests AS (
                SELECT
                    ModelId,
                    RequestDate,
                    RequestStatus,
                    PodReadyTimestamp,
                    JobSubmissionTimestamp,
                    ProcessedTimestamp,
                    EXTRACT(EPOCH FROM (ProcessedTimestamp - RequestDate)) AS request_time,
                    EXTRACT(EPOCH FROM (JobSubmissionTimestamp - RequestDate)) AS request_start_time,
                    EXTRACT(EPOCH FROM (ProcessedTimestamp - JobSubmissionTimestamp)) AS job_execution_time
                FROM WorkRequest
                %s
            ),

            TotalStats AS (
                SELECT
                    ModelId as model_id,
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
                GROUP BY ModelId
            ),

            SuccessStats AS (
                SELECT
                    ModelId as model_id,
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
                GROUP BY ModelId
            ),

            FailedStats AS (
                SELECT
                    ModelId as model_id,
                    count(*) AS fail_count,
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
                GROUP BY ModelId
            )

            SELECT
                TotalStats.*,
                SuccessStats.*,
                FailedStats.*
            FROM TotalStats
            LEFT JOIN SuccessStats
                ON TotalStats.model_id = SuccessStats.model_id
            LEFT JOIN FailedStats
                ON TotalStats.model_id = FailedStats.model_id
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
        )

        return sql, field_map


class WorkRequestStatsDAO(BaseDAO.DAO):
    queries = {
        WorkRequestStatsQuery.FILTERED_STATS: WorkRequestFilteredStatsQuery,
    }
