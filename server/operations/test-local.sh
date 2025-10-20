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

export LOG_LEVEL_ModelController="INFO"
export LOG_LEVEL_ModelIntegrationController="INFO"
export LOG_LEVEL_K8sController="DEBUG"
export LOG_LEVEL_K8sProxyController="INFO"
export LOG_LEVEL_ScalingManager="DEBUG"
export LOG_LEVEL_ScalingWorker="INFO"
export LOG_LEVEL_WorkRequestController="INFO"
export LOG_LEVEL_WorkRequestWorker="TRACE"
export LOG_LEVEL_JobSubmissionTask="TRACE"
export LOG_LEVEL_S3IntegrationController="DEBUG"
export LOG_LEVEL_AuthController="INFO"
export LOG_LEVEL_InstanceMetricsController="INFO"
export LOG_LEVEL_ModelInstanceHandler="TRACE"
export LOG_LEVEL_ServerController="TRACE"
export LOG_LEVEL_FailedServerHandler="TRACE"
export LOG_LEVEL_ModelInputCache="TRACE"

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

# TODO: add to SECRET
export PASSWORD_SALT="temptesting"

echo "\nStarting Python app..."

python3 src/app.py

export VIRTUAL_ENV=""
