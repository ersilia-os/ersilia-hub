from platform import node
from sys import exc_info, stdout
from threading import Event, Thread
import traceback
from typing import List

from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from python_framework.time import utc_now

from config.application_config import ApplicationConfig
from db.daos.server import ServerDAO, ServerQuery, ServerRecord

class ServerControllerKillInstance(KillInstance):
    def kill(self):
        ServerController.instance().kill()

class ServerController(Thread):

    _instance: "ServerController" = None

    server_id: str
    
    _logger_key: str
    _kill_event: Event

    def __init__(self):
        Thread.__init__(self)

        self.server_id = load_environment_variable("SERVER_ID", default=node())

        self._kill_event = Event()
        self._logger_key = f"Server"

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_Server", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "ServerController":
        if ServerController._instance is not None:
            return ServerController._instance

        ServerController._instance = ServerController()
        GracefulKiller.instance().register_kill_instance(
            ServerControllerKillInstance()
        )

        return ServerController._instance

    @staticmethod
    def instance() -> "ServerController":
        return ServerController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def on_startup(self):
        server_record = ServerRecord.init(
            serverid=self.server_id,
            ishealthy=1,
            startuptime=utc_now(),
            lastcheckin=utc_now()
        )

        try:
            results: List[ServerRecord] = ServerDAO.execute_upsert(
                ApplicationConfig.instance().database_config,
                **server_record.generate_upsert_query_args(),
            )

            if results is None or len(results) == 0:
                raise Exception("Insert returned zero records")

            
            ContextLogger.debug(
                self._logger_key,
                "ServerRecord inserted"
            )
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to insert ServerRecord, error = [%s]" % (repr(exc_info()),),
            )
            traceback.print_exc(file=stdout)

    def delete_server(self, server_id: str) -> ServerRecord | None:
        server_record = ServerRecord.init(
            serverid=server_id,
            ishealthy=1,
            lastcheckin=None
        )

        try:
            results: List[ServerRecord] = ServerDAO.execute_delete(
                ApplicationConfig.instance().database_config,
                **server_record.generate_delete_query_args(),
            )

            if results is None or len(results) == 0:
                return None
            
            return results[0]
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to delete ServerRecord, error = [%s]" % (repr(exc_info()),),
            )
            traceback.print_exc(file=stdout)

            return None

    def on_termination(self):
        # NOTE: we do not want to delete the server, in case there are hanging processes / requests
        #       if we delete, we cannot do cleanup from other servers
        ContextLogger.debug(
            self._logger_key,
            "Server termination successful"
        )

    def check_in(self):
        server_record = ServerRecord.init(
            serverid=self.server_id,
            ishealthy=1,
            lastcheckin=utc_now()
        )

        try:
            results: List[ServerRecord] = ServerDAO.execute_update(
                ApplicationConfig.instance().database_config,
                **server_record.generate_update_query_args(),
            )

            if results is None or len(results) == 0:
                raise Exception("Update returned zero records")

            
            ContextLogger.debug(
                self._logger_key,
                "Server check-in successful"
            )
        except:
            ContextLogger.error(
                self._logger_key,
                "Server check-in failed to update ServerRecord, error = [%s]" % (repr(exc_info()),),
            )
            traceback.print_exc(file=stdout)

    def load_unhealthy_servers(self) -> List[ServerRecord]:
        try:
            results: List[ServerRecord] = ServerDAO.execute_query(
                ServerQuery.SELECT_UNHEALTHY,
                ApplicationConfig.instance().database_config,
            )

            return list(filter(lambda s: s.server_id != self.server_id, results))
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to load unhealthy servers, error = [%s]" % (repr(exc_info()),),
            )
            traceback.print_exc(file=stdout)

            return []

    def run(self):
        ContextLogger.info(self._logger_key, "controller started")

        self.on_startup()

        while True:
            if self._wait_or_kill(30):
                break

            self.check_in()

        self.on_termination()
        
        ContextLogger.info(self._logger_key, "controller stopped")

