from typing import Any, Dict, List

from pydantic import BaseModel
from db.daos.work_request_stats import WorkRequestStatsRecord


def default_float(value: float | None) -> float:
    return 0.0 if value is None else value


def default_int(value: int | None) -> int:
    return 0 if value is None else value


class WorkRequestStatsModel(BaseModel):
    model_id: str
    input_size: int
    total_count: int
    success_count: int
    failed_count: int

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

    total_failed_request_start_time: float
    max_failed_request_start_time: float
    min_failed_request_start_time: float
    avg_failed_request_start_time: float

    total_failed_request_time: float
    max_failed_request_time: float
    min_failed_request_time: float
    avg_failed_request_time: float

    total_failed_job_execution_time: float
    max_failed_job_execution_time: float
    min_failed_job_execution_time: float
    avg_failed_job_execution_time: float

    @staticmethod
    def init(
        model_id: str,
        input_size: int,
        total_count: int,
        success_count: int,
        failed_count: int,
        total_all_request_start_time: float,
        max_all_request_start_time: float,
        min_all_request_start_time: float,
        avg_all_request_start_time: float,
        total_all_request_time: float,
        max_all_request_time: float,
        min_all_request_time: float,
        avg_all_request_time: float,
        total_all_job_execution_time: float,
        max_all_job_execution_time: float,
        min_all_job_execution_time: float,
        avg_all_job_execution_time: float,
        total_success_request_start_time: float,
        max_success_request_start_time: float,
        min_success_request_start_time: float,
        avg_success_request_start_time: float,
        total_success_request_time: float,
        max_success_request_time: float,
        min_success_request_time: float,
        avg_success_request_time: float,
        total_success_job_execution_time: float,
        max_success_job_execution_time: float,
        min_success_job_execution_time: float,
        avg_success_job_execution_time: float,
        total_failed_request_start_time: float,
        max_failed_request_start_time: float,
        min_failed_request_start_time: float,
        avg_failed_request_start_time: float,
        total_failed_request_time: float,
        max_failed_request_time: float,
        min_failed_request_time: float,
        avg_failed_request_time: float,
        total_failed_job_execution_time: float,
        max_failed_job_execution_time: float,
        min_failed_job_execution_time: float,
        avg_failed_job_execution_time: float,
    ):
        return WorkRequestStatsModel(
            model_id=model_id,
            input_size=default_int(input_size),
            total_count=default_int(total_count),
            success_count=default_int(success_count),
            failed_count=default_int(failed_count),
            total_all_request_start_time=default_float(total_all_request_start_time),
            max_all_request_start_time=default_float(max_all_request_start_time),
            min_all_request_start_time=default_float(min_all_request_start_time),
            avg_all_request_start_time=default_float(avg_all_request_start_time),
            total_all_request_time=default_float(total_all_request_time),
            max_all_request_time=default_float(max_all_request_time),
            min_all_request_time=default_float(min_all_request_time),
            avg_all_request_time=default_float(avg_all_request_time),
            total_all_job_execution_time=default_float(total_all_job_execution_time),
            max_all_job_execution_time=default_float(max_all_job_execution_time),
            min_all_job_execution_time=default_float(min_all_job_execution_time),
            avg_all_job_execution_time=default_float(avg_all_job_execution_time),
            total_success_request_start_time=default_float(
                total_success_request_start_time
            ),
            max_success_request_start_time=default_float(
                max_success_request_start_time
            ),
            min_success_request_start_time=default_float(
                min_success_request_start_time
            ),
            avg_success_request_start_time=default_float(
                avg_success_request_start_time
            ),
            total_success_request_time=default_float(total_success_request_time),
            max_success_request_time=default_float(max_success_request_time),
            min_success_request_time=default_float(min_success_request_time),
            avg_success_request_time=default_float(avg_success_request_time),
            total_success_job_execution_time=default_float(
                total_success_job_execution_time
            ),
            max_success_job_execution_time=default_float(
                max_success_job_execution_time
            ),
            min_success_job_execution_time=default_float(
                min_success_job_execution_time
            ),
            avg_success_job_execution_time=default_float(
                avg_success_job_execution_time
            ),
            total_failed_request_start_time=default_float(
                total_failed_request_start_time
            ),
            max_failed_request_start_time=default_float(max_failed_request_start_time),
            min_failed_request_start_time=default_float(min_failed_request_start_time),
            avg_failed_request_start_time=default_float(avg_failed_request_start_time),
            total_failed_request_time=default_float(total_failed_request_time),
            max_failed_request_time=default_float(max_failed_request_time),
            min_failed_request_time=default_float(min_failed_request_time),
            avg_failed_request_time=default_float(avg_failed_request_time),
            total_failed_job_execution_time=default_float(
                total_failed_job_execution_time
            ),
            max_failed_job_execution_time=default_float(max_failed_job_execution_time),
            min_failed_job_execution_time=default_float(min_failed_job_execution_time),
            avg_failed_job_execution_time=default_float(avg_failed_job_execution_time),
        )

    @staticmethod
    def init_from_record(record: WorkRequestStatsRecord) -> "WorkRequestStatsModel":
        return WorkRequestStatsModel.init(
            record.model_id,
            record.input_size,
            record.total_count,
            record.success_count,
            record.failed_count,
            record.total_all_request_start_time,
            record.max_all_request_start_time,
            record.min_all_request_start_time,
            record.avg_all_request_start_time,
            record.total_all_request_time,
            record.max_all_request_time,
            record.min_all_request_time,
            record.avg_all_request_time,
            record.total_all_job_execution_time,
            record.max_all_job_execution_time,
            record.min_all_job_execution_time,
            record.avg_all_job_execution_time,
            record.total_success_request_start_time,
            record.max_success_request_start_time,
            record.min_success_request_start_time,
            record.avg_success_request_start_time,
            record.total_success_request_time,
            record.max_success_request_time,
            record.min_success_request_time,
            record.avg_success_request_time,
            record.total_success_job_execution_time,
            record.max_success_job_execution_time,
            record.min_success_job_execution_time,
            record.avg_success_job_execution_time,
            record.total_failed_request_start_time,
            record.max_failed_request_start_time,
            record.min_failed_request_start_time,
            record.avg_failed_request_start_time,
            record.total_failed_request_time,
            record.max_failed_request_time,
            record.min_failed_request_time,
            record.avg_failed_request_time,
            record.total_failed_job_execution_time,
            record.max_failed_job_execution_time,
            record.min_failed_job_execution_time,
            record.avg_failed_job_execution_time,
        )


class WorkRequestStatsListModel(BaseModel):

    stats: List[WorkRequestStatsModel]


class WorkRequestStatsFilters(BaseModel):
    user_id: str = None
    session_id: str = None
    model_ids: List[str] = []
    request_date_from: str = None
    request_date_to: str = None
    request_statuses: List[str] = []
    input_size_ge: int | None = None
    input_size_le: int | None = None
    group_by: List[str] = None

    def to_object(self) -> Dict[str, Any]:
        filters = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "model_ids": self.model_ids,
            "request_date_from": self.request_date_from,
            "request_date_to": self.request_date_to,
            "request_statuses": self.request_statuses,
            "input_size_ge": self.input_size_ge,
            "input_size_le": self.input_size_le,
            "group_by": self.group_by,
        }

        return filters


class WorkRequestStatsFilterData(BaseModel):

    model_ids: List[str]
    group_by: List[str] = ["ModelId", "InputSize"]
