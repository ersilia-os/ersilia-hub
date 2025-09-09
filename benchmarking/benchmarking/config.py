from typing import Any, override


class BenchmarkModelConfig:

    id: str
    model_id: str
    total_jobs: int
    input_size: int | None
    input_file_path: str | None

    def __init__(self, model_id: str, total_jobs: int,
        input_size: int | None = None,
        input_file_path: str | None = None
    ) -> None:
        self.model_id = model_id
        self.total_jobs = total_jobs
        self.input_size = input_size
        self.input_file_path = input_file_path

        if input_size is not None:
            self.id = f"{model_id}_{input_size}"
        elif input_file_path is not None:
            self.id = f"{model_id}_{input_file_path}"
        else:
            self.id = model_id

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
        out = f"(model_id = '{self.model_id}', total_jobs = {self.total_jobs}"

        if self.input_size is not None:
            out += f", input_size = {self.input_size}"

        if self.input_file_path is not None:
            out += f", input_file_path = '{self.input_file_path}"

        out += ")"

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

