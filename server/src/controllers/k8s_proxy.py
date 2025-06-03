from sys import exc_info, stdout
from threading import Lock
import traceback
from typing import Dict, List
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from subprocess import Popen

from controllers.k8s import K8sController

PORT_RANGE_START = 9010
PORT_RANGE_END = 9030


class K8sProxy:

    model_id: str
    request_id: str
    port: int
    host: str
    process: Popen

    def __init__(
        self,
        model_id: str,
        request_id: str,
        port: int,
        process: Popen,
        host: str = "localhost",
    ):
        self.model_id = model_id
        self.request_id = request_id
        self.port = port
        self.host = host
        self.process = process


class K8sProxyController:

    _instance: "K8sProxyController" = None

    _logger_key: str = None

    _proxies: Dict[str, K8sProxy]
    _port_status: Dict[int, bool]
    _portforward_lock: Lock

    def __init__(self):
        self._logger_key = "K8sProxyController"
        self._proxies = {}
        self._port_status = {}

        for x in range(PORT_RANGE_START, PORT_RANGE_END + 1):
            self._port_status[x] = True

        self._portforward_lock = Lock()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "K8sProxyController":
        if K8sProxyController._instance is not None:
            return K8sProxyController._instance

        K8sProxyController._instance = K8sProxyController()

        return K8sProxyController._instance

    @staticmethod
    def instance() -> "K8sProxyController":
        return K8sProxyController._instance

    def start_proxy(self, model_id: str, request_id: str) -> K8sProxy:
        _proxy_id = f"{model_id}/{request_id}"

        if _proxy_id in self._proxies:
            return self._proxies[_proxy_id]

        try:
            port_used = 0
            self._portforward_lock.acquire()

            for port, status in self._port_status.items():
                if not status:
                    continue

                port_used = port
                break

            proxy_process = K8sController.instance().portforward(
                model_id, request_id, port_used
            )

            if proxy_process is None:
                raise Exception("Port forward failed for [%s]" % _proxy_id)

            proxy = K8sProxy(model_id, request_id, port_used, proxy_process)
            self._proxies[_proxy_id] = proxy
            self._port_status[port_used] = False

            return proxy
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to get k8s proxy, error = [%s]" % repr(exc_info()),
            )
            traceback.print_exc(file=stdout)

            return None
        finally:
            self._portforward_lock.release()

    def remove_proxy(self, model_id: str, request_id: str):
        _proxy_id = f"{model_id}/{request_id}"

        if _proxy_id not in self._proxies or self._proxies[_proxy_id] is None:
            return

        proxy = self._proxies[_proxy_id]

        try:
            self._portforward_lock.acquire()

            proxy.process.terminate()
            del self._proxies[_proxy_id]
            self._port_status[proxy.port] = True
        except:
            ContextLogger.error(
                self._logger_key, "Failed to remove proxy for [%s]" % _proxy_id
            )
            traceback.print_exc(file=stdout)
        finally:
            self._portforward_lock.release()
