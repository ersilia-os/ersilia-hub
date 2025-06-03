from enum import Enum
from typing import Any, Dict, List, Union


class JobStatus(Enum):

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        elif self.__class__ is other.__class__:
            return self.value == other.value

        return self.value == other

    def __str__(self):
        return self.name

    def __hash__(self):
        return str(self.name).__hash__()


class JobInputItem:
    key: str
    input: str


JobSubmissionRequestPayload = List[Union[str, JobInputItem]]


class JobSubmissionRequest:
    body: JobSubmissionRequestPayload
    params: Dict[str, str]
    orient: str  # probably enum?
    min_workers: int
    max_workers: int

    def __init__(
        self,
        body: JobSubmissionRequestPayload,
        params: Dict[str, str],
    ):
        self.body = body
        self.params = params

    @staticmethod
    def from_entries(entries: List[str]) -> "JobSubmissionRequest":
        # TODO: make the workers configurable based on model
        return JobSubmissionRequest(
            entries, {"orient": "records", "min_workers": 1, "max_workers": 5}
        )


class JobSubmissionResponse:

    job_id: str
    message: str

    def __init__(self, job_id: str, message: str):
        self.job_id = job_id
        self.message = message

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "JobSubmissionResponse":
        return JobSubmissionResponse(obj["job_id"], obj["message"])


class JobStatusResponse:
    job_id: str
    status: JobStatus

    def __init__(self, job_id: str, status: JobStatus):
        self.job_id = job_id
        self.status = status

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "JobStatusResponse":
        return JobStatusResponse(obj["job_id"], obj["status"])


JobResult = List[Dict[str, Any]]
