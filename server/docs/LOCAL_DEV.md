## Dependencies ##

- python3 pip
- python3 venv
- Docker (or equivalent, e.g. Podman)
- Kubernetes API access to the Ersilia cluster - see infrastructure repo
- AWS access and an AWS profile with the name `ersilia`

## Setup ##

### Python ###

```
python3 -m venv .venv

export PATH=".venv/bin:$PATH"

# Download external dependency
curl -L https://github.com/RudolfStander/python-framework/releases/download/0.0.2/python_framework-0.0.2-py3-none-any.whl \
    -o dependencies/python_framework-0.0.2-py3-none-any.whl

pip3 install -r ./requirements.txt
```

### PostgreSql ###

```
# Start postgresql docker instance
docker run --name ersilia-pgsql -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
```

## Environment Variables ##

Most env vars are set in the [test-local.sh](./operation/test-local.sh) script and committed to Git for local development.\
There are some secrets that get loaded externally using a NON-COMMITTED script: `operations/secrets.sh`


`operations/secrets.sh` content:
```
export SLACK_TOKEN="..."
export SLACK_CHANNEL_ID="..."
```

## Execution ##

Local execution can be performed by executing the [test-local.sh](./operation/test-local.sh) script.\
This script will:
    - check and start postgresql docker instance
    - activate the Python virtual environment
    - set all required environment variables
    - run the python3 app


By default, the api is accessible at `localhost:8080` (configurable with env vars `API_HOST` + `API_PORT`)

