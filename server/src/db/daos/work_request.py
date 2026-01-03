from enum import Enum
from typing import Dict, List, Union

import python_framework.db.dao.dao as BaseDAO
from db.daos.shared_record import MapRecord
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class WorkRequestQuery(Enum):
    SELECT_FILTERED = "SELECT_FILTERED"
    DELETE_BY_USER = "DELETE_BY_USER"


class WorkRequestRecord(DAORecord):
    id: int
    model_id: str
    user_id: str
    request_payload: str | None
    request_date: str
    metadata: str
    request_status: str
    request_status_reason: str
    model_job_id: str
    last_updated: Union[str, None]
    pod_ready_timestamp: Union[str, None]
    job_submission_timestamp: Union[str, None]
    processed_timestamp: Union[str, None]
    input_size: int | None
    server_id: str | None

    def __init__(self, result: dict):
        super().__init__(result)

        self.id = result["id"]
        self.model_id = result["modelid"]
        self.user_id = result["userid"]
        self.request_payload = (
            None if "requestpayload" not in result else result["requestpayload"]
        )
        self.request_date = result["requestdate"]
        self.metadata = result["metadata"]
        self.request_status = result["requeststatus"]
        self.request_status_reason = result["requeststatusreason"]
        self.model_job_id = None if "modeljobid" not in result else result["modeljobid"]
        self.last_updated = (
            None
            if result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )
        self.pod_ready_timestamp = (
            None
            if result["podreadytimestamp"] is None
            else timestamp_to_utc_timestamp(result["podreadytimestamp"])
        )
        self.job_submission_timestamp = (
            None
            if result["jobsubmissiontimestamp"] is None
            else timestamp_to_utc_timestamp(result["jobsubmissiontimestamp"])
        )
        self.processed_timestamp = (
            None
            if result["processedtimestamp"] is None
            else timestamp_to_utc_timestamp(result["processedtimestamp"])
        )
        self.input_size = result["inputsize"]
        self.server_id = result["serverid"]

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "model_id": self.model_id,
            "user_id": self.user_id,
            "request_payload": self.request_payload,
            "request_date": self.request_date,
            "metadata": self.metadata,
            "request_status": self.request_status,
            "request_status_reason": self.request_status_reason,
            "pod_ready_timestamp": self.pod_ready_timestamp,
            "job_submission_timestamp": self.job_submission_timestamp,
            "processed_timestamp": self.processed_timestamp,
            "input_size": self.input_size,
            "server_id": self.server_id,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "request_status": self.request_status,
            "request_status_reason": self.request_status_reason,
            "model_job_id": self.model_job_id,
            "expected_last_updated": self.last_updated,
            "pod_ready_timestamp": self.pod_ready_timestamp,
            "job_submission_timestamp": self.job_submission_timestamp,
            "processed_timestamp": self.processed_timestamp,
            "server_id": self.server_id,
        }

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class WorkRequestSelectAllQuery(DAOQuery):
    def __init__(self):
        super().__init__(WorkRequestRecord)

    def to_sql(self):
        field_map = {}

        sql = """
            SELECT
                WorkRequest.Id,
                WorkRequest.ModelId,
                WorkRequest.UserId,
                WorkRequestData.RequestPayload::text,
                WorkRequest.RequestDate::text,
                WorkRequest.Metadata::text,
                WorkRequest.RequestStatus,
                WorkRequest.RequestStatusReason,
                WorkRequest.ModelJobId,
                WorkRequest.LastUpdated::text,
                WorkRequest.PodReadyTimestamp::text,
                WorkRequest.JobSubmissionTimestamp::text,
                WorkRequest.ProcessedTimestamp::text,
                WorkRequest.InputSize,
                WorkRequest.ServerId
            FROM WorkRequest
            LEFT JOIN WorkRequestData
                ON WorkRequest.Id = WorkRequestData.RequestId
            ORDER BY WorkRequest.RequestDate DESC, WorkRequest.ModelId ASC
            LIMIT 300
        """

        return sql, field_map


