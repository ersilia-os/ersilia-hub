

from sys import exc_info, stdout
from threading import Event, Thread
import traceback
from typing import List

from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from config.application_config import ApplicationConfig
from controllers.server import ServerController
from db.daos.server import ServerDAO, ServerQuery, ServerRecord
from controllers.k8s import K8sController
from controllers.work_request import WorkRequestController
from objects.k8s import ErsiliaAnnotations
from objects.work_request import WorkRequest, WorkRequestStatus

class FailedServerHandlerKillInstance(KillInstance):
    def kill(self):
        FailedServerHandler.instance().kill()

class FailedServerHandler(Thread):

    _instance: "FailedServerHandler" = None

    _logger_key: str
    _kill_event: Event

    def __init__(self):
        Thread.__init__(self)

        self._kill_event = Event()
        self._logger_key = f"FailedServerHandler"

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_FailedServerHandler", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "FailedServerHandler":
        if FailedServerHandler._instance is not None:
            return FailedServerHandler._instance

        FailedServerHandler._instance = FailedServerHandler()
        GracefulKiller.instance().register_kill_instance(
            FailedServerHandlerKillInstance()
        )

        return FailedServerHandler._instance

    @staticmethod
    def instance() -> "FailedServerHandler":
        return FailedServerHandler._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _terminate_active_pods(self, server_id: str, work_requests: List[WorkRequest]) -> bool:
        has_error = False

        for work_request in work_requests:
            try:
                K8sController.instance().delete_pod(
                    model_id=work_request.model_id,
                    annotations_filter=dict([(ErsiliaAnnotations.SERVER_ID.value, server_id), (ErsiliaAnnotations.REQUEST_ID.value, work_request.id)])
                )
                ContextLogger.debug(self._logger_key, f"Deleted pod related to failed server [{server_id}], work_request_id = [{work_request.id}]")
            except:
                ContextLogger.error(
                    self._logger_key,
                    f"Failed to delete pod work_request_id = [{work_request.id}], model_id = [{work_request.model_id}], error = [{repr(exc_info())}]"
                )
                has_error = True

        return not has_error

    def _requeue_work_requests(self, server_id: str) -> tuple[bool, List[WorkRequest]]:
        work_requests = WorkRequestController.instance().get_requests(
            server_ids=[server_id], 
            request_statuses=[WorkRequestStatus.QUEUED.value, WorkRequestStatus.SCHEDULING.value, WorkRequestStatus.PROCESSING.value]
        )
        
        has_error = False

        if len(work_requests) == 0:
            return (True, work_requests)

        for work_request in work_requests:
            work_request.server_id = None
            work_request.request_status = WorkRequestStatus.QUEUED
            work_request.request_status_reason = "REQUEUED"
            work_request.job_submission_timestamp = None
            work_request.pod_ready_timestamp = None
            work_request.processed_timestamp = None
            
            if WorkRequestController.instance().update_request(work_request, enforce_same_server_id=False) is None:
                has_error = True
                ContextLogger.error(self._logger_key, f"Failed to requeue work_request [{work_request.id}]")
            else:
                ContextLogger.debug(self._logger_key, f"Requeued work_request [{work_request.id}]")

        return (not has_error, work_requests)

    def _delete_server_entry(self, server_id: str):
        if ServerController.instance().delete_server(server_id) is None:
            ContextLogger.warn(self._logger_key, f"Failed to delete server [{server_id}]")
        else:
            ContextLogger.debug(self._logger_key, f"Deleted server [{server_id}]")

    def handle_failed_servers(self):
        failed_servers = ServerController.instance().load_unhealthy_servers()

        for server in failed_servers:
            ContextLogger.debug(self._logger_key, f"Found failed server [{server.server_id}]")

            requeue_success, requests = self._requeue_work_requests(server.server_id)
            delete_pod_success = self._terminate_active_pods(server.server_id, requests)
            
            if requeue_success and delete_pod_success:
                self._delete_server_entry(server.server_id)

    def run(self):
        ContextLogger.info(self._logger_key, "controller started")

        while True:
            if self._wait_or_kill(60):
                break

            self.handle_failed_servers()

        ContextLogger.info(self._logger_key, "controller stopped")

