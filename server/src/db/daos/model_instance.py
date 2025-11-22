from typing import Dict, Union

import python_framework.db.dao.dao as BaseDAO
from python_framework.db.dao.objects import DAOQuery, DAORecord
from python_framework.time import timestamp_to_utc_timestamp


class ModelInstanceRecord(DAORecord):
    model_id: str
    work_request_id: int
    instance_id: str | None
    instance_details: str | None
    state: str
    termination_reason: str | None
    job_submission_process: str | None
    last_updated: str | None

    def __init__(self, result: dict):
        super().__init__(result)

        self.model_id = result["modelid"]
        self.work_request_id = result["workrequestid"]
        self.instance_id = result["instanceid"]
        self.instance_details = result["instancedetails"]
        self.state = result["state"]
        self.termination_reason = result["terminationreason"]
        self.job_submission_process = result["jobsubmissionprocess"]
        self.last_updated = (
            None
            if "lastupdated" not in result or result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return {
            "model_id": self.model_id,
            "work_request_id": self.work_request_id,
            "instance_id": self.instance_id,
            "instance_details": self.instance_details,
            "state": self.state,
            "termination_reason": self.termination_reason,
            "job_submission_process": self.job_submission_process,
            "expected_last_updated": self.last_updated,
        }

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class ModelInstanceExtendedRecord(DAORecord):
    model_id: str
    work_request_id: int
    instance_id: str | None
    instance_details: str | None
    state: str
    termination_reason: str | None
    job_submission_process: str | None
    last_updated: str | None

    last_event: str | None
    work_request: str | None

    def __init__(self, result: dict):
        super().__init__(result)

        self.model_id = result["modelid"]
        self.work_request_id = result["workrequestid"]
        self.instance_id = result["instanceid"]
        self.instance_details = result["instancedetails"]
        self.state = result["state"]
        self.termination_reason = result["terminationreason"]
        self.job_submission_process = result["jobsubmissionprocess"]
        self.last_updated = (
            None
            if "lastupdated" not in result or result["lastupdated"] is None
            else timestamp_to_utc_timestamp(result["lastupdated"])
        )
        self.last_event = result["lastevent"]
        self.work_request = result["workrequest"]

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class ModelInstanceUpsertQuery(DAOQuery):
    model_id: str
    work_request_id: int
    instance_id: str | None
    instance_details: str | None
    state: str
    termination_reason: str | None
    job_submission_process: str | None
    expected_last_updated: str | None

    def __init__(
        self,
        model_id: str,
        work_request_id: int,
        instance_id: str | None,
        instance_details: str | None,
        state: str,
        termination_reason: str | None,
        job_submission_process: str | None,
        expected_last_updated: str | None,
    ):
        super().__init__(ModelInstanceRecord)

        self.model_id = model_id
        self.work_request_id = work_request_id
        self.instance_id = instance_id
        self.instance_details = instance_details
        self.state = state
        self.termination_reason = termination_reason
        self.job_submission_process = job_submission_process
        self.expected_last_updated = expected_last_updated

    def to_sql(self):
        # TODO: from here
        field_map = {
            "query_ModelId": self.model_id,
            "query_WorkRequestId": self.work_request_id,
            "query_InstanceId": self.instance_id,
            "query_InstanceDetails": self.instance_details,
            "query_State": self.state,
            "query_TerminationReason": self.termination_reason,
            "query_JobSubmissionProcess": self.job_submission_process,
            "query_ExpectedLastUpdated": self.expected_last_updated,
        }

        sql = """
            INSERT INTO ModelInstance (
                ModelId,
                WorkRequestId,
                InstanceId,
                InstanceDetails,
                State,
                TerminationReason,
                JobSubmissionDetails,
                LastUpdated
            )
            VALUES (
                :query_ModelId,
                :query_WorkRequestId,
                :query_InstanceId,
                :query_InstanceDetails,
                :query_State,
                :query_TerminationReason,
                :query_JobSubmissionProcess,
                CURRENT_TIMESTAMP
            )
            ON CONFLICT
            UPDATE ModelInstance
            SET InstanceId = EXCLUDED.InstanceId,
                InstanceDetails = EXCLUDED.InstanceDetails,
                State = EXCLUDED.State,
                TerminationReason = EXCLUDED.TerminationReason,
                JobSubmissionProcess = EXCLUDED.JobSubmissionProcess,
                LastUpdated = EXCLUDED.LastUpdated
            WHERE ModelId = EXCLUDED.ModelId
            AND WorkRequestId = EXCLUDED.WorkRequestId
            AND LastUpdated = :query_ExpectedLastUpdated
            RETURNING
                ModelId,
                WorkRequestId,
                InstanceId,
                InstanceDetails::text,
                State,
                TerminationReason,
                JobSubmissionDetails::text,
                LastUpdated::text
        """

        return sql, field_map


class ModelInstanceSelectFilteredQuery(DAOQuery):
    model_ids: list[str] | None
    work_request_ids: list[str] | None
    instance_ids: list[str] | None
    limit: int
    date_from: str | None
    date_to: str | None
    instance_states: list[str] | None
    not_instance_states: list[str] | None

    def __init__(
        self,
        model_ids: list[str] | None = None,
        work_request_ids: list[str] | None = None,
        instance_ids: list[str] | None = None,
        limit: int = 100,
        date_from: str | None = None,
        date_to: str | None = None,
        instance_states: list[str] | None = None,
        not_instance_states: list[str] | None = None,
    ):
        super().__init__(ModelInstanceExtendedRecord)

        self.model_ids = model_ids
        self.work_request_ids = work_request_ids
        self.instance_ids = instance_ids
        self.date_from = date_from
        self.date_to = date_to
        self.limit = limit
        self.instance_states = instance_states
        self.not_instance_states = not_instance_states

    def to_sql(self):
        field_map = {}
        custom_filters = []

        if self.model_ids is not None and len(self.model_ids) > 0:
            custom_filters.append(
                "ModelInstance.ModelId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.model_ids))
            )

        if self.work_request_ids is not None and len(self.work_request_ids) > 0:
            custom_filters.append(
                "ModelInstance.WorkRequestId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.work_request_ids))
            )

        if self.instance_ids is not None and len(self.instance_ids) > 0:
            custom_filters.append(
                "ModelInstance.InstanceId IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.instance_ids))
            )

        if self.date_from is not None and self.date_to is not None:
            custom_filters.append(
                "ModelInstance.LastUpdated BETWEEN :query_DateFrom AND :query_DateTo"
            )
            field_map["query_DateFrom"] = self.date_from
            field_map["query_DateTo"] = self.date_to
        elif self.date_from is not None:
            custom_filters.append("ModelInstance.LastUpdated >= :query_DateFrom")
            field_map["query_DateFrom"] = self.date_from
        elif self.date_to is not None:
            custom_filters.append("ModelInstance.LastUpdated <= :query_DateTo")
            field_map["query_DateTo"] = self.date_to

        if self.instance_states is not None and len(self.instance_states) > 0:
            custom_filters.append(
                "ModelInstance.State IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.instance_states))
            )

        if self.not_instance_states is not None and len(self.not_instance_states) > 0:
            custom_filters.append(
                "ModelInstance.State NOT IN (%s)"
                % ",".join(map(lambda x: "'%s'" % x, self.not_instance_states))
            )

        sql = """
            SELECT
                ModelInstance.ModelId,
                ModelInstance.WorkRequestId,
                ModelInstance.InstanceId,
                ModelInstance.InstanceDetails::text,
                ModelInstance.State,
                ModelInstance.TerminationReason,
                ModelInstance.JobSubmissionDetails::text,
                ModelInstance.LastUpdated::text,
                row_to_json(wr) AS workrequest,
                row_to_json(log) AS lastevent
            FROM ModelInstance
            LEFT JOIN WorkRequest wr
                ON ModelInstance.ModelId = wr.ModelId
                AND ModelInstance.WorkRequestId = wr.id
            LEFT JOIN LATERAL (
                SELECT *
                FROM ModelInstanceLog log
                WHERE ModelInstance.ModelId = log.ModelId
                AND (
                    ModelInstance.WorkRequestId = log.CorrelationId
                    OR ModelInstance.InstanceId = log.InstanceId
                )
                ORDER BY log.LogTimestamp DESC
                LIMIT 1
            ) lastevent
            %s
            ORDER BY ModelInstance.LastUpdated DESC
            LIMIT %d
        """ % (
            "" if len(custom_filters) == 0 else "WHERE " + " AND ".join(custom_filters),
            self.limit,
        )

        return sql, field_map


class ModelInstanceDAO(BaseDAO.DAO):
    queries = {
        BaseDAO.UPSERT_QUERY_KEY: ModelInstanceUpsertQuery,
        BaseDAO.SELECT_ALL_QUERY_KEY: ModelInstanceSelectFilteredQuery,
    }