class WorkRequestSelectFilteredQuery(DAOQuery):
    def __init__(
        self,
        id: str = None,
        model_ids: List[str] = None,
        user_id: str = None,
        request_date_from: str = None,
        request_date_to: str = None,
        request_statuses: List[str] = None,
        session_id: str = None,
        server_ids: List[str] = None,
        limit: int = 200,
    ):
        super().__init__(WorkRequestRecord)

        self.id = id
        self.model_ids = model_ids
        self.user_id = user_id
        self.request_date_from = request_date_from
        self.request_date_to = request_date_to
        self.request_statuses = request_statuses
        self.session_id = session_id
        self.server_ids = server_ids
        self.limit = limit

    def to_sql(self):
        field_map = {}
        custom_filters = []

        if self.id is not None:
            custom_filters.append("Id = :query_Id")
            field_map["query_Id"] = self.id

        if self.model_ids is not None and len(self.model_ids) > 0:
            custom_filters.append(
                "WorkRequest.ModelId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.model_ids))
            )

        if self.user_id is not None:
            custom_filters.append("WorkRequest.UserId = :query_UserId")
            field_map["query_UserId"] = self.user_id

        if self.request_date_from is not None and self.request_date_to is not None:
            custom_filters.append(
                "WorkRequest.RequestDate BETWEEN :query_RequestDateFrom AND :query_RequestDateTo"
            )
            field_map["query_RequestDateFrom"] = self.request_date_from
            field_map["query_RequestDateTo"] = self.request_date_to
        elif self.request_date_from is not None:
            custom_filters.append("WorkRequest.RequestDate >= :query_RequestDateFrom")
            field_map["query_RequestDateFrom"] = self.request_date_from
        elif self.request_date_to is not None:
            custom_filters.append("WorkRequest.RequestDate <= :query_RequestDateTo")
            field_map["query_RequestDateTo"] = self.request_date_to

        if self.request_statuses is not None and len(self.request_statuses) > 0:
            custom_filters.append(
                "WorkRequest.RequestStatus IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.request_statuses))
            )

        if self.session_id is not None:
            custom_filters.append(
                'WorkRequest.Metadata @> \'{"sessionId": "%s"}\'' % self.session_id
            )

        if self.server_ids is not None:
            has_null_server = any(map(lambda s: s == "NULL", self.server_ids))
            other_server_ids = list(
                map(
                    lambda sm: f"'{sm}'", filter(lambda s: s != "NULL", self.server_ids)
                )
            )

            if has_null_server:
                custom_filters.append(
                    "(WorkRequest.ServerId IS NULL OR WorkRequest.ServerId IN (%s))"
                    % ",".join(other_server_ids)
                )
            else:
                custom_filters.append(
                    "WorkRequest.ServerId IN (%s)" % ",".join(other_server_ids)
                )

        sql = """
            SELECT
                WorkRequest.Id,
                WorkRequest.ModelId,
                WorkRequest.UserId,
                WorkRequestData.RequestPayload::text,
                WorkRequest.RequestDate::text,
                WorkRequest.Metadata::text,
                WorkRequest.RequestStatus,
                WorkRequest.RequestStatusReason,
                WorkRequest.ModelJobId,
                WorkRequest.LastUpdated::text,
                WorkRequest.PodReadyTimestamp::text,
                WorkRequest.JobSubmissionTimestamp::text,
                WorkRequest.ProcessedTimestamp::text,
                WorkRequest.InputSize,
                WorkRequest.ServerId
            FROM WorkRequest
            LEFT JOIN WorkRequestData
                ON WorkRequest.Id = WorkRequestData.RequestId
            %s
            ORDER BY WorkRequest.RequestDate DESC, WorkRequest.ModelId ASC
            LIMIT %d
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
            self.limit,
        )

        return sql, field_map


class WorkRequestInsertQuery(DAOQuery):
    def __init__(
        self,
        model_id: str,
        user_id: str,
        request_payload: str,
        request_date: str,
        metadata: str,
        request_status: str,
        request_status_reason: str,
        pod_ready_timestamp: str,
        job_submission_timestamp: str,
        processed_timestamp: str,
        input_size: int,
        server_id: str,
    ):
        super().__init__(WorkRequestRecord)

        self.model_id = model_id
        self.user_id = user_id
        self.request_payload = request_payload
        self.request_date = request_date
        self.metadata = metadata
        self.request_status = request_status
        self.request_status_reason = request_status_reason
        self.pod_ready_timestamp = pod_ready_timestamp
        self.job_submission_timestamp = job_submission_timestamp
        self.processed_timestamp = processed_timestamp
        self.input_size = input_size
        self.server_id = server_id

    def to_sql(self):
        field_map = {
            "query_ModelId": self.model_id,
            "query_UserId": self.user_id,
            "query_RequestPayload": self.request_payload,
            "query_RequestDate": self.request_date,
            "query_Metadata": self.metadata,
            "query_RequestStatus": self.request_status,
            "query_RequestStatusReason": self.request_status_reason,
            "query_PodReadyTimestamp": self.pod_ready_timestamp,
            "query_JobSubmissionTimestamp": self.job_submission_timestamp,
            "query_ProcessedTimestamp": self.processed_timestamp,
            "query_InputSize": self.input_size,
            "query_ServerId": self.server_id,
        }

        sql = """
            WITH WorkRequestInsert AS (
                INSERT INTO WorkRequest (
                    ModelId,
                    UserId,
                    RequestDate,
                    Metadata,
                    RequestStatus,
                    RequestStatusReason,
                    LastUpdated,
                    PodReadyTimestamp,
                    JobSubmissionTimestamp,
                    ProcessedTimestamp,
                    InputSize,
                    ServerId
                )
                VALUES (
                    :query_ModelId,
                    :query_UserId,
                    :query_RequestDate,
                    :query_Metadata,
                    :query_RequestStatus,
                    :query_RequestStatusReason,
                    CURRENT_TIMESTAMP,
                    :query_PodReadyTimestamp,
                    :query_JobSubmissionTimestamp,
                    :query_ProcessedTimestamp,
                    :query_InputSize,
                    :query_ServerId
                )
                RETURNING
                    Id,
                    ModelId,
                    UserId,
                    RequestDate,
                    Metadata::text,
                    RequestStatus,
                    RequestStatusReason,
                    ModelJobId,
                    LastUpdated::text,
                    PodReadyTimestamp::text,
                    JobSubmissionTimestamp::text,
                    ProcessedTimestamp::text,
                    InputSize,
                    ServerId
            ),

            WorkRequestDataInsert AS (
                INSERT INTO WorkRequestData (
                    RequestId,
                    RequestPayload,
                    RequestDate
                )
                SELECT
                    Id,
                    :query_RequestPayload,
                    RequestDate
                FROM WorkRequestInsert
                RETURNING
                    RequestId,
                    RequestPayload::text,
                    RequestDate::text
            )

            SELECT 
                WorkRequestInsert.Id,
                WorkRequestInsert.ModelId,
                WorkRequestInsert.UserId,
                WorkRequestDataInsert.RequestPayload::text,
                WorkRequestInsert.RequestDate::text,
                WorkRequestInsert.Metadata::text,
                WorkRequestInsert.RequestStatus,
                WorkRequestInsert.RequestStatusReason,
                WorkRequestInsert.ModelJobId,
                WorkRequestInsert.LastUpdated::text,
                WorkRequestInsert.PodReadyTimestamp::text,
                WorkRequestInsert.JobSubmissionTimestamp::text,
                WorkRequestInsert.ProcessedTimestamp::text,
                WorkRequestInsert.InputSize,
                WorkRequestInsert.ServerId
            FROM WorkRequestInsert
            INNER JOIN WorkRequestDataInsert
                ON WorkRequestInsert.Id = WorkRequestDataInsert.RequestId
        """

        return sql, field_map


class WorkRequestUpdateQuery(DAOQuery):
    def __init__(
        self,
        id: str,
        request_status: str,
        request_status_reason: str,
        model_job_id: str,
        expected_last_updated: str,
        pod_ready_timestamp: str,
        job_submission_timestamp: str,
        processed_timestamp: str,
        server_id: str,
        expected_server_id: str | None = None,
    ):
        super().__init__(WorkRequestRecord)

        self.id = id
        self.request_status = request_status
        self.request_status_reason = request_status_reason
        self.model_job_id = model_job_id
        self.expected_last_updated = expected_last_updated
        self.pod_ready_timestamp = pod_ready_timestamp
        self.job_submission_timestamp = job_submission_timestamp
        self.processed_timestamp = processed_timestamp
        self.server_id = server_id
        self.expected_server_id = expected_server_id

    def to_sql(self):
        field_map = {
            "query_Id": self.id,
            "query_RequestStatus": self.request_status,
            "query_RequestStatusReason": self.request_status_reason,
            "query_ModelJobId": self.model_job_id,
            "query_ExpectedLastUpdated": self.expected_last_updated,
            "query_PodReadyTimestamp": self.pod_ready_timestamp,
            "query_JobSubmissionTimestamp": self.job_submission_timestamp,
            "query_ProcessedTimestamp": self.processed_timestamp,
            "query_ServerId": self.server_id,
        }

        custom_filters = []

        if self.expected_server_id is not None:
            if self.expected_server_id == "NULL":
                custom_filters.append("ServerId IS NULL")
            else:
                custom_filters.append(f"ServerId = '{self.expected_server_id}'")

        sql = """
            WITH WorkRequestUpdate AS (
                UPDATE WorkRequest 
                SET
                    RequestStatus = :query_RequestStatus,
                    RequestStatusReason = :query_RequestStatusReason,
                    ModelJobId = :query_ModelJobId,
                    LastUpdated = CURRENT_TIMESTAMP,
                    PodReadyTimestamp = :query_PodReadyTimestamp,
                    JobSubmissionTimestamp = :query_JobSubmissionTimestamp,
                    ProcessedTimestamp = :query_ProcessedTimestamp,
                    ServerId = :query_ServerId
                WHERE Id = :query_Id
                AND LastUpdated = :query_ExpectedLastUpdated
                %s
                RETURNING
                    Id,
                    ModelId,
                    UserId,
                    RequestDate::text,
                    Metadata::text,
                    RequestStatus,
                    RequestStatusReason,
                    ModelJobId,
                    LastUpdated::text,
                    PodReadyTimestamp::text,
                    JobSubmissionTimestamp::text,
                    ProcessedTimestamp::text,
                    InputSize,
                    ServerId
            )

            SELECT 
                WorkRequestUpdate.Id,
                WorkRequestUpdate.ModelId,
                WorkRequestUpdate.UserId,
                WorkRequestData.RequestPayload::text,
                WorkRequestUpdate.RequestDate::text,
                WorkRequestUpdate.Metadata::text,
                WorkRequestUpdate.RequestStatus,
                WorkRequestUpdate.RequestStatusReason,
                WorkRequestUpdate.ModelJobId,
                WorkRequestUpdate.LastUpdated::text,
                WorkRequestUpdate.PodReadyTimestamp::text,
                WorkRequestUpdate.JobSubmissionTimestamp::text,
                WorkRequestUpdate.ProcessedTimestamp::text,
                WorkRequestUpdate.InputSize,
                WorkRequestUpdate.ServerId
            FROM WorkRequestUpdate
            LEFT JOIN WorkRequestData
                ON WorkRequestUpdate.Id = WorkRequestData.RequestId
        """ % (
            "" if len(custom_filters) == 0 else "AND " + " AND ".join(custom_filters)
        )

        return sql, field_map


class WorkRequestDeleteByUserQuery(DAOQuery):
    def __init__(
        self,
        user_id: str,
    ):
        super().__init__(MapRecord)

        self.user_id = user_id

    def to_sql(self):
        field_map = {
            "query_UserId": self.user_id,
        }

        sql = """
            WITH WorkRequestsToDelete AS (
                SELECT Id, UserId
                FROM WorkRequest
                WHERE UserId = :query_UserId
            ),

            DeletedWRData AS (
                DELETE FROM WorkRequestData
                WHERE RequestId IN (
                    SELECT Id FROM WorkRequestsToDelete
                )
                RETURNING RequestId
            ),

            DeletedWRCache AS (
                DELETE FROM WorkRequestResultCacheTemp
                WHERE WorkRequestId IN (
                    SELECT Id FROM WorkRequestsToDelete
                )
                RETURNING WorkRequestId
            ),

            DeletedModelInstance AS (
                DELETE FROM ModelInstance
                WHERE WorkRequestId IN (
                    SELECT Id FROM WorkRequestsToDelete
                )
                RETURNING WorkRequestId
            ),

            DeletedWR AS (
                DELETE FROM WorkRequest
                WHERE Id IN (
                    SELECT Id FROM WorkRequestsToDelete
                )
                RETURNING Id
            )

            SELECT WorkRequestsToDelete.Id as id
            FROM WorkRequestsToDelete
            LEFT JOIN DeletedWRData 
                ON WorkRequestsToDelete.Id = DeletedWRData.RequestId
            LEFT JOIN DeletedWRCache
                ON WorkRequestsToDelete.Id = DeletedWRCache.WorkRequestId
            LEFT JOIN DeletedModelInstance
                ON WorkRequestsToDelete.Id = DeletedModelInstance.WorkRequestId
            LEFT JOIN DeletedWR
                ON WorkRequestsToDelete.Id = DeletedWR.Id
        """

        return sql, field_map


class WorkRequestDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: WorkRequestSelectAllQuery,
        BaseDAO.INSERT_QUERY_KEY: WorkRequestInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: WorkRequestUpdateQuery,
        WorkRequestQuery.DELETE_BY_USER: WorkRequestDeleteByUserQuery,
        WorkRequestQuery.SELECT_FILTERED: WorkRequestSelectFilteredQuery,
    }
