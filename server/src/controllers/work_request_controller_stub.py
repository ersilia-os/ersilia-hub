###
# Stub class for passing controller by reference, without importing the file
##


from objects.work_request import WorkRequest


class WorkRequestControllerStub:
    @staticmethod
    def instance() -> "WorkRequestControllerStub":
        pass

    def update_request(
        self,
        work_request: WorkRequest,
        enforce_same_server_id: bool = True,
        expect_null_server_id: bool = False,  # for first time update
        retry_count: int = 0,
    ) -> WorkRequest | None:
        pass

    def mark_workrequest_failed(
        self, work_request: WorkRequest, reason: str | None = None
    ) -> WorkRequest:
        pass

    def get_requests(
        self,
        id: str = None,
        model_ids: list[str] = None,
        user_id: str = None,
        request_date_from: str = None,
        request_date_to: str = None,
        request_statuses: list[str] = None,
        server_ids: list[str] | None = None,
        limit: int = 200,
    ) -> list[WorkRequest]:
        pass

    def update_work_request_metadata(
        self,
        work_request_id: int,
        job_model_version: str | None = None,
    ) -> WorkRequest:
        pass
