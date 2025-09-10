

# TODO: check previous sub-process implementations

###
# The design of the processing is essentially to have ONE process per model job submission.
# The "main" process orchestrates the model submission processes by round-robin execution by model, until each model's submission count is reached
##

from subprocess import PIPE, Popen
from sys import exc_info
from typing import IO
from benchmarking.benchmarking.config import BenchmarkConfig, BenchmarkModelConfig

        
class ModelJobProcess:
    """
    Subprocess for submitting a model job and waiting for the result
    """

    config: BenchmarkModelConfig
    result: tuple[bool, str|None, str|None] | None # success, work_request_id, reason
    process: Popen[bytes] | None

    def __init__(self, config: BenchmarkModelConfig) -> None:
        self.config = config
        self.result = None
        self.process = None

    def stop(self) -> bool:
        if self.process is None:
            return False

        self.process.kill()

        return True

    def check_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def get_result(self) -> tuple[bool, str|None, str|None]:
        if self.result is not None:
            return self.result

        if self.process is None:
            return False, None, "Process not started"
        elif self.process.poll() is None:
            return False, None, "Process still busy"
        elif self.process.returncode != 0:
            return False, None, f"Process exited with non-zero code: [{self.process.returncode}]"

        process_stdout: list[str] | None = None
        p_stdout: IO[bytes] | None = self.process.stdout

        try:
            if p_stdout is not None:
                process_stdout = list(map(lambda b: b.decode(), p_stdout.readlines()))
        except:
            return True, None, f"Failed to read process result from stdout: [{repr(exc_info())}]"

        if process_stdout is None or len(process_stdout) == 0:
            return True, None, "Process succeeded, but missing result output"

        _result = process_stdout[-1].strip().split("##")

        self.result = bool(_result[0]), None if len(_result[1]) == 0 else _result[1], None if len(_result[2]) == 0 else _result[2]

        try:
            if p_stdout is not None:
                p_stdout.close()
        except:
            pass

        return self.result

    def run(self):
        if self.process is not None:
            return

        self.process = Popen([
            "python3",
            "./benchmarking/work_request.py",
            self.config.model_id,
            self.config.file_path
        ], stdout=PIPE)
        

class ModelProcessHandler:

    config: BenchmarkModelConfig
    job_count: int
    results: list[tuple[bool, str|None, str|None]]

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
        process.run()

        return process

    def check_process(self, process: ModelJobProcess) -> bool: # completed
        # NOTE: we should add a lock here if we make the "main" thread concurrent

        if process.check_running():
            return False

        self.job_count += 1
        self.results.append(process.get_result())

        return True

    def stop_process(self, process: ModelJobProcess):
        try:
            _ = process.stop()
        except:
            pass

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

