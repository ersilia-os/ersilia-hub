if [ $(docker ps | grep -c "pgsql") -eq "0" ]; then
    echo -e "\nStarting docker postgresql..."
    docker run --name ersilia-pgsql -p 5432:5432 -e POSTGRES_PASSWORD=password -d postgres
fi

docker run -p 8080:8080 --network=host \
    -e DATABASE_HOST="localhost" \
    -e DATABASE_PORT="5432" \
    -e DATABASE_NAME="postgres" \
    -e DATABASE_USERNAME="postgres" \
    -e DATABASE_PASSWORD="password" \
    -e DATABASE_SCHEMA="model_manager" \
    -e DATABASE_MIGRATIONS_PATH="/app/src/db/migrations" \
    -e LOG_LEVEL_ModelController="DEBUG" \
    -e LOG_LEVEL_ModelIntegrationController="DEBUG" \
    -e LOG_LEVEL_K8sController="DEBUG" \
    -e LOG_LEVEL_K8sProxyController="DEBUG" \
    -e LOG_LEVEL_ScalingWorker="DEBUG" \
    -e LOG_LEVEL_WorkRequestController="DEBUG" \
    -e LOG_LEVEL_WorkRequestWorker="DEBUG" \
    -e LOG_LEVEL_S3IntegrationController="DEBUG" \
    -e LOG_LEVEL_AuthController="TRACE" \
    -e MODELS_NAMESPACE="eos-models" \
    -e MODEL_COLLECTION_NAME="eos" \
    -e LOAD_K8S_IN_CLUSTER="false" \
    -e MODEL_S3_BUCKET_NAME="ersilia-hub" \
    -e MODEL_S3_DATA_PATH="model-data" \
    -e MODEL_INTEGRATION_PORT="80" \
    -e MODEL_INTEGRATION_MOCK_SUCCESS_ID="eos3nn9" \
    -e MODEL_INTEGRATION_MOCK_FAIL_ID="eos4e40" \
    -e MODEL_INTEGRATION_PROXY_IDS="eos5axz" \
    -e AWS_PROFILE="h3d" \
    -e PASSWORD_SALT="temptesting" \
    -v ~/.kube:/home/eos/.kube \
    -v ~/.aws:/home/eos/.aws \
    ersiliaos/ersilia-hub-server:0.0.3
