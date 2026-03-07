# Request Submission Process #

The submission of a request is fairly uninvolved, since we use a "work queue" strategy for processing.

Therefore, submitting a Work Request (or evaluation) is simply a matter of:
- The client (ui or other) will send the Work Request payload to the API
- The API will validate the request content and structure (just a simple validation) using the Work Request Controller
- The API will call the Work Request Controller for processing the submission request
- The Work Request Controller will:
    - Generate a new ID for the Work Request
    - Set the Work Request Status as "PENDING"
    - Persist the Work Request in the PostgreSql Database
    - Return the Persisted Work Request details

[Request Submission Process](./Request Submission Process (High Level).drawio.svg)


## Frontend Related Code ##

- Component for creating and submitting the Work Request [here](../frontend/src/app/request-create/request-create.component.ts)
- API Service for submitting the Work Request - see method called `submitRequest` [here](../frontend/src/services/requests.service.ts)

## Server Related Code ##

- API for Work Request Submission - see method called `create_request` [here](../server/src/api/work_request.py)
- Work Request object class - see `WorkRequest` class [here](../server/src/objects/work_request.py)
- Work Request Controller validation - see method called `validate_request` [here](../server/src/controllers/work_request.py)
- Work Request Controller persistence - see method called `create_request` [here](../server/src/controllers/work_request.py)
- Database Persistence logic - see class `WorkRequestInsertQuery` [here](../server/src/db/daos/work_request.py)
