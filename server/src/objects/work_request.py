from enum import Enum
from json import dumps, loads
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Field

from db.daos.work_request import WorkRequestRecord


class WorkRequestPayloadModel(BaseModel):
    entries: List[str]

    def to_object(self) -> Dict[str, Any]:
        return {
            "entries": self.entries,
        }


class WorkRequestPayload:

    entries: List[str]

    def __init__(self, entries: List[str]):
        self.entries = entries

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "WorkRequestPayload":
        if obj is None or "entries" not in obj or len(obj["entries"]) <= 0:
            raise Exception("Invalid request payload")

        return WorkRequestPayload(
            obj["entries"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "entries": self.entries,
        }


class WorkRequestStatus(Enum):

    QUEUED = "QUEUED"
    SCHEDULING = "SCHEDULING"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        elif self.__class__ is other.__class__:
            return self.value == other.value

        return self.value == other

    def __str__(self):
        return self.name

    def __hash__(self):
        return str(self.name).__hash__()


# NOT RETURNED VIA API
class WorkRequestMetadata:

    user_agent: str
    session_id: str

    def __init__(
        self,
        user_agent: str,
        session_id: str,
    ):
        self.user_agent = user_agent
        self.session_id = session_id

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "WorkRequestMetadata":
        return WorkRequestMetadata(
            obj["userAgent"],
            obj["sessionId"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "userAgent": self.user_agent,
            "sessionId": self.session_id,
        }


class WorkRequest:

    id: int
    model_id: str
    user_id: str
    request_payload: WorkRequestPayload
    request_date: str
    metadata: WorkRequestMetadata
    request_status: WorkRequestStatus
    request_status_reason: Union[str, None]
    model_job_id: Union[str, None]
    last_updated: Union[str, None]

    def __init__(
        self,
        id: int,
        model_id: str,
        user_id: str,
        request_payload: WorkRequestPayload,
        request_date: str,
        metadata: WorkRequestMetadata,
        request_status: WorkRequestStatus,
        request_status_reason: Union[str, None] = None,
        model_job_id: Union[str, None] = None,
        last_updated: Union[str, None] = None,
    ):
        self.id = id
        self.model_id = model_id
        self.user_id = user_id
        self.request_payload = request_payload
        self.request_date = request_date
        self.metadata = metadata
        self.request_status = request_status
        self.request_status_reason = request_status_reason
        self.model_job_id = model_job_id
        self.last_updated = last_updated

    @staticmethod
    def init_from_record(record: WorkRequestRecord) -> "WorkRequest":
        return WorkRequest(
            record.id,
            record.model_id,
            record.user_id,
            WorkRequestPayload.from_object(loads(record.request_payload)),
            record.request_date,
            WorkRequestMetadata.from_object(loads(record.metadata)),
            record.request_status,
            record.request_status_reason,
            record.model_job_id,
            record.last_updated,
        )

    def to_record(self) -> WorkRequestRecord:
        return WorkRequestRecord.init(
            id=self.id,
            modelid=self.model_id,
            userid=self.user_id,
            requestpayload=dumps(self.request_payload.to_object()),
            requestdate=self.request_date,
            metadata=dumps(self.metadata.to_object()),
            requeststatus=self.request_status,
            requeststatusreason=self.request_status_reason,
            modeljobid=self.model_job_id,
            lastupdated=self.last_updated,
        )

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "WorkRequest":
        return WorkRequest(
            None if "id" not in obj else obj["id"],
            obj["modelId"],
            None if "userId" not in obj else obj["userId"],
            WorkRequestPayload.from_object(obj["requestPayload"]),
            None if "requestDate" not in obj else obj["requestDate"],
            (
                WorkRequestMetadata(None, None)
                if "metadata" not in obj
                else WorkRequestMetadata.from_object(obj["metadata"])
            ),
            None if "requestStatus" not in obj else obj["requestStatus"],
            None if "requestStatusReason" not in obj else obj["requestStatusReason"],
            None if "modelJobId" not in obj else obj["modelJobId"],
            None if "lastUpdated" not in obj else obj["lastUpdated"],
        )

    def to_object(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "modelId": self.model_id,
            "userId": self.user_id,
            "requestPayload": self.request_payload.to_object(),
            "requestDate": self.request_date,
            "metadata": self.metadata.to_object(),
            "requestStatus": str(self.request_status),
            "requestStatusReason": self.request_status_reason,
            "modelJobId": self.model_job_id,
            "lastUpdated": self.last_updated,
        }


class WorkRequestCreateModel(BaseModel):

    model_id: str
    request_payload: WorkRequestPayloadModel

    def to_object(self) -> Dict[str, Any]:
        return {
            "modelId": self.model_id,
            "requestPayload": self.request_payload.to_object(),
        }


# Result is either a Json list or a CSV file of lines
WorkRequestResult = List[Union[str, Dict[str, Any]]]


class WorkRequestModel(BaseModel):

    id: int | None = None
    model_id: str
    user_id: str
    request_payload: WorkRequestPayloadModel
    request_date: str | None = None
    request_status: WorkRequestStatus | None = None
    request_status_reason: str | None = None
    model_job_id: str | None = None
    last_updated: str | None = None
    result: WorkRequestResult | None = None

    def to_object(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "modelId": self.model_id,
            "userId": self.user_id,
            "requestPayload": self.request_payload.to_object(),
            "requestDate": self.request_date,
            "requestStatus": str(self.request_status),
            "requestStatusReason": self.request_status_reason,
            "modelJobId": self.model_job_id,
            "lastUpdated": self.last_updated,
            "result": self.result,
        }

    @staticmethod
    def from_workrequest(workrequest: WorkRequest) -> "WorkRequestModel":
        return WorkRequestModel(
            id=workrequest.id,
            model_id=workrequest.model_id,
            user_id=workrequest.user_id,
            request_payload=(
                None
                if workrequest.request_payload is None
                else WorkRequestPayloadModel(
                    entries=workrequest.request_payload.entries
                )
            ),
            request_date=workrequest.request_date,
            request_status=workrequest.request_status,
            request_status_reason=workrequest.request_status_reason,
            model_job_id=workrequest.model_job_id,
            last_updated=workrequest.last_updated,
            result=None,
        )

    def map_result_to_csv(self):
        if self.result is None:
            return

        # check if result is a list of something, we don't support string / object yet
        if not isinstance(self.result, list):
            return

        if len(self.result) == 0:
            return

        # already a string (probably CSV)
        if isinstance(self.result[0], str):
            return

        if not isinstance(self.result[0], dict):
            return

        # we will map the json to a header line and multiple value lines
        csv_column_names = []
        csv_value_lines: List[List[str]] = []

        for result in self.result:
            is_first_result = len(csv_column_names) == 0
            csv_value_line = []

            for key, value in result.items():
                if is_first_result:
                    csv_column_names.append(key)

                if isinstance(value, str):
                    csv_value_line.append(f"'{value}'")
                else:
                    csv_value_line.append(str(value))

            csv_value_lines.append(csv_value_line)

        self.result = [
            ",".join(csv_column_names),
        ] + list(map(lambda csv_line: ",".join(csv_line), csv_value_lines))


class WorkRequestListModel(BaseModel):

    items: List[WorkRequestModel]


class WorkRequestUpdateModel(BaseModel):

    id: int
    request_status: WorkRequestStatus
    request_status_reason: str | None = None
    model_job_id: str | None = None

    def __init__(
        self,
        id: int,
        request_status: WorkRequestStatus,
        request_status_reason: Union[str, None] = None,
        model_job_id: Union[str, None] = None,
    ):
        self.id = id
        self.request_status = request_status
        self.request_status_reason = request_status_reason
        self.model_job_id = model_job_id

    def to_work_request(self) -> WorkRequest:
        return WorkRequest(
            self.id,
            None,
            None,
            None,
            None,
            self.request_status,
            request_status_reason=self.request_status_reason,
            model_job_id=self.model_job_id,
        )


class WorkRequestLoadAllFilters(BaseModel):
    id: str = None
    user_id: str = None
    model_ids: List[str] = []
    request_date_from: str = None
    request_date_to: str = None
    request_statuses: List[str] = []
    limit: int = Field(100, gt=0, le=500)

    def to_object(self) -> Dict[str, Any]:
        filters = {
            "id": self.id,
            "user_id": self.user_id,
            "model_ids": self.model_ids,
            "request_date_from": self.request_date_from,
            "request_date_to": self.request_date_to,
            "request_statuses": self.request_statuses,
            "limit": self.limit,
        }

        if self.limit is None:
            del filters["limit"]

        return filters


class WorkRequestLoadFilters(BaseModel):
    include_result: bool = False
    csv_result: bool = False
    user_id: str = None
