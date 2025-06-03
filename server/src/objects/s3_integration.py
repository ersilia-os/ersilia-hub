from json import dumps, loads
from typing import Any, Dict


class S3ResultObject:

    version: str
    model_id: str
    request_id: str
    result: str

    def __init__(
        self,
        model_id: str,
        request_id: str,
        result: str,
        version: str = "1.0.0",
    ):
        self.version = version
        self.model_id = model_id
        self.request_id = request_id
        self.result = result

    @staticmethod
    def from_object(obj: Dict[str, Any]) -> "S3ResultObject":
        if obj["version"] == "1.0.0":
            return S3ResultObject(
                obj["modelId"],
                obj["requestId"],
                obj["result"],
                version=obj["version"],
            )

        raise Exception("Unsupported S3Result version [%s]" % obj["version"])

    def to_object(self) -> Dict[str, Any]:
        if self.version == "1.0.0":
            return {
                "modelId": self.model_id,
                "requestId": self.request_id,
                "result": self.result,
                "version": self.version,
            }

        raise Exception("Unsupported S3Result version [%s]" % self.version)

    def to_bytes(self) -> bytes:
        return str.encode(dumps(self.to_object()))

    def extract_result(self) -> Any:
        if self.version == "1.0.0":
            return loads(self.result)
