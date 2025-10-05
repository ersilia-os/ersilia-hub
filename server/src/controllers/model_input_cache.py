

from src.db.daos.model_input_cache import ModelInputCacheRecord


class ModelInputCache:
    
    def __init__(self) -> None:
        pass

# TODO: singleton stuff + logger stuff

    # TODO: eventually improve the caching process by adding to a queue and/or batching the inserts
    def cache_model_results(self, model_id: str, inputs: list[str], results: list[str]) -> bool:
        # TODO: hash inputs
        # TODO: create transaction
        # TODO: insert records one-by-one (handle exceptions)
        # TODO: commit TX
        # TODO: return True if ALL persisted
        pass

    def lookup_model_results(self, model_id: str, inputs: list[str]) -> list[ModelInputCacheRecord]:
        # TODO: md5 hash the inputs
        # TODO: load batch with "result only" using hashes
        # TODO: on result, hydrate the "input" field, using the matching hash
        # TODO: return list
        pass

