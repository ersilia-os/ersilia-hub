from sys import exc_info, stdout
from threading import Event, Thread
import traceback
from typing import List
from python_framework.thread_safe_list import ThreadSafeList
from python_framework.logger import ContextLogger, LogLevel
from python_framework.config_utils import load_environment_variable
from library.process_lock import ProcessLock
from string import ascii_lowercase
from random import choices

from controllers.k8s import K8sController
from controllers.model import ModelController
from objects.k8s import ErsiliaAnnotations, K8sPod


class ScalingWorker(Thread):

    SCALE_DOWN_WAIT_TIME = 20  # TODO: make config + increase default
    LOCK_TIMEOUT = 10

    _logger_key: str = None
    _kill_event: Event
    _process_lock: ProcessLock

    id: str
    model_ids: ThreadSafeList[str]

    def __init__(self, process_lock: ProcessLock):
        Thread.__init__(self)

        self.id = "".join(choices(ascii_lowercase, k=6))
        self.model_ids = ThreadSafeList

        self._logger_key = "ScalingWorker[%s]" % self.id
        self._kill_event = Event()
        self._process_lock = process_lock

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_ScalingWorker", default=LogLevel.INFO.name
                )
            ),
        )

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def update_model_ids(self, model_ids: List[str]):
        self.model_ids = ThreadSafeList(model_ids)

    def _scale_down_model_instances(
        self,
        model_id: str,
        scale_down_candidates: List[K8sPod],
    ) -> None:
        lock_acquired = False

        try:
            if not self._process_lock.acquire_lock(
                model_id, timeout=ScalingWorker.LOCK_TIMEOUT
            ):
                raise Exception(
                    "Failed to acquire lock on model [%s] within [%d] seconds"
                    % (model_id, ScalingWorker.LOCK_TIMEOUT)
                )

            lock_acquired = True

            ContextLogger.trace(
                self._logger_key,
                "model [%s] scale_down_candidates = [%s]"
                % (model_id, list(map(lambda x: x.name, scale_down_candidates))),
            )

            for candidate in scale_down_candidates:
                try:
                    if not K8sController.instance().delete_pod(
                        model_id, target_pod_name=candidate.name
                    ):
                        ContextLogger.warn(
                            self._logger_key,
                            "Scale down was unsuccessful for model [%s], pod [%s]"
                            % (model_id, candidate.name),
                        )
                        continue

                    ContextLogger.info(
                        self._logger_key,
                        "Model auto-scaled down model [%s], pod [%s]"
                        % (model_id, candidate.name),
                    )
                except:
                    error_str = (
                        "Failed to auto-scale down model [%s], pod [%s], error = [%s]"
                        % (
                            model_id,
                            candidate.name,
                            repr(exc_info()),
                        )
                    )
                    ContextLogger.error(self._logger_key, error_str)
                    traceback.print_exc(file=stdout)
        except:
            ContextLogger.error(
                self._logger_key,
                "Failed to auto-scale down instances for model [%s], error = [%s]"
                % (model_id, repr(exc_info())),
            )
            traceback.print_exc(file=stdout)
        finally:
            if lock_acquired:
                self._process_lock.release_lock(model_id)

    def _auto_scale_down_models(self) -> None:
        ContextLogger.debug(
            self._logger_key, "Model auto-scaled down iteration starting..."
        )

        ContextLogger.trace(self._logger_key, "model ids = [%s]" % self.model_ids)

        for model_id in self.model_ids:
            instances = K8sController.instance().load_model_pods(model_id)

            if len(instances) == 0:
                ContextLogger.debug(
                    self._logger_key, "no instances deployed for model [%s]" % model_id
                )
                continue

            scale_down_candidates: List[K8sPod] = []

            for instance in instances:
                # ignore used instances
                if not instance.annotation_is_null(ErsiliaAnnotations.REQUEST_ID.value):
                    continue

                # ignore terminating instance
                if instance.state.phase.lower() == "terminating":
                    continue

                # TODO: also check instance start time, need to allow startup time of 60s

                scale_down_candidates.append(instance)

            if len(scale_down_candidates) == 0:
                ContextLogger.debug(
                    self._logger_key,
                    "no scale down candidates found for model [%s]" % model_id,
                )
                continue

            self._scale_down_model_instances(model_id, scale_down_candidates)

        ContextLogger.debug(
            self._logger_key, "Model auto-scaled down iteration completed."
        )

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        while True:
            if self._wait_or_kill(ScalingWorker.SCALE_DOWN_WAIT_TIME):
                break

            try:
                self._auto_scale_down_models()
            except:
                error_str = "Failed to auto scale down, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

        ContextLogger.info(self._logger_key, "Controller stopped")
