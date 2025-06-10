from types import ModuleType
from fastapi import FastAPI

from python_framework.dynamic_loader import load_submodules
from python_framework.logger import ContextLogger, LogLevel
from fastapi.middleware.cors import CORSMiddleware

import uvicorn

import logging


class EndpointFilter(logging.Filter):
    """Filter class to exclude specific endpoints from log entries."""

    excluded_endpoints: list[str]

    def __init__(self, excluded_endpoints: list[str]) -> None:
        """
        Initialize the EndpointFilter class.

        Args:
            excluded_endpoints: A list of endpoints to be excluded from log entries.
        """
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out log entries for excluded endpoints.

        Args:
            record: The log record to be filtered.

        Returns:
            bool: True if the log entry should be included, False otherwise.
        """
        return (
            record.args
            and len(record.args) >= 3
            and record.args[2] not in self.excluded_endpoints
        )


DEFAULT_LOG_FILTERED_ENDPOINTS = ["/healthz", "/readyz", "/livez"]


class FastAPIRoot(object):

    _instance: "FastAPIRoot" = None

    application_name: str
    host: str
    port: int
    app: FastAPI = None
    log_filtered_endpoints: list[str]

    # Initialization #

    def __init__(
        self,
        application_name: str,
        host: str,
        port: int,
        log_filtered_endpoints: list[str] = DEFAULT_LOG_FILTERED_ENDPOINTS,
    ):
        self.app = None
        self.application_name = application_name
        self.host = host
        self.port = port
        self.log_filtered_endpoints = log_filtered_endpoints

    @staticmethod
    def instance() -> "FastAPIRoot":
        return FastAPIRoot._instance

    @staticmethod
    def initialize(
        application_name: str, host: str, port: int, resources_module: ModuleType
    ) -> "FastAPIRoot":
        if FastAPIRoot._instance is not None:
            return FastAPIRoot._instance

        ContextLogger.sys_log(LogLevel.INFO, "[FastAPIRoot] initializing...")

        FastAPIRoot._instance = FastAPIRoot(application_name, host, port)
        FastAPIRoot._instance.app = FastAPI(title=application_name)
        FastAPIRoot._instance.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        logging.getLogger("uvicorn.access").addFilter(
            EndpointFilter(FastAPIRoot._instance.log_filtered_endpoints)
        )

        FastAPIRoot._instance.register_routes(resources_module)

        FastAPIRoot._instance.print_routes()

        return FastAPIRoot._instance

    def register_routes(self, resources_module: ModuleType):
        modules = load_submodules(resources_module, ["register"])

        for module in modules:
            module.register(self)

    @staticmethod
    def run():
        uvicorn.run(
            FastAPIRoot._instance.app,
            host=FastAPIRoot._instance.host,
            port=FastAPIRoot._instance.port,
        )

    @staticmethod
    def stop():
        # TODO: potentially create + run server manually, then we can control "should_exit"
        pass

    def register_router(self, router):
        self.app.include_router(router)

    def print_routes(self):
        pass
