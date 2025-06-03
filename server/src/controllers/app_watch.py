from threading import Event, Thread
from time import sleep

from colorama import Back, Fore, Style
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.time import utc_now

STARTUP_LOG = """
   ****************************************************************
   ***                                                          ***
   *** %s Started - %s%s ***
   ***                                                          ***
   ****************************************************************
"""

SHUTDOWN_LOG = """
   ****************************************************************
   ***                                                          ***
   *** %s Stopped - %s%s ***
   ***                                                          ***
   ****************************************************************
"""


class AppWatchKillInstance(KillInstance):
    def kill(self):
        AppWatch.instance().kill()


class AppWatch(Thread):

    __instance: "AppWatch" = None

    _kill: Event
    _killed: bool

    application_name: str

    def __init__(self, application_name: str):
        Thread.__init__(self)

        self._killed = False
        self._kill = Event()

        self.application_name = application_name

    def kill(self):
        self._killed = True
        self._kill.set()

    def wait_or_kill(self, wait_time: int = 10):
        return self._kill.wait(wait_time)

    @staticmethod
    def instance() -> "AppWatch":
        return AppWatch.__instance

    @staticmethod
    def initialize(application_name: str) -> "AppWatch":
        if AppWatch.__instance is not None:
            return AppWatch.__instance

        AppWatch.__instance = AppWatch(application_name)

        GracefulKiller.register_kill_instance(AppWatchKillInstance())

        return AppWatch.__instance

    def run(self):
        sleep(5)  # wait before logging
        self.on_startup()

        while True:
            if self.wait_or_kill(2):
                sleep(5)  # wait before logging
                self.on_shutdown()
                break

    def on_startup(self):
        now = utc_now()
        startup_log = STARTUP_LOG % (self.application_name, now, " " * (32 - len(now)))
        foreground_colour = f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}"

        print(f"{foreground_colour}{startup_log}{Style.RESET_ALL}")

    def on_shutdown(self):
        now = utc_now()
        shutdown_log = SHUTDOWN_LOG % (
            self.application_name,
            now,
            " " * (32 - len(now)),
        )
        foreground_colour = f"{Style.BRIGHT}{Fore.LIGHTMAGENTA_EX}"

        print(f"{foreground_colour}{shutdown_log}{Style.RESET_ALL}")
