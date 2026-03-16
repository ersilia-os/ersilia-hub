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

See `_handle_queued_requests` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py).

- set WorkRequest status to SCHEDULING
- load results from Cache for Model (see `_handle_work_request_cache` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py))
- if all results returned from cache:
    - upload result to S3
    - set work request status to COMPLETED
- else, request a new [ModelInstance](../server/src/controllers/model_instance_handler.py) (for more details on ModelInstance see [Model Instance Process](./MODEL_INSTANCE_PROCESS.md))
- if success, set status to PROCESSING
- else, set status back to QUEUED

## SCHEDULING ##

See `_handle_scheduling_requests` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py).

 - check state of work request
 - if possibly failed, move back to QUEUED
 - if in-progress, move to PROCESSING

## PROCESSING ##

See `_handle_processing_work_requests` and `_handle_processing_work_request` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py).

 - check state of work request
 - if job processing completed, process result based on status (COMPLETED / FAILED)

## COMPLETED ##

See `_process_completed_job` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py).\
**NOTE: This forms part of the above `_handle_processing_work_requests`, it is not separately handled.**

 - get processed results from Job
 - merge with any cached results
 - upload full results to s3
 - if cache opt-in, cache new results
 - set WorkRequest status to COMPLETED

## FAILED ##

See `_process_failed_job` in [WorkRequestWorker](../server/src/controllers/work_request_worker.py).\
**NOTE: This forms part of the above `_handle_processing_work_requests`.**

 - set error details on the WorkRequest
 - set WorkRequest status to FAILED

Failed WorkRequests are also separately loaded and handled in `_handle_failed_work_requests` - [WorkRequestWorker](../server/src/controllers/work_request_worker.py).\
This function simply ensures all resources are properly cleaned up for any failed WorkRequests
