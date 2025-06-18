from sys import exc_info, stdout
import traceback
from typing import List, Tuple, Union
from time import sleep, time

from requests import get, post
from objects.model_integration import (
    JobResult,
    JobStatus,
    JobStatusResponse,
    JobSubmissionRequest,
    JobSubmissionResponse,
)
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable

from controllers.k8s_proxy import K8sProxy, K8sProxyController


class ModelIntegrationController:

    _instance: "ModelIntegrationController" = None

    _logger_key: str = None
    _model_port: int
    _request_timeout: float
    _proxy_ids: List[str]

    def __init__(
        self,
        model_port: int,
        request_timeout: float,
        proxy_ids: Union[str, List[str]] = None,
    ):
        self._logger_key = "ModelIntegrationController"
        self._model_port = model_port
        self._request_timeout = request_timeout

        if proxy_ids is None:
            self._proxy_ids = []
        elif type(proxy_ids) == "str":
            self._proxy_ids = [] if len(self._proxy_ids) == 0 else proxy_ids.split(",")
        else:
            self._proxy_ids = proxy_ids

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "ModelIntegrationController":
        if ModelIntegrationController._instance is not None:
            return ModelIntegrationController._instance

        ModelIntegrationController._instance = ModelIntegrationController(
            int(load_environment_variable(f"MODEL_INTEGRATION_PORT", default="80")),
            float(
                load_environment_variable(f"MODEL_INTEGRATION_TIMEOUT", default="10")
            ),
            load_environment_variable("MODEL_INTEGRATION_PROXY_IDS"),
        )

        return ModelIntegrationController._instance

    @staticmethod
    def instance() -> "ModelIntegrationController":
        return ModelIntegrationController._instance

    def _get_proxy(self, model_id: str, request_id: str) -> K8sProxy:
        ContextLogger.trace(
            self._logger_key,
            "proxying requests for model [%s], request_id = [%s]"
            % (model_id, request_id),
        )

        return K8sProxyController.instance().start_proxy(model_id, request_id)

    def _proxied_host_and_port(
        self, model_id: str, request_id: str, host: str, port: int
    ) -> Tuple[str, int]:
        if model_id in self._proxy_ids:
            proxy = self._get_proxy(model_id, request_id)

            if proxy is None:
                raise Exception("Failed to proxy request")

            return proxy.host, proxy.port
        else:
            return host, port

    def healthz(self, model_id: str, request_id: str, host: str) -> bool:
        ContextLogger.debug(
            self._logger_key,
            "Checking model health for model [%s], request_id [%s] using host = [%s]..."
            % (model_id, request_id, host),
        )

        _host, _port = self._proxied_host_and_port(
            model_id, request_id, host, self._model_port
        )

        try:
            response = get(
                url=f"http://{_host}:{_port}/healthz",
                timeout=self._request_timeout,
            )

            if response.status_code < 200 or response.status_code >= 300:
                ContextLogger.warn(
                    self._logger_key,
                    "Model health response = [%d] for model [%s], request_id [%s] using host = [%s]..."
                    % (response.status_code, model_id, request_id, host),
                )
                return False

            return True
        except:
            ContextLogger.error(
                ModelIntegrationController.instance()._logger_key,
                "Failed to retrieve instance health for model [%s], request_id [%s] using host = [%s], error = [%s]"
                % (model_id, request_id, _host, repr(exc_info())),
            )

            return False

    def wait_for_model_readiness(
        self, model_id: str, request_id: str, host: str, timeout: float = 60
    ) -> bool:
        ContextLogger.debug(
            self._logger_key,
            "checking model readiness for model [%s], request_id [%s]..."
            % (model_id, request_id),
        )
        start_time = time()

        while True:
            try:
                if self.healthz(model_id, request_id, host):
                    ContextLogger.debug(
                        self._logger_key,
                        "model ready - model [%s], request_id [%s]"
                        % (model_id, request_id),
                    )
                    return True
            except:
                pass

            ContextLogger.trace(
                self._logger_key,
                "model not ready yet - model [%s], request_id [%s]"
                % (model_id, request_id),
            )
            sleep(5)

            if time() - start_time >= timeout:
                ContextLogger.warn(
                    self._logger_key,
                    "timeout reached for model readiness - model [%s], request_id [%s]"
                    % (model_id, request_id),
                )
                return False

    def submit_job(
        self, model_id: str, request_id: str, host: str, entries: List[str]
    ) -> JobSubmissionResponse:
        ContextLogger.debug(
            self._logger_key,
            "Submitting job using host = [%s]..." % host,
        )

        if not self.wait_for_model_readiness(model_id, request_id, host):
            error_str = "model failed readiness - model [%s], request_id [%s]" % (
                model_id,
                request_id,
            )
            ContextLogger.error(self._logger_key, error_str)

            raise Exception(error_str)

        _host, _port = self._proxied_host_and_port(
            model_id, request_id, host, self._model_port
        )

        try:
            _url = f"http://{_host}:{_port}/job/submit"
            _request = JobSubmissionRequest.from_entries(entries)
            _json = _request.body
            _params = _request.params

            ContextLogger.trace(
                self._logger_key,
                "submitting job to [%s], body [%s], params [%s]"
                % (_url, _json, _params),
            )

            response = post(
                url=_url,
                json=_json,
                params=_params,
                timeout=self._request_timeout,
            )
            response.raise_for_status()

            ContextLogger.debug(
                ModelIntegrationController.instance()._logger_key,
                "Job successfully submitted to host = [%s]" % _host,
            )

            return JobSubmissionResponse.from_object(response.json())
        except:
            error_str = "Failed to submit job for host = [%s], error = [%s]" % (
                _host,
                repr(exc_info()),
            )
            ContextLogger.error(
                ModelIntegrationController.instance()._logger_key,
                error_str,
            )
            traceback.print_exc(file=stdout)

            raise Exception(error_str)

    def submit_job_sync(
        self, model_id: str, request_id: str, host: str, entries: List[str]
    ) -> Tuple[JobStatus, str, JobResult]:
        ContextLogger.debug(
            self._logger_key,
            "Submitting SYNC job using host = [%s]..." % host,
        )

        if not self.wait_for_model_readiness(model_id, request_id, host):
            error_str = "model failed readiness - model [%s], request_id [%s]" % (
                model_id,
                request_id,
            )
            ContextLogger.error(self._logger_key, error_str)

            raise Exception(error_str)

        _host, _port = self._proxied_host_and_port(
            model_id, request_id, host, self._model_port
        )

        try:
            _url = f"http://{_host}:{_port}/run"
            _request = JobSubmissionRequest(
                entries,
                {
                    "orient": "records",
                    "min_workers": 1,
                    "max_workers": 12,
                    "fetch_cache": True,
                    "save_cache": True,
                    "cache_only": False,
                },
            )
            _json = _request.body
            _params = _request.params

            ContextLogger.trace(
                self._logger_key,
                "submitting SYNC job to [%s], body [%s], params [%s]"
                % (_url, _json, _params),
            )

            response = post(
                url=_url,
                json=_json,
                params=_params,
                timeout=1200,  # 20min timeout
            )
            response.raise_for_status()

            ContextLogger.debug(
                ModelIntegrationController.instance()._logger_key,
                "SYNC Job successfully completed for host = [%s]" % _host,
            )

            return (
                JobStatus.COMPLETED,
                "Job completed",
                response.json(),
            )
        except:
            error_str = "Failed to submit job for host = [%s], error = [%s]" % (
                _host,
                repr(exc_info()),
            )
            ContextLogger.error(
                ModelIntegrationController.instance()._logger_key,
                error_str,
            )
            traceback.print_exc(file=stdout)

            return (
                JobStatus.FAILED,
                "Job submission failed, error = [%s]" % repr(exc_info()),
                None,
            )

    def get_job_status(
        self, model_id: str, request_id: str, host: str, job_id: str
    ) -> JobStatusResponse:
        ContextLogger.debug(
            self._logger_key,
            "Getting job status using host = [%s], job_id = [%s]..." % (host, job_id),
        )

        _host, _port = self._proxied_host_and_port(
            model_id, request_id, host, self._model_port
        )

        try:
            response = get(
                url=f"http://{_host}:{_port}/job/status/{job_id}",
                timeout=self._request_timeout,
            )
            response.raise_for_status()

            return JobStatusResponse.from_object(response.json())
        except:
            error_str = (
                "Failed to retrieve job status for host = [%s], job_id = [%s], error = [%s]"
                % (_host, job_id, repr(exc_info()))
            )
            ContextLogger.error(
                ModelIntegrationController.instance()._logger_key,
                error_str,
            )
            traceback.print_exc(file=stdout)

            raise Exception(error_str)

    def get_job_result(
        self, model_id: str, request_id: str, host: str, job_id: str
    ) -> JobResult:
        ContextLogger.debug(
            self._logger_key,
            "Getting job result using host = [%s], job_id = [%s]..." % (host, job_id),
        )

        _host, _port = self._proxied_host_and_port(
            model_id, request_id, host, self._model_port
        )

        try:
            response = get(
                url=f"http://{_host}:{_port}/job/result/{job_id}",
                timeout=self._request_timeout,
            )
            response.raise_for_status()

            return response.json()
        except:
            error_str = (
                "Failed to retrieve job result for host = [%s], job_id = [%s], error = [%s]"
                % (_host, job_id, repr(exc_info()))
            )
            ContextLogger.error(
                ModelIntegrationController.instance()._logger_key,
                error_str,
            )
            traceback.print_exc(file=stdout)

            raise Exception(error_str)
