

from json import load
from sys import argv

from benchmarking.benchmarking.config import BenchmarkConfig
from benchmarking.benchmarking.process import BenchmarkProcess


if __name__ == '__main__':
    config: BenchmarkConfig | None = None

    with open(argv[1], 'r') as file:
        config = BenchmarkConfig.from_json(load(file))

    process = BenchmarkProcess(config)
    process.run()

