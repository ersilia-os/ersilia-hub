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
- EriliaUser
- ErsiliaAnonymous

The ErsiliaAnonymous auth only requires a user-generated GUID as "key" to the creating a Session.\
Whereas the ErsiliaUser requires a full username and password to create a Session and also enables Authorization functionality.\
Both implementations uses a Session in the back for keeping the user active.

Server Code:
- [API](./server/src/api/auth.py)
- [API Integration](./server/src/library/api_utils.py) (see `api_handler` and `api_validate_auth`)
- [Session Database Integration](./server/src/db/daos/user_session.py)
- [User Database Integration](./server/src/db/daos/user.py)
- [User Auth Databse Integration](./server/src/db/daos/user_auth.py)
- [User Persmission Database Integration](./server/src/db/daos/user_permission.py)
- [AuthController](./server/src/controllers/auth.py)


### User admin ###
(brief description + links to classes + live page)



### Node monitor (instance metrics collection) ###
(brief description + links to classes + live page)


### Work Request Stats ###
(brief description + links to classes + live page)

