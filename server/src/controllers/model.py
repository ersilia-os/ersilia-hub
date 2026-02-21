import traceback
from sys import exc_info, stdout
from threading import Event, Lock, Thread
from typing import Any, Dict, List, Union

from config.application_config import ApplicationConfig
from controllers.k8s import K8sController
from db.daos.model import ModelDAO, ModelRecord
from objects.model import (
    Model,
    ModelIdentificationDetails,
    ModelScalingInfo,
    ModelUpdate,
)
from python_framework.config_utils import load_environment_variable
from python_framework.graceful_killer import GracefulKiller, KillInstance
from python_framework.logger import ContextLogger, LogLevel
from python_framework.thread_safe_cache import ThreadSafeCache
from requests import get, post
from sqlalchemy.engine.base import Connection


class ModelControllerKillInstance(KillInstance):
    def kill(self):
        ModelController.instance().kill()


class ModelController(Thread):
    _instance: "ModelController" = None

    UPDATE_WAIT_TIME = 30

    _logger_key: str = None
    _kill_event: Event

    _models_cache: ThreadSafeCache[str, Model]
    _models_cache_update_lock: Lock
    _models_scaling_info: ThreadSafeCache[str, ModelScalingInfo]
    _models_scaling_info_update_lock: Lock

    _model_hub_records_url: str
    _model_hub_details_base_url: str
    _ersilia_catalog_models_url: str

    def __init__(self):
        Thread.__init__(self)

        self._logger_key = "ModelController"
        self._kill_event = Event()

        self._models_cache = ThreadSafeCache()
        self._models_cache_update_lock = Lock()
        self._models_scaling_info = ThreadSafeCache()
        self._models_scaling_info_update_lock = Lock()

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

        self._model_hub_records_url = load_environment_variable(
            "MODEL_HUB_RECORDS_URL", error_on_none=False
        )
        self._model_hub_details_base_url = load_environment_variable(
            "MODEL_HUB_DETAILS_BASE_URL", error_on_none=False
        )
        self._ersilia_catalog_models_url = load_environment_variable(
            "ERSILIA_CATALOG_MODELS_URL", error_on_none=True
        )

    @staticmethod
    def initialize() -> "ModelController":
        if ModelController._instance is not None:
            return ModelController._instance

        ModelController._instance = ModelController()
        GracefulKiller.instance().register_kill_instance(ModelControllerKillInstance())

        return ModelController._instance

    @staticmethod
    def instance() -> "ModelController":
        return ModelController._instance

    def _wait_or_kill(self, timeout: float) -> bool:
        return self._kill_event.wait(timeout)

    def kill(self):
        self._kill_event.set()

    def _update_models_cache(self, models: Dict[str, Model]) -> bool:
        try:
            self._models_cache_update_lock.acquire()

            new_cache = ThreadSafeCache(models)
            self._models_cache = new_cache
        except:
            error_str = "Failed to update models cache, error = [%s]" % repr(exc_info())
            ContextLogger.error(self._logger_key, error_str)

            return False
        finally:
            self._models_cache_update_lock.release()

        return True

    def _update_models_scaling_info(
        self, models_scaling_info: Dict[str, ModelScalingInfo]
    ):
        try:
            self._models_scaling_info_update_lock.acquire()

            new_cache = ThreadSafeCache(models_scaling_info)
            self._models_scaling_info = new_cache
        except:
            error_str = "Failed to update models cache, error = [%s]" % repr(exc_info())
            ContextLogger.error(self._logger_key, error_str)

            return False
        finally:
            self._models_scaling_info_update_lock.release()

        return True

    def _load_persisted_models(self) -> Dict[str, Model]:
        ContextLogger.debug(self._logger_key, "Loading models from DB...")
        results: List[ModelRecord] = ModelDAO.execute_select_all(
            ApplicationConfig.instance().database_config,
        )
        ContextLogger.debug(self._logger_key, "Models loaded from DB.")

        return dict(
            map(
                lambda model: (model.id, model),
                map(lambda record: Model.init_from_record(record), results),
            )
        )

    def _load_model_scaling_info(self) -> Dict[str, ModelScalingInfo]:
        ContextLogger.debug(self._logger_key, "Loading model scaling info from k8s...")

        scaling_info = {}

        for model in self._models_cache.values():
            instance_count = 0

            try:
                current_instances = K8sController.instance().load_model_pods(model.id)
                instance_count = len(current_instances)
            except:
                ContextLogger.warn(
                    self._logger_key,
                    "Failed to get instance count for model [%s], error = [%s]"
                    % (model.id, repr(exc_info())),
                )

            scaling_info[model.id] = ModelScalingInfo(
                True, instance_count, model.details.max_instances
            )

        ContextLogger.debug(self._logger_key, "Model scaling info loaded from k8s.")

        return scaling_info

    def _update_models_state(self) -> List[Model]:
        """1. Load persisted (db) models
        2. Update scaling info cache locally

        returns the persisted models list
        """
        persisted_models = self._load_persisted_models()

        self._update_models_cache(persisted_models)
        self._update_models_scaling_info(self._load_model_scaling_info())

        return persisted_models

    def model_exists(self, model_id: str) -> bool:
        return model_id in self._models_cache

    def get_models(self) -> List[Model]:
        return list(self._models_cache.values())

    def get_model(self, model_id: str) -> Union[Model, None]:
        return self._models_cache[model_id] if model_id in self._models_cache else None

    def get_models_scaling_info(self) -> Dict[str, ModelScalingInfo]:
        return dict(self._models_scaling_info)

    def get_model_scaling_info(self, model_id: str) -> Union[ModelScalingInfo, None]:
        return (
            self._models_scaling_info[model_id]
            if model_id in self._models_scaling_info
            else None
        )

    def _upsert_model(
        self,
        model: Model,
        connection: Union[Connection, None] = None,
    ) -> Union[Model, None]:
        try:
            results: List[ModelRecord] = None

            if model.last_updated is None:
                ContextLogger.debug(
                    self._logger_key, "Inserting NEW model with id [%s]" % model.id
                )
                results: List[ModelRecord] = ModelDAO.execute_insert(
                    ApplicationConfig.instance().database_config,
                    connection=connection,
                    **model.to_record().generate_insert_query_args(),
                )
            else:
                ContextLogger.debug(
                    self._logger_key,
                    "Updating EXISTING model with id [%s]" % model.id,
                )
                results: List[ModelRecord] = ModelDAO.execute_update(
                    ApplicationConfig.instance().database_config,
                    connection=connection,
                    **model.to_record().generate_update_query_args(),
                )

            if results is None or len(results) == 0:
                raise Exception("Insert/update returned zero records]")

            return Model.init_from_record(results[0])
        except:
            error_str = "Failed to persist model with id = [%s], error = [%s]" % (
                model.id,
                repr(exc_info()),
            )
            ContextLogger.error(self._logger_key, error_str)
            traceback.print_exc(file=stdout)

        return None

    def update_model(self, model_update: ModelUpdate) -> Union[Model, None]:
        if model_update.id not in self._models_cache:
            ContextLogger.warn(
                self._logger_key,
                "Update failed: No model found with id = [%s]" % model_update.id,
            )
            return None

        _new_model = self._models_cache[model_update.id].copy()
        _new_model.apply_update(model_update)

        persisted_model = self._upsert_model(_new_model)

        if persisted_model is not None:
            self._models_cache[persisted_model.id] = persisted_model

        return persisted_model

    def create_model(self, model: Model) -> Union[Model, None]:
        if model.id in self._models_cache:
            ContextLogger.error(
                self._logger_key, "Model with id [%s] already exists" % model.id
            )
            return None

        persisted_model = self._upsert_model(model)

        if persisted_model is not None:
            self._models_cache[persisted_model.id] = persisted_model

        return persisted_model

    def get_details_from_ersilia_catalog(
        self, model_id: str
    ) -> ModelIdentificationDetails | None:
        ContextLogger.debug(
            self._logger_key,
            f"Getting Ersilia Catalog model records using url = [{self._ersilia_catalog_models_url}], model_id = [{model_id}]...",
        )

        response = get(url=self._ersilia_catalog_models_url)
        response.raise_for_status()

        model_records: list[dict[str, Any]] | None = response.json()
        model_record: dict[str, Any] | None = None

        for record in model_records:
            if "Identifier" in record and record["Identifier"] == model_id:
                model_record = record
                break

        if model_record is None:
            raise Exception(
                f"Failed to find model [{model_id}] in Ersilia Catalog response"
            )

        model_identification_details = ModelIdentificationDetails()

        if "Description" in model_record:
            model_identification_details.description = model_record["Description"]

        if "Title" in model_record:
            model_identification_details.title = model_record["Title"]

        if "Slug" in model_record:
            model_identification_details.slug = model_record["Slug"]

        if "Interpretation" in model_record:
            model_identification_details.interpretation = model_record["Interpretation"]

        if "Publication" in model_record:
            model_identification_details.publication = model_record["Publication"]

        if "GitHub" in model_record:
            model_identification_details.source_code = model_record["GitHub"]

        if "Target Organism" in model_record:
            model_identification_details.target_organisms = model_record[
                "Target Organism"
            ]

        if "Biomedical Area" in model_record:
            model_identification_details.biomedical_areas = model_record[
                "Biomedical Area"
            ]

        return model_identification_details

    def get_details_from_model_hub(
        self, model_id: str
    ) -> ModelIdentificationDetails | None:
        if (
            self._model_hub_details_base_url is None
            or self._model_hub_records_url is None
        ):
            ContextLogger.warn(
                self._logger_key, "Model Hub model details not configured"
            )
            return None

        ContextLogger.debug(
            self._logger_key,
            f"Getting ModelHub records using url = [{self._model_hub_records_url}], model_id = [{model_id}]...",
        )

        response = post(
            url=self._model_hub_records_url,
            json={
                "options": {
                    "cellFormat": "string",
                    "timeZone": "UTC",
                    "userLocale": "en-US",
                },
                "pageContext": None,
                "filterCriteria": {
                    "filterConditionGroup": {
                        "logicalOperator": "AND",
                        "filterGroups": [
                            {
                                "logicalOperator": "OR",
                                "filters": [
                                    {
                                        "subject": "Identifier",
                                        "operator": "CONTAINS",
                                        "value": model_id,
                                    }
                                ],
                            }
                        ],
                    }
                },
                "pagingOption": {"offset": None, "count": 6},
            },
        )

        response.raise_for_status()
        model_records: dict[str, Any] | None = response.json()

        ContextLogger.debug(self._logger_key, f"ModelHub records = [{model_records}]")

        if (
            model_records is None
            or "records" not in model_records
            or model_records["records"] is None
            or len(model_records["records"]) == 0
        ):
            return None

        model_hub_id: str | None = None

        for record in model_records["records"]:
            if (
                "fields" not in record
                or record["fields"] is None
                or "Identifier" not in record["fields"]
            ):
                continue

            if record["fields"]["Identifier"] == model_id:
                if "id" not in record:
                    raise Exception("ModelHub record found but no 'id' field present")

                model_hub_id = record["id"]
                break

        if model_hub_id is None:
            return None

        ContextLogger.debug(
            self._logger_key,
            f"Getting ModelHub details using url = [{self._model_hub_details_base_url}/{model_hub_id}], model_id = [{model_id}]...",
        )
        response = post(
            url=f"{self._model_hub_details_base_url}/{model_hub_id}",
            json={
                "options": {
                    "cellFormat": "string",
                    "timeZone": "UTC",
                    "userLocale": "en-US",
                },
                "pageContext": None,
                "filterCriteria": {},
            },
        )

        response.raise_for_status()
        model_records: dict[str, Any] | None = response.json()

        ContextLogger.debug(self._logger_key, f"ModelHub records = [{model_records}]")

        if (
            model_records is None
            or "records" not in model_records
            or model_records["records"] is None
            or len(model_records["records"]) == 0
        ):
            return None

        model_record: dict[str, Any] = model_records["records"][0]

        if (
            model_record is None
            or "fields" not in model_record
            or model_record["fields"] is None
        ):
            raise Exception("ModelHub record found, but no 'fields' present")

        model_identification_details = ModelIdentificationDetails()

        if "Description" in model_record["fields"]:
            model_identification_details.description = model_record["fields"][
                "Description"
            ]

        if "Title" in model_record["fields"]:
            model_identification_details.title = model_record["fields"]["Title"]

        if "Slug" in model_record["fields"]:
            model_identification_details.slug = model_record["fields"]["Slug"]

        if "Interpretation" in model_record["fields"]:
            model_identification_details.interpretation = model_record["fields"][
                "Interpretation"
            ]

        if "Publication" in model_record["fields"]:
            model_identification_details.publication = model_record["fields"][
                "Publication"
            ]

        if "GitHub" in model_record["fields"]:
            model_identification_details.source_code = model_record["fields"]["GitHub"]

        if "Target Organism" in model_record["fields"]:
            model_identification_details.target_organisms = (
                []
                if len(model_record["fields"]["Target Organism"]) == 0
                else list(
                    map(
                        lambda x: x.strip(),
                        model_record["fields"]["Target Organism"].split(","),
                    )
                )
            )

        if "Biomedical Area" in model_record["fields"]:
            model_identification_details.biomedical_areas = (
                []
                if len(model_record["fields"]["Biomedical Area"]) == 0
                else list(
                    map(
                        lambda x: x.strip(),
                        model_record["fields"]["Biomedical Area"].split(","),
                    )
                )
            )

        return model_identification_details

    def run(self):
        ContextLogger.info(self._logger_key, "Controller started")

        while True:
            try:
                self._update_models_state()
            except:
                error_str = "Failed to update models state, error = [%s]" % (
                    repr(exc_info()),
                )
                ContextLogger.error(self._logger_key, error_str)
                traceback.print_exc(file=stdout)

            if self._wait_or_kill(ModelController.UPDATE_WAIT_TIME):
                break

        ContextLogger.info(self._logger_key, "Controller stopped")
