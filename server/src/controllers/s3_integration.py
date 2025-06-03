from json import loads
import traceback
from boto3 import client
from sys import exc_info, stdout
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from objects.s3_integration import S3ResultObject


class S3IntegrationController:

    _instance: "S3IntegrationController" = None

    _logger_key: str = None

    bucket_name: str
    model_data_path: str
    s3_client: any

    def __init__(self, bucket_name: str, model_data_path: str):
        self._logger_key = "S3IntegrationController"

        self.bucket_name = bucket_name
        self.model_data_path = model_data_path

        self.s3_client = client("s3")

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "S3IntegrationController":
        if S3IntegrationController._instance is not None:
            return S3IntegrationController._instance

        S3IntegrationController._instance = S3IntegrationController(
            load_environment_variable("MODEL_S3_BUCKET_NAME", error_on_none=True),
            load_environment_variable("MODEL_S3_DATA_PATH", error_on_none=True),
        )

        return S3IntegrationController._instance

    @staticmethod
    def instance() -> "S3IntegrationController":
        return S3IntegrationController._instance

    def upload_result(self, result_obj: S3ResultObject) -> bool:
        bucket_path = f"{self.model_data_path}/{result_obj.model_id}/{result_obj.request_id}/result.json"

        ContextLogger.debug(
            self._logger_key,
            "Uploading result for [%s - %s] to S3 URI [%s/%s]..."
            % (
                result_obj.model_id,
                result_obj.request_id,
                self.bucket_name,
                bucket_path,
            ),
        )

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                ContentType="application/json",
                Key=bucket_path,
                Metadata={
                    "modelId": result_obj.model_id,
                    "requestId": result_obj.request_id,
                },
                Body=result_obj.to_bytes(),
            )

            return True
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to upload result [%s - %s] to S3 URI [%s/%s], error = [%s]"
                % (
                    result_obj.model_id,
                    result_obj.request_id,
                    self.bucket_name,
                    bucket_path,
                    repr(exc_info()),
                ),
            )
            traceback.print_exc(file=stdout)

            return False

    def download_result(self, model_id: str, request_id: str) -> S3ResultObject:
        bucket_path = f"{self.model_data_path}/{model_id}/{request_id}/result.json"

        ContextLogger.debug(
            self._logger_key,
            "Downloading result for [%s - %s] from S3 URI [%s/%s]..."
            % (
                model_id,
                request_id,
                self.bucket_name,
                bucket_path,
            ),
        )

        try:
            result = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=bucket_path,
            )

            result_json = loads(result["Body"].read().decode("utf-8"))

            return S3ResultObject.from_object(result_json)
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to download result [%s - %s] from S3 URI [%s/%s], error = [%s]"
                % (
                    model_id,
                    request_id,
                    self.bucket_name,
                    bucket_path,
                    repr(exc_info()),
                ),
            )
            traceback.print_exc(file=stdout)

            return None
