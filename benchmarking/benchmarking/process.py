

# TODO: check previous sub-process implementations

###
# The design of the processing is essentially to have ONE process per model job submission.
# The "main" process orchestrates the model submission processes by round-robin execution by model, until each model's submission count is reached
##

from benchmarking.benchmarking.config import BenchmarkConfig, BenchmarkModelConfig

        
class ModelJobProcess:
    """
    Subprocess for submitting a model job and waiting for the result
    """

    # TODO: extend process / Popen, or something

    config: BenchmarkModelConfig
    result: tuple[bool, str|None, str] # success, work_request_id, reason

    def __init__(self, config: BenchmarkModelConfig) -> None:
        self.config = config
        self.result = (False, None, "Not started")

    def run(self):
        pass

class ModelProcessHandler:

    config: BenchmarkModelConfig
    job_count: int
    results: list[tuple[bool, str|None, str]]

    def __init__(self, config: BenchmarkModelConfig) -> None:
        self.config = config
        self.job_count = 0
        self.results = []

    def limit_reached(self) -> bool:
        return self.job_count >= self.config.total_jobs

    def new_process(self) -> None | ModelJobProcess:
        if self.limit_reached():
            return None

        process = ModelJobProcess(self.config)
        # TODO: run the process here

        return process

    def job_completed(self, process: ModelJobProcess):
        # NOTE: we should add a lock here if we make the "main" thread concurrent
        self.job_count += 1
        self.results.append(process.result)

class BenchmarkProcess:
    """
    1. initialize Model Process objects in a dict
    2. round robin between process objects, spawning new job process if it has NOT reached the job_limit.
    3. keep track of in-progress processes
    4. on completion, write results to file
    """
    
    config: BenchmarkConfig
    model_process_handlers: dict[str, ModelProcessHandler]
    ordered_handlers: list[str]
    active_job_processes: list[ModelJobProcess]
    _current_round_robin_index: int

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self.model_process_handlers = {}
        self.ordered_handlers = []

        for model_config in config.model_configs:
            self.model_process_handlers[model_config.id] = ModelProcessHandler(model_config)
            self.ordered_handlers.append(model_config.id)

        self.active_job_processes = []
        self._current_round_robin_index = 0

    def submit_next_job(self) -> tuple[bool, bool, str]: # success, should_exit, reason
        pass

    def run(self):
        pass

