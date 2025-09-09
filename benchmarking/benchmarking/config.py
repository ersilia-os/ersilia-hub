from typing import Any, override

BENCHMARK_INPUTS_PATH = "./inputs"

class BenchmarkModelConfig:

    id: str
    model_id: str
    total_jobs: int
    file_path: str

    def __init__(self, model_id: str, total_jobs: int,
        input_size: int | None = None,
        input_file_path: str | None = None
    ) -> None:
        self.model_id = model_id
        self.total_jobs = total_jobs

        if input_size is not None:
            self.id = f"{model_id}_{input_size}"
            self.file_path = f"{BENCHMARK_INPUTS_PATH}/{model_id}/{input_size}.csv"
        elif input_file_path is not None:
            self.id = f"{model_id}_{input_file_path}"
            self.file_path = input_file_path
        else:
            raise Exception("Required one of 'input_size' or 'input_file_path'")

    @staticmethod
    def from_json(obj: dict[str, Any]) -> "BenchmarkModelConfig":
        return BenchmarkModelConfig(
            model_id=obj["modelId"],
            total_jobs=obj["totalJobs"],
            input_size=None if "inputSize" not in obj else obj["inputSize"],
            input_file_path=None if "inputFilePath" not in obj else obj["inputFilePath"],
        )

    @override
    def __str__(self) -> str:
        out = f"(model_id = '{self.model_id}', total_jobs = {self.total_jobs}, file_path = '{self.file_path}')"

        return out

    @override
    def __repr__(self) -> str:
        return self.__str__()

class BenchmarkConfig:

    model_configs: list[BenchmarkModelConfig]
    results_file_path: str
    max_processes: int = 50

    def __init__(self, model_configs: list[BenchmarkModelConfig], results_file_path: str, max_processes: int = 50) -> None:
        self.model_configs = model_configs
        self.results_file_path = results_file_path
        self.max_processes = max_processes

    @staticmethod
    def from_json(obj: dict[str, Any]) -> "BenchmarkConfig":
        return BenchmarkConfig(
            list(map(BenchmarkModelConfig.from_json, obj["modelConfigs"])),
            obj["resultsFilePath"],
            50 if "maxProcesses" not in obj else int(obj["maxProcesses"])
        )

    @override
    def __str__(self) -> str:
        out = f"(results_file_path = '{self.results_file_path}', max_processes = {self.max_processes}, model_configs = ["
        out += ", ".join(list(map(lambda x: str(x), self.model_configs)))
        out += "])"

        return out

    @override
    def __repr__(self) -> str:
        return self.__str__()

