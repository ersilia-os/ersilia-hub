# ersilia-hub

# Development Documentation #

## Local Dev ##

- [Server](./server/docs/LOCAL_DEV.md)
- [Frontend](./server/docs/LOCAL_DEV.md)

## Deployment Process

[Deployment Process](./docs/DEPLOYMENT.md)

## External Integration (non-ui)

[External Integration](./docs/INTEGRATION.md)

## Live API Docs

To access the API docs of the live environment, you can open the below link in a private (incognito) tab in your browser.\
https://hub.ersilia.io/api/v1/docs \

The link needs to be opened in a private tab, because the hub.ersilia.io application installs a Service Worker which intercepts requests and breaks the docs rendering on non-private tab access.


# Implementation Documentation #

## Processes ##

- [Request Submission](./docs/REQUEST_SUBMISSION.md)
- [Request Processing Flow](./docs/REQUEST_PROCESSING_FLOW.md)
- [Model Instance Process / Job Processing](./docs/MODEL_INSTANCE_PROCESS.md)

## Undocumented Processes ##

### Model Recommendation Engine ###
The Model Recommendation Engine is responsible for evaluating the Memory and CPU resources used by a Model execution\
and automatically recommending better Memory and CPU constraints. The user can apply these recommended values on the [Model Recommendations](https://hub.ersilia.io/recommendations) page.

Server code:
- [Database Integration](./server/src/db/daos/instance_metrics.py)
- [Recommendation Engine](./server/src/controllers/recommendation_engine.py)
- [Metrics Collection](./server/src/controllers/node_monitor.py)
- [API](./server/src/api/recommendations.py)

Frontend code:
- [Model Recommendations component](./frontend/src/app/model-recommendations/model-recommendations.component.ts)
- [Resource visualizer component](./frontend/src/app/model-instance-resource/model-instance-resource.component.ts)

### Model Input Caching ###
When a user opts-in, the results of their model evaluations will be cached in the database for that model.\
This cache is used for every subsequent model Work Request submissions (regardless of opt-in).\
Some additional logic has been implemented for cache clearing on request, etc.

Server code:
- [Database Integration](./server/src/db/daos/model_input_cache.py)
- [ModelInputCacheController](./server/src/controllers/model_input_cache.py)


### User Authentication and Authorization ###
There are two different Authentication methods in Ersilia Hub:\
- ErsiliaUser
- ErsiliaAnonymous

The ErsiliaAnonymous auth only requires a user-generated GUID as "key" to the creating a Session.\
Whereas the ErsiliaUser requires a full username and password to create a Session and also enables Authorization functionality.\
Both implementations uses a Session in the back for keeping the user active.

Server code:
- [API](./server/src/api/auth.py)
- [API Integration](./server/src/library/api_utils.py) (see `api_handler` and `api_validate_auth`)
- [Session Database Integration](./server/src/db/daos/user_session.py)
- [User Database Integration](./server/src/db/daos/user.py)
- [User Auth Database Integration](./server/src/db/daos/user_auth.py)
- [User Persmission Database Integration](./server/src/db/daos/user_permission.py)
- [AuthController](./server/src/controllers/auth.py)

Frontend code:
- [Auth Service](./frontend/src/services/auth.service.ts)
- [Auth Interceptor](./frontend/src/services/auth.service.ts) (see `authInterceptor`)
- [Page Auth Guards](./frontend/src/app/app.routes.ts)
- [Login page](./frontend/src/app/login/login.component.ts)

### User admin ###
User admin includes: user deletion, user passowrd reset, user permission management, and user data clearing.

Server code:
- [API](./server/src/api/users.py)
- [User Database Integration](./server/src/db/daos/user.py)
- [User Persmission Database Integration](./server/src/db/daos/user_permission.py)
- [User Admin Controller](./server/src/controllers/user_admin.py)

Frontend code:
- [Users Service](./frontend/src/services/users.service.ts)
- [Various User Admin Components](./frontend/src/app/user/)

### Node monitor (instance metrics collection) ###
The [Node Monitor](./server/src/controllers/node_monitor.py) runs on every node associated with Ersilia pods.\
It automatically scrapes all metrics on the node and gos through an Ingestion process (see [InstanceMetricsController](./server/src/controllers/instance_metrics.py)).\
Metrics are kept in-memory for every existing Model Instance in cyclic buffers.\
Once the ModelInstance is terminated (either with success or failure), the metrics are aggregated and persisted in the database.

Server Code:
- [Node Monitor](./server/src/controllers/node_monitor.py)
- [InstanceMetricsController](./server/src/controllers/instance_metrics.py)
- [Metrics Persistence from ModelInstanceHandler](./server/src/controllers/model_instance_handler.py) see `_on_terminated` in `ModelInstanceHandler`
- [Database Integration](./server/src/db/daos/instance_metrics.py)
- [API](./server/src/api/metrics.py)

### Work Request Stats ###
During the transition of a WorkRequest through various processes, we track various statistics on the WorkRquest regarding timings of certain processes.\
With these statistics, we can draw reports on our processes.

Server code:
- [Database Integration](./server/src/db/daos/work_request_stats.py) NOTE: the stats columns are part of the standard WorkRequest table
- [API](./server/src/api/work_request_stats.py)

Frontend code:
- [Stats Service](./frontend/src/services/request-stats.service.ts)
- [Stats Dashboard Page](./frontend/src/app/stats/stats.component.ts)

