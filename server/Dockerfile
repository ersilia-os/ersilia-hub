FROM python:3.12-slim AS build

WORKDIR /operations

RUN apt update && apt install -y curl
RUN mkdir -p dependencies
RUN curl -L https://github.com/RudolfStander/python-framework/releases/download/0.0.2/python_framework-0.0.2-py3-none-any.whl -o dependencies/python_framework-0.0.2-py3-none-any.whl
RUN python3 -m venv .venv

ENV PATH="/operations/.venv/bin:$PATH"

COPY requirements.txt .
RUN pip3 install -r ./requirements.txt

FROM python:3.12-slim AS production

RUN useradd eos
USER eos
WORKDIR /app

COPY --chown=eos:eos src src
COPY --chown=eos:eos --from=build /operations/.venv .venv

ENV PYTHONUNBUFFERED="1"

ENV APPLICATION_NAME="ersilia-hub"
ENV API_HOST="0.0.0.0"

ENV DATABASE_HOST="localhost"
ENV DATABASE_PORT="5432"
ENV DATABASE_NAME="postgres"
ENV DATABASE_USERNAME="postgres"
ENV DATABASE_PASSWORD="password"
ENV DATABASE_SCHEMA="public"
ENV DATABASE_MIGRATIONS_PATH="/app/src/db/migrations"

ENV LOG_LEVEL_ModelController="INFO"
ENV LOG_LEVEL_ModelIntegrationController="INFO"
ENV LOG_LEVEL_K8sController="INFO"
ENV LOG_LEVEL_K8sProxyController="INFO"
ENV LOG_LEVEL_ScalingManager="INFO"
ENV LOG_LEVEL_ScalingWorker="INFO"
ENV LOG_LEVEL_WorkRequestController="INFO"
ENV LOG_LEVEL_WorkRequestWorker="INFO"
ENV LOG_LEVEL_JobSubmissionTask="INFO"
ENV LOG_LEVEL_S3IntegrationController="INFO"
ENV LOG_LEVEL_AuthController="INFO"

ENV MODELS_NAMESPACE="eos-models"
ENV MODEL_COLLECTION_NAME="eos"
ENV LOAD_K8S_IN_CLUSTER="true"

ENV MODEL_S3_BUCKET_NAME="ersilia-hub"
ENV MODEL_S3_DATA_PATH="model-data"

ENV MODEL_INTEGRATION_PORT="80"
ENV MODEL_INTEGRATION_MOCK_SUCCESS_ID=""
ENV MODEL_INTEGRATION_MOCK_FAIL_ID=""
ENV MODEL_INTEGRATION_PROXY_IDS=""

# NOTE: service MUST override this
ENV PASSWORD_SALT="temptesting"

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

ENTRYPOINT ["python"]
CMD ["src/app.py"]
