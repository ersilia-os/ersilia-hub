from types import ModuleType
from fastapi import FastAPI

from python_framework.dynamic_loader import load_submodules
from python_framework.logger import ContextLogger, LogLevel
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uuid import uuid4

import uvicorn


class FastAPIRoot(object):

    _instance: "FastAPIRoot" = None

    application_name: str
    host: str
    port: int
    app: FastAPI = None

    # Initialization #

    def __init__(self, application_name: str, host: str, port: int):
        self.app = None
        self.application_name = application_name
        self.host = host
        self.port = port

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
