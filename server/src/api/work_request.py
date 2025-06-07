from sys import exc_info
from typing import Annotated, List

from controllers.work_request import WorkRequestController
from objects.work_request import (
    WorkRequest,
    WorkRequestCreateModel,
    WorkRequestListModel,
    WorkRequestLoadAllFilters,
    WorkRequestLoadFilters,
    WorkRequestModel,
    WorkRequestStatus,
    WorkRequestUpdateModel,
)
from controllers.model import ModelController

from fastapi import APIRouter, HTTPException, Query, Request

from library.fastapi_root import FastAPIRoot
from controllers.s3_integration import S3IntegrationController

from library.api_utils import api_handler
from objects.api import AuthType
from python_framework.logger import ContextLogger, LogLevel


###############################################################################
## API REGISTRATION                                                          ##
###############################################################################

router = APIRouter(prefix="/api/work-requests", tags=["work-requests"])


def register(fastapi_root: FastAPIRoot = None):
    if fastapi_root is None:
        FastAPIRoot.instance().register_router(router)
    else:
        fastapi_root.register_router(router)


###############################################################################


@router.post("")
def create_request(
    work_request: WorkRequestCreateModel,
    api_request: Request,
) -> WorkRequestModel:
    auth_details, tracking_details = api_handler(api_request)

    if work_request is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    models = ModelController.instance().get_models()

    if not any(map(lambda x: x.id == work_request.model_id, models)):
        raise HTTPException(
            status_code=400,
            detail="Invalid request body - No model with id [%s]"
            % work_request.model_id,
        )

    new_work_request = WorkRequest.from_object(work_request.to_object())
    new_work_request.user_id = auth_details.user_session.userid
    new_work_request.metadata.session_id = auth_details.user_session.session_id
    new_work_request.metadata.user_agent = tracking_details.user_agent

    persisted_request = WorkRequestController.instance().create_request(
        new_work_request
    )

    if persisted_request is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to persist request, see server logs",
        )

    return WorkRequestModel.from_workrequest(persisted_request)


@router.put("/{request_id}")
def update_request(
    request_id: str,
    update: WorkRequestUpdateModel,
    api_request: Request,
) -> WorkRequestModel:
    auth_details, tracking_details = api_handler(api_request)

    if update is None:
        raise HTTPException(status_code=400, detail="Missing request body")

    update.id = request_id
    update_work_request = update.to_work_request()
    update_work_request.metadata.session_id = auth_details.user_session.session_id

    persisted_request = WorkRequestController.instance().update_request(
        update_work_request,
        enforce_same_session_id=auth_details.auth_type == AuthType.ErsiliaAnonymous,
    )

    if persisted_request is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to persist request, see server logs",
        )

    return WorkRequestModel.from_workrequest(persisted_request)


@router.get("")
def load_requests(
    filters: Annotated[WorkRequestLoadAllFilters, Query()],
    api_request: Request,
) -> WorkRequestListModel:
    auth_details, tracking_details = api_handler(api_request)

    filters_dict = filters.to_object()

    filters_dict["user_id"] = auth_details.user_session.userid

    if auth_details.auth_type == AuthType.ErsiliaAnonymous:
        filters_dict["session_id"] = auth_details.user_session.session_id

    requests = WorkRequestController.instance().get_requests(**filters_dict)

    if requests is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to load requests, see server logs",
        )

    return WorkRequestListModel(
        items=list(map(lambda x: WorkRequestModel.from_workrequest(x), requests))
    )


@router.get("/{id}")
def load_workrequest(
    id: str,
    filters: Annotated[WorkRequestLoadFilters, Query()],
    api_request: Request,
) -> WorkRequestModel:
    auth_details, tracking_details = api_handler(api_request)

    filters_dict = {"id": id}

    filters_dict["user_id"] = auth_details.user_session.userid

    if auth_details.auth_type == AuthType.ErsiliaAnonymous:
        filters_dict["session_id"] = auth_details.user_session.session_id

    requests = WorkRequestController.instance().get_requests(**filters_dict)

    if requests is None or len(requests) == 0:
        raise HTTPException(
            status_code=404, detail="Failed to load request with id [%s]" % id
        )

    request = WorkRequestModel.from_workrequest(requests[0])

    if request.request_status == WorkRequestStatus.COMPLETED and filters.include_result:
        try:
            result = S3IntegrationController.instance().download_result(
                request.model_id, request.id
            )
            request.result = result.extract_result()

            if filters.csv_result:
                request.map_result_to_csv()
        except:
            ContextLogger.sys_log(
                LogLevel.ERROR, "Failed to download work request result from S3, error = [%s]"
                % repr(exc_info())
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to download work request result from S3",
            )

    return request
