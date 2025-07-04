from base64 import b64encode
from json import dumps
from time import sleep, time
from typing import Any, Dict
from uuid import uuid4
from requests import get, post
from sys import argv, exc_info

API_BASE_URL = "https://hub.ersilia.io"
REQUEST_TIMEOUT = 600  # 10 minutes, in seconds


def get_auth_header(session_id):
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


def submit_work_request(auth_header, model_id, smiles):
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


def wait_for_result(auth_header, request_id):
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

            return response_json["result"]
        except:
            raise Exception(f"Failed to submit Job: [{repr(exc_info())}]")


def submit_job(model_id, smiles):
    session_id = str(uuid4())
    auth_header = get_auth_header(session_id)
    request_id = submit_work_request(auth_header, model_id, smiles)

    return wait_for_result(auth_header, request_id)


def get_models(auth_header) -> Dict[str, Any]:
    print("Getting models from server...")

    try:
        response = get(
            f"{API_BASE_URL}/api/models",
            headers={"Authorization": auth_header},
        )

        if response.status_code != 200:
            raise Exception(
                f"HTTP:{response.status_code} - {response.content.decode()}"
            )

        return response.json()
    except:
        raise Exception(f"Failed to submit job: [{repr(exc_info())}]")


def print_models(argv):
    session_id = str(uuid4())
    auth_header = get_auth_header(session_id)

    models = get_models(auth_header)

    for model in models["items"]:
        print(f"{model['id']}  |  [{'x' if model['enabled'] else ' '}]")


def run_model(argv):
    smiles = None

    with open(argv[2], "r") as file:
        smiles = file.readlines()

    result = submit_job(argv[1], smiles)

    with open(argv[3], "w+") as file:
        for line in result:
            file.write(line + "\n")


if __name__ == "__main__":
    cmd: str = None

    if len(argv) == 4:
        cmd = "run_model"
    elif len(argv) == 2 and argv[1] == "print_models":
        cmd = "print_models"

    if cmd is None:
        print("Invalid arguments!")
        print(
            "Usage: python basic_client.py <model-id> <smiles-csv-filepath> <output-filepath>"
        )
        print(
            "e.g.:\n python basic_client.py eos2m0f ../examples/smiles_100.csv smiles_100_output.csv"
        )
        print("\nTo print server models:\npython basic_client.py print_models")

        raise Exception("Invalid script arguments")

    if cmd == "run_model":
        run_model(argv)
    elif cmd == "print_models":
        print_models(argv)
