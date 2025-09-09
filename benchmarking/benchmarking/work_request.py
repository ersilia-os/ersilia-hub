from base64 import b64encode
from json import dumps
from os.path import exists
from sys import exc_info
from time import sleep, time
from uuid import uuid4
from requests import get, post

API_BASE_URL = "https://hub.ersilia.io"
REQUEST_TIMEOUT = 900  # 15 minutes, in seconds
BENCHMARK_INPUTS_PATH = "./inputs"

def get_auth_header(session_id: str):
    print("Starting anonymous session...")

    try:
        response = post(f"{API_BASE_URL}/api/auth/anonymous-login/{session_id}")

        if response.status_code != 200:
            raise Exception(
                f"HTTP:{response.status_code} - {response.content.decode()}"
            )

        return (
            "ErsiliaAnonymous "
            + b64encode(dumps(response.json()["session"]).encode()).decode()
        )
    except:
        raise Exception(f"Failed to start anonymous session: [{repr(exc_info())}]")


def submit_work_request(auth_header: str, model_id: str, smiles: list[str]) -> str:
    print("Submitting job...")

    try:
        response = post(
            f"{API_BASE_URL}/api/work-requests",
            json={
                "model_id": model_id,
                "request_payload": {"entries": smiles},
            },
            headers={"Authorization": auth_header},
        )

        if response.status_code != 200:
            raise Exception(
                f"HTTP:{response.status_code} - {response.content.decode()}"
            )

        return response.json()["id"]
    except:
        raise Exception(f"Failed to submit job: [{repr(exc_info())}]")


def wait_for_result(auth_header: str, request_id: str) -> None:
    print("Waiting for result...")

    start_time = time()

    while True:
        if start_time + REQUEST_TIMEOUT < time():
            raise Exception("Request Time Out reached")

        try:
            response = get(
                f"{API_BASE_URL}/api/work-requests/{request_id}",
                params={"include_result": True, "csv_result": True},
                headers={"Authorization": auth_header},
            )

            if response.status_code != 200:
                raise Exception(
                    f"HTTP:{response.status_code} - {response.content.decode()}"
                )

            response_json = response.json()

            if response_json["request_status"] == "FAILED":
                raise Exception(f"Job failed: {response_json["request_status_reason"]}")
            elif response_json["request_status"] != "COMPLETED":
                sleep(10)
                continue
        except:
            raise Exception(f"Failed to submit Job: [{repr(exc_info())}]")

def load_smiles_from_file(file_path: str) -> list[str] | None:
    if not exists(file_path):
        raise Exception(f"Filepath [{file_path}] not found")
    
    with open(file_path, "r") as file:
        return file.readlines()

def load_smiles_by_model_and_size(model_id: str, input_size: int) -> list[str] | None:
    return load_smiles_from_file(f"{BENCHMARK_INPUTS_PATH}/{model_id}/{input_size}.csv")

def submit_job(model_id: str, smiles: list[str] | None = None, input_size: int | None = None, input_file_path: str | None = None) -> tuple(bool, str | None, str):
    _smiles: list[str] | None = None

    if smiles is not None:
        _smiles = smiles
    elif input_file_path is not None:
        try:
            _smiles = load_smiles_from_file(input_file_path)
        except:
            return False, None, "Failed to load smiles file: %s" % repr(exc_info())
    elif input_size is not None:
        try:
            _smiles = load_smiles_by_model_and_size(model_id, input_size)
        except:
            return False, None, "Failed to load smiles by id + input: %s" % repr(exc_info())

    if _smiles is None or len(_smiles) == 0:
        return False, None, "Smiles is empty"

    _request_id: str | None = None

    try:
        session_id = str(uuid4())
        auth_header = get_auth_header(session_id)
        _request_id = submit_work_request(auth_header, model_id, _smiles)
        wait_for_result(auth_header, _request_id)

        # TODO: add timings, eventually - we can use stats in backend for now
        return True, _request_id, None
    except:
        return False, _request_id, "Job failed: %s" % repr(exc_info())

