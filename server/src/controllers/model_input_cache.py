from hashlib import md5
from sys import exc_info

from python_framework.config_utils import load_environment_variable
from python_framework.db.transaction_manager import TransactionManager
from python_framework.logger import ContextLogger, LogLevel

from src.config.application_config import ApplicationConfig
from src.db.daos.model_input_cache import ModelInputCacheDAO, ModelInputCacheRecord


class ModelInputCache:
    _instance: "ModelInputCache" = None

    _logger_key: str = None

    def __init__(self) -> None:
        self._logger_key = "ModelInputCache"

        ContextLogger.instance().create_logger_for_context(
            self._logger_key,
            LogLevel.from_string(
                load_environment_variable(
                    f"LOG_LEVEL_{self._logger_key}", default=LogLevel.INFO.name
                )
            ),
        )

    @staticmethod
    def initialize() -> "ModelInputCache":
        if ModelInputCache._instance is not None:
            return ModelInputCache._instance

        ModelInputCache._instance = ModelInputCache()

        return ModelInputCache._instance

    @staticmethod
    def instance() -> "ModelInputCache":
        return ModelInputCache._instance

    # TODO: eventually improve the caching process by adding to a queue and/or batching the inserts
    def cache_model_results(
        self,
        model_id: str,
        inputs: list[str],
        results: list[str],
        user_id: str | None = None,
    ) -> bool:
        try:
            with TransactionManager(
                ApplicationConfig.instance().database_config
            ) as conn:
                for i in range(len(inputs)):
                    try:
                        _ = ModelInputCacheDAO.execute_insert(
                            connection=conn,
                            modelid=model_id,
                            inputhash=md5(inputs[i].encode()).hexdigest(),
                            result=results[i],
                            input=inputs[i],
                            userid=user_id,
                        )
                    except:
                        # NOTE: allow single failures
                        ContextLogger.warn(
                            self._logger_key,
                            f"Failed to persist modelcacherecord for model_id = [{model_id}], reason = {exc_info()!r}",
                        )
        except:
            ContextLogger.error(
                self._logger_key,
                f"Failed to persist modelcacherecords for model_id = [{model_id}], reason = {exc_info()!r}",
            )

            return False

        return True

    def lookup_model_results(
        self, model_id: str, inputs: list[str], result_only: bool = True
    ) -> list[ModelInputCacheRecord]:
        inputs_map: dict[str, str] = dict(
            list(map(lambda input: (md5(input.encode()).hexdigest(), input), inputs))
        )

        records: list[ModelInputCacheRecord] = ModelInputCacheDAO.execute_select_all(
            ApplicationConfig.instance().database_config,
            model_id=model_id,
            input_hashes=list(inputs_map.keys()),
            result_only=result_only,
        )

        if result_only:
            # hydrate the "input" field, using the matching hash
            for record in records:
                record.input = inputs_map.get(record.input_hash)

        return records
