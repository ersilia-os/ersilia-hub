import traceback
from enum import Enum
from json import dumps
from sys import exc_info, stdout
from typing import List

from config.application_config import ApplicationConfig
from db.daos.model_instance_log import (
    ModelInstanceLogDAO,
    ModelInstanceLogRecord,
)
from objects.k8s import ErsiliaAnnotations, ErsiliaLabels, K8sPod
from python_framework.config_utils import load_environment_variable
from python_framework.logger import ContextLogger, LogLevel


class ModelInstanceLogEvent(Enum):
    INSTANCE_REQUESTED = "INSTANCE_REQUESTED"
    INSTANCE_CREATED = "INSTANCE_CREATED"
    INSTANCE_CREATION_FAILED = "INSTANCE_CREATION_FAILED"
    INSTANCE_POD_CREATED = "INSANCE_POD_CREATED"
    INSTANCE_POD_CREATION_FAILED = "INSANCE_POD_CREATION_FAILED"
    INSTANCE_POD_TERMINATED = "INSTANCE_POD_TERMINATED"
    INSTANCE_POD_OOMKILLED = "INSTANCE_POD_OOMKILLED"
    INSTANCE_POD_READY = "INSTANCE_POD_READY"
    INSTANCE_TERMINATED = "INSTANCE_TERMINATED"
    INSTANCE_QUERIED = "INSTANCE_QUERIED"
    INSTANCE_READINESS_CHECKED = "INSTANCE_READINESS_CHECKED"
    INSTANCE_READY = "INSTANCE_READY"
    INSTANCE_READINESS_FAILED = "INSTANCE_READINESS_FAILED"
    INSTANCE_JOB_SUBMITTED = "INSTANCE_JOB_SUBMITTED"
    INSTANCE_JOB_SUBMISSION_FAILED = "INSTANCE_JOB_SUBMISSION_FAILED"
    INSTANCE_JOB_COMPLETED = "INSTANCE_JOB_COMPLETED"
    INSTANCE_UPDATED = "INSTANCE_UPDATED"

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


class ModelInstanceLogController:
    _instance: "ModelInstanceLogController" = None

    _logger_key: str = None

    def __init__(self):
        self._logger_key = "ModelInstanceLogController"

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "ModelInstanceLogController":
        if ModelInstanceLogController._instance is not None:
            return ModelInstanceLogController._instance

        ModelInstanceLogController._instance = ModelInstanceLogController()

        return ModelInstanceLogController._instance

    @staticmethod
    def instance() -> "ModelInstanceLogController":
        return ModelInstanceLogController._instance

    def log_instance(
        self,
        log_event: ModelInstanceLogEvent,
        k8s_pod: K8sPod | None = None,
        model_id: str | None = None,
        work_request_id: int | str | None = None,
    ):
        _model_id = (
            model_id
            if model_id is not None
            else (
                k8s_pod.labels.get(ErsiliaLabels.MODEL_ID.value)
                if k8s_pod is not None
                else None
            )
        )

        if _model_id is None:
            ContextLogger.error(
                self._logger_key, "Failed to log_instance, model_id or k8s_pod is null"
            )
            return

        _correlation_id = (
            str(work_request_id)
            if work_request_id is not None
            else (
                k8s_pod.annotations.get(ErsiliaAnnotations.REQUEST_ID.value)
                if k8s_pod is not None
                else "UNKNOWN"
            )
        )

        _instance_id = (
            f"{_model_id}_{_correlation_id}" if k8s_pod is None else k8s_pod.name
        )

        log_record = ModelInstanceLogRecord.init(
            modelid=_model_id,
            instanceid=_instance_id,
            correlationid=_correlation_id,
            instancedetails="{}" if k8s_pod is None else dumps(k8s_pod.to_object()),
            logevent=str(log_event),
        )

        try:
            results: List[ModelInstanceLogRecord] = ModelInstanceLogDAO.execute_insert(
                ApplicationConfig.instance().database_config,
                **log_record.generate_insert_query_args(),
            )

            if results is None or len(results) == 0:
                raise Exception("Insert returned zero records")

            # ContextLogger.debug(
            #     self._logger_key,
            #     "WorkRequest inserted, new id = [%s]" % new_work_request.id,
            # )
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to insert ModelInstanceLog, error = [%s]" % (repr(exc_info()),),
            )
            traceback.print_exc(file=stdout)
