# Request Processing Flow #

Persisted WorkRequests are processed by the [WorkRequestWorker](../server/src/controllers/work_request_worker.py) thread.\
The [WorkRequestController](../server/src/controllers/work_request.py) (see `_initialize_workers` and `_update_worker_models`) spawns these Worker threads and load-balances active models between them, such that no two workers process the same models.

The Workers are responsible for processing all Requests. \
WorkRequests are loaded from the database based on status, the Worker's assigned ModelIds, and the active ServerId (see `_handle_work_requests` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py)) \
Additionally, failed WorkRequests are also processed to ensure all resources are cleaned up (see `_handle_failed_work_requests` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py))

The basic flow is described by the following diagram:
![Request_Processing_Flow](./Request_Processing_Flow.drawio.svg)


# The Process by Status #

## QUEUED ##


## SCHEDULING ##


## PROCESSING ##


## COMPLETED ##


## FAILED ##

