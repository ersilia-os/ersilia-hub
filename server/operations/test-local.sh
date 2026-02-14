if [ $(docker ps | grep -c "pgsql") -eq "0" ]; then
    echo -e "\nStarting docker postgresql..."
    docker run --name ersilia-pgsql -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
fi

if [ "$VIRTUAL_ENV" = "" ]; then
    echo "\nActivating virtual env..."
    export VIRTUAL_ENV="$(pwd)/.venv"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
fi

export APPLICATION_NAME="ersilia-model-manager"

export DATABASE_HOST="localhost" # TODO: check this
export DATABASE_PORT="5432"
export DATABASE_NAME="postgres"
export DATABASE_USERNAME="postgres"
export DATABASE_PASSWORD="password"
export DATABASE_SCHEMA="model_manager"
export DATABASE_MIGRATIONS_PATH="src/db/migrations"

export LOG_LEVEL_ModelController="DEBUG"
export LOG_LEVEL_ModelIntegrationController="INFO"
export LOG_LEVEL_K8sController="DEBUG"
export LOG_LEVEL_K8sProxyController="INFO"
export LOG_LEVEL_WorkRequestController="DEBUG"
export LOG_LEVEL_WorkRequestWorker="TRACE"
export LOG_LEVEL_JobSubmissionTask="TRACE"
export LOG_LEVEL_S3IntegrationController="DEBUG"
export LOG_LEVEL_AuthController="INFO"
export LOG_LEVEL_InstanceMetricsController="INFO"
export LOG_LEVEL_ModelInstanceHandler="TRACE"
export LOG_LEVEL_ServerController="TRACE"
export LOG_LEVEL_FailedServerHandler="TRACE"
export LOG_LEVEL_ModelInputCache="TRACE"
export LOG_LEVEL_JobSubmissionProcess="TRACE"

export MODELS_NAMESPACE="eos-models"
export MODEL_COLLECTION_NAME="eos"
export LOAD_K8S_IN_CLUSTER="false"

export MODEL_S3_BUCKET_NAME="ersilia-hub"
export MODEL_S3_DATA_PATH="model-data"

export MODEL_INTEGRATION_PORT="80"
export MODEL_INTEGRATION_MOCK_SUCCESS_ID="eos3nn9"
export MODEL_INTEGRATION_MOCK_FAIL_ID="eos4e40"
export MODEL_INTEGRATION_PROXY_IDS="eos5axz,eos7d58,eos42ez,eos3804,eos2db3,eos18ie,eos5dti,eos7m30,eos37l0,eos2m0f"

export AWS_PROFILE="h3d"

export SERVER_ID="server-0"
export MAX_CONCURRENT_MODEL_INSTANCES="2"

export MODEL_HUB_RECORDS_URL="https://www.ersilia.io/v1/datasource/airtable/5ce288d5-4600-42df-9d5f-8617b023a3e3/40117d92-6c86-49e2-94f1-ff4069ccbfd4/7811ffd5-cf42-4ace-85ea-5fc7490c47aa/3a852b80-9afe-4ae7-bad4-09a87afc7f8b/data"
export MODEL_HUB_DETAILS_BASE_URL="https://www.ersilia.io/v1/datasource/airtable/5ce288d5-4600-42df-9d5f-8617b023a3e3/0e97c68a-b15c-42bb-b34c-344cacfab08d/3e2b9c48-4162-40d0-8962-fb8852d85fbe/69ca2816-fba2-4d81-80a5-1e4f6a25f8dd/data"

# TODO: add to SECRET
export PASSWORD_SALT="temptesting"

if [ $(ls -1 "operations" | grep -c "secrets.sh") -eq "1" ]; then
  source operations/secrets.sh
fi

echo "\nStarting Python app..."

python3 src/app.py

export VIRTUAL_ENV=""
