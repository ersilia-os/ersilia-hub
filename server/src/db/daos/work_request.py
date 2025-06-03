from enum import Enum
from typing import Dict, List, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class WorkRequestQuery(Enum):
    SELECT_FILTERED = "SELECT_FILTERED"


class WorkRequestRecord(DAORecord):
    id: int
    model_id: str
    user_id: str
    request_payload: str
    request_date: str
    metadata: str
    request_status: str
    request_status_reason: str
    model_job_id: str
    last_updated: Union[str, None]

    def __init__(self, result: dict):
        super().__init__(result)

        self.id = result["id"]
        self.model_id = result["modelid"]
        self.user_id = result["userid"]
        self.request_payload = result["requestpayload"]
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

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "model_id": self.model_id,
            "user_id": self.user_id,
            "request_payload": self.request_payload,
            "request_date": self.request_date,
            "metadata": self.metadata,
            "request_status": self.request_status,
            "request_status_reason": self.request_status_reason,
        }

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "id": self.id,
            "request_status": self.request_status,
            "request_status_reason": self.request_status_reason,
            "model_job_id": self.model_job_id,
            "expected_last_updated": self.last_updated,
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
                Id,
                ModelId,
                UserId,
                RequestPayload::text,
                RequestDate::text,
                Metadata::text,
                RequestStatus,
                RequestStatusReason,
                ModelJobId,
                LastUpdated::text
            FROM WorkRequest
            ORDER BY RequestDate DESC, ModelId ASC
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
        self.limit = limit

    def to_sql(self):
        field_map = {}
        custom_filters = []

        if self.id is not None:
            custom_filters.append("Id = :query_Id")
            field_map["query_Id"] = self.id

        if self.model_ids is not None and len(self.model_ids) > 0:
            custom_filters.append(
                "ModelId IN (%s)" % ",".join(map(lambda x: "'%s'" % x, self.model_ids))
            )

        if self.user_id is not None:
            custom_filters.append("UserId = :query_UserId")
            field_map["query_UserId"] = self.user_id

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

        if self.session_id is not None:
            custom_filters.append(
                'Metadata @> \'{"sessionId": "%s"}\'' % self.session_id
            )

        sql = """
            SELECT
                Id,
                ModelId,
                UserId,
                RequestPayload::text,
                RequestDate::text,
                Metadata::text,
                RequestStatus,
                RequestStatusReason,
                ModelJobId,
                LastUpdated::text
            FROM WorkRequest
            %s
            ORDER BY RequestDate DESC, ModelId ASC
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
    ):
        super().__init__(WorkRequestRecord)

        self.model_id = model_id
        self.user_id = user_id
        self.request_payload = request_payload
        self.request_date = request_date
        self.metadata = metadata
        self.request_status = request_status
        self.request_status_reason = request_status_reason

    def to_sql(self):
        field_map = {
            "query_ModelId": self.model_id,
            "query_UserId": self.user_id,
            "query_RequestPayload": self.request_payload,
            "query_RequestDate": self.request_date,
            "query_Metadata": self.metadata,
            "query_RequestStatus": self.request_status,
            "query_RequestStatusReason": self.request_status_reason,
        }

        sql = """
            INSERT INTO WorkRequest (
                ModelId,
                UserId,
                RequestPayload,
                RequestDate,
                Metadata,
                RequestStatus,
                RequestStatusReason,
                LastUpdated
            )
            VALUES (
                :query_ModelId,
                :query_UserId,
                :query_RequestPayload,
                :query_RequestDate,
                :query_Metadata,
                :query_RequestStatus,
                :query_RequestStatusReason,
                CURRENT_TIMESTAMP
            )
            RETURNING
                Id,
                ModelId,
                UserId,
                RequestPayload::text,
                RequestDate::text,
                Metadata::text,
                RequestStatus,
                RequestStatusReason,
                ModelJobId,
                LastUpdated::text
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
    ):
        super().__init__(WorkRequestRecord)

        self.id = id
        self.request_status = request_status
        self.request_status_reason = request_status_reason
        self.model_job_id = model_job_id
        self.expected_last_updated = expected_last_updated

    def to_sql(self):
        field_map = {
            "query_Id": self.id,
            "query_RequestStatus": self.request_status,
            "query_RequestStatusReason": self.request_status_reason,
            "query_ModelJobId": self.model_job_id,
            "query_ExpectedLastUpdated": self.expected_last_updated,
        }

        sql = """
            UPDATE WorkRequest 
            SET
                RequestStatus = :query_RequestStatus,
                RequestStatusReason = :query_RequestStatusReason,
                ModelJobId = :query_ModelJobId,
                LastUpdated = CURRENT_TIMESTAMP
            WHERE Id = :query_Id
            AND LastUpdated = :query_ExpectedLastUpdated
            RETURNING
                Id,
                ModelId,
                UserId,
                RequestPayload::text,
                RequestDate::text,
                Metadata::text,
                RequestStatus,
                RequestStatusReason,
                ModelJobId,
                LastUpdated::text
        """

        return sql, field_map


class WorkRequestDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.SELECT_ALL_QUERY_KEY: WorkRequestSelectAllQuery,
        BaseDAO.INSERT_QUERY_KEY: WorkRequestInsertQuery,
        BaseDAO.UPDATE_QUERY_KEY: WorkRequestUpdateQuery,
        WorkRequestQuery.SELECT_FILTERED: WorkRequestSelectFilteredQuery,
    }
