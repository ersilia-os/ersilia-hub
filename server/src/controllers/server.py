


from threading import Event, Thread

from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

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

        server_id = "" # TODO: get hostname

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
        pass
        # TODO: insert new server record

    def on_termination(self):
        pass
        # TODO: drop record ?? - we have no need of keeping servers around, so drop seems good

    def check_in(self):
        pass
        # TODO: update last-check-in

    def run(self):
        ContextLogger.info(self._logger_key, "controller started")

        self.on_startup()

        while True:
            if self._wait_or_kill(30):
                break

            self.check_in()

        self.on_termination()
        
        ContextLogger.info(self._logger_key, "controller stopped")

         
