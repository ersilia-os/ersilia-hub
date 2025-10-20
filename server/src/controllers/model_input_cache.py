import traceback
from hashlib import md5
from json import dumps, loads
from sys import exc_info, stdout
from typing import Any

from config.application_config import ApplicationConfig
from db.daos.model_input_cache import ModelInputCacheDAO, ModelInputCacheRecord
from db.daos.work_request_result_cache_temp import (
    WorkRequestResultCacheTempDAO,
    WorkRequestResultCacheTempRecord,
)
from python_framework.config_utils import load_environment_variable
from python_framework.db.transaction_manager import TransactionManager
from python_framework.logger import ContextLogger, LogLevel


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
        results: list[dict[str, Any]],
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
                            model_id=model_id,
                            input_hash=md5(inputs[i].encode()).hexdigest(),
                            result=dumps(results[i]),
                            input=inputs[i],
                            user_id=user_id,
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
        self,
        model_id: str,
        inputs: list[str],
        result_only: bool = True,
        max_batch_size: int = 1000,
    ) -> list[ModelInputCacheRecord]:
        records: list[ModelInputCacheRecord] = []
        batch_count = 0
        current_batch_index = 0

        while True:
            batch_size = min(
                (batch_count + 1) * max_batch_size, len(inputs) - current_batch_index
            )
            inputs_map: dict[str, str] = dict(
                list(
                    map(
                        lambda input: (md5(input.encode()).hexdigest(), input),
                        inputs[current_batch_index : current_batch_index + batch_size],
                    )
                )
            )

            batch_records: list[ModelInputCacheRecord] = (
                ModelInputCacheDAO.execute_select_all(
                    ApplicationConfig.instance().database_config,
                    model_id=model_id,
                    input_hashes=list(inputs_map.keys()),
                    result_only=result_only,
                )
            )

            if result_only:
                # hydrate the "input" field, using the matching hash
                for record in batch_records:
                    record.input = inputs_map.get(record.input_hash)

            records.extend(batch_records)

            if batch_size < max_batch_size:
                break

            batch_count += 1
            current_batch_index += batch_size

        return records

    def persist_cached_workrequest_results(
        self,
        work_request_id: int,
        cached_results: list[ModelInputCacheRecord],
    ) -> bool:
        try:
            with TransactionManager(
                ApplicationConfig.instance().database_config
            ) as conn:
                for record in cached_results:
                    try:
                        _ = WorkRequestResultCacheTempDAO.execute_insert(
                            connection=conn,
                            work_request_id=work_request_id,
                            input_hash=record.input_hash,
                            result=record.result,
                            input=record.input,
                        )
                    except:
                        raise Exception(
                            f"Failed to persist WorkRequestResultCacheTemp record for request_id = [{work_request_id}], reason = {exc_info()!r}"
                        )
        except:
            ContextLogger.error(
                self._logger_key,
                f"Failed to persist WorkRequestResultCacheTemp record for request_id = [{work_request_id}], reason = {exc_info()!r}",
            )
            traceback.print_exc(file=stdout)

            return False

        return True

    def load_work_request_cached_results(
        self, work_request_id: int
    ) -> list[WorkRequestResultCacheTempRecord]:
        try:
            records: list[WorkRequestResultCacheTempRecord] = []
            batch_size = 1000
            batch_offset = 0

            while True:
                batch_records = WorkRequestResultCacheTempDAO.execute_select_all(
                    ApplicationConfig.instance().database_config,
                    work_request_id=work_request_id,
                    batch_size=batch_size,
                    batch_offset=batch_offset,
                )

                if batch_records is None or len(batch_records) == 0:
                    break

                records.extend(batch_records)

                if len(batch_records) < batch_size:
                    break

                batch_offset += batch_size

            return records
        except:
            raise Exception(
                f"Failed to load persisted workrequest results cache for [{work_request_id}], error = [{exc_info()!r}]"
            )

    def clear_work_request_cached_results(self, work_request_id: int):
        try:
            deleted = WorkRequestResultCacheTempDAO.execute_delete(
                ApplicationConfig.instance().database_config,
                work_request_id=work_request_id,
            )
        except:
            raise Exception(
                f"Failed to clear persisted workrequest results cache for [{work_request_id}], error = [{exc_info()!r}]"
            )

    def consolidate_results(
        self,
        ordered_inputs: list[str],
        job_inputs: list[str],
        job_results: list[dict[str, Any]],
        cached_results: list[WorkRequestResultCacheTempRecord]
        | list[ModelInputCacheRecord],
    ) -> list[dict[str, Any] | None]:
        consolidated_results: dict[str, dict[str, Any] | None] = dict(
            map(lambda input: (input, None), ordered_inputs)
        )

        ContextLogger.debug(
            self._logger_key,
            "Consolidating [%d] cached results with [%d] processed results..."
            % (len(cached_results), len(job_results)),
        )

        # set job results in final_results map
        for i in range(len(job_inputs)):
            if job_inputs[i] in consolidated_results:
                consolidated_results[job_inputs[i]] = job_results[i]

        for result in cached_results:
            if result.input in consolidated_results:
                consolidated_results[result.input] = loads(result.result)

        return list(map(lambda input: consolidated_results[input], ordered_inputs))

    def hydrate_job_result_with_cached_results(
        self,
        work_request_id: int,
        work_request_ordered_inputs: list[str],
        job_inputs: list[str],
        job_results: list[dict[str, Any]],
    ) -> list[dict[str, Any] | None]:
        cached_results = self.load_work_request_cached_results(work_request_id)

        ContextLogger.debug(
            self._logger_key,
            "Loaded [%d] cached results for workrequest [%d]"
            % (len(cached_results), work_request_id),
        )

        return self.consolidate_results(
            work_request_ordered_inputs, job_inputs, job_results, cached_results
        )
