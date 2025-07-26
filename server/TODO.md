
[x] Add controller for loading active models:
  * full pod !!! NEED TO ADD RESOURCES TO PERSISTED POD !!!
  * all running averages for all metrics
  
[x] Add API to load active models (no filters for now)

```
File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/api/instances.py", line 40, in load_instances
    metrics.extend(
    ~~~~~~~~~~~~~~^
        map(
        ^^^^
    ...<4 lines>...
        )
        ^
    )
    ^
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/objects/instance.py", line 29, in from_object
    k8s_pod=K8sPodModel.from_object(obj.k8s_pod),
            ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/objects/k8s_model.py", line 112, in from_object
    pod_state=K8sPodStateModel.from_object(k8s_pod.pod_state),
              ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/objects/k8s_model.py", line 69, in from_object
    else list(map(K8sPodConditionModel.from_object, obj.conditions))
         ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/objects/k8s_model.py", line 46, in from_object
    return K8sPodConditionModel(
        last_probe_time=obj.last_probe_time,
    ...<4 lines>...
        type=obj.type,
    )
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/.venv/lib/python3.13/site-packages/pydantic/main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
pydantic_core._pydantic_core.ValidationError: 3 validation errors for K8sPodConditionModel
last_probe_time
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.11/v/string_type
message
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.11/v/string_type
reason
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.11/v/string_type
INFO:     ::1:54706 - "GET /api/instances?active=true HTTP/1.1" 500 Internal Server Error
```


```
[ERROR - InstanceMetricsController] @ [2025-07-26T14:37:05.742Z] : Failed to insert PersistedInstanceMetrics, error = [(<class 'TypeError'>, TypeError("PersistedInstanceMetrics.__init__() missing 1 required positional argument: 'memory_running_averages'"), <traceback object at 0x105c7bd80>)]
[ERROR - InstanceMetricsController] @ [2025-07-26T14:37:05.742Z] : Failed to insert PersistedInstanceMetrics, error = [(<class 'TypeError'>, TypeError("PersistedInstanceMetrics.__init__() missing 1 required positional argument: 'memory_running_averages'"), <traceback object at 0x103f1b1c0>)]
[INFO - NodeMonitorController] @ [2025-07-26T14:37:05.742Z] : controller stopped.
[INFO - ScalingManager] @ [2025-07-26T14:37:05.742Z] : Controller stopped
Traceback (most recent call last):
Traceback (most recent call last):
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/controllers/instance_metrics.py", line 192, in persist_metrics
    persisted_metrics = PersistedInstanceMetrics(
        _metrics.model_id,
    ...<2 lines>...
        _metrics.memory_running_averages,
    )
  File "/Users/nasihastander/rudolf/h3d/repos/ersilia-hub/server/src/controllers/instance_metrics.py", line 192, in persist_metrics
    persisted_metrics = PersistedInstanceMetrics(
        _metrics.model_id,
    ...<2 lines>...
        _metrics.memory_running_averages,
    )
```


[ ] Add frontend to visualize active models
  [ ] objects + service
  [ ] new page (header + add to sidebar)
  [ ] custom "blocks" (maybe fill width for now)
    [ ] model id (filter out server for now, separate toggle for that)
    [ ] instance name
    [ ] cpu stats
      [ ] "guage" MAX usage OVERALL out of resource limit
      [ ] "guage" min usage OVERALL out of resource REQUEST
      [ ] "guage" avg usage OVERALL out of resource limit
    [ ] memory stats
      [ ] "guage" MAX usage OVERALL out of resource limit
      [ ] "guage" min usage OVERALL out of resource REQUEST
      [ ] "guage" avg usage OVERALL out of resource limit
    * stats guage should show x / x below and % (as number) inside
    * stats guage levels, should get it from recommendation engine (or at least hardcode it for now)
      cpu:
      - 0 - 40% = orange (very under), 
      - 40 - 65 = yellow (under),
      - 65 - 85 = green (recommended),
      - 85 - 95 = yellow (over)
      - 95 - 105 = orange (very over)
      - 105+ red 
      mem:
      - 0 - 40% = orange (very under)
      - 40 - 65 = yellow (under),
      - 65 - 80 = green (recommended),
      - 80 - 90 = yellow (over)
      - 90 - 93 = orange (very over)
      - 93+ red (anything above is dangerously close to OOM) 

---

[ ] Add loading of persisted models to controller:
    * full pod (final "active" state, just before TERMINATED, i.e. sort desc by timestamp and filter out TERMINATE)
    * all running averages for all metrics

[ ] Implement recommendations engine
  * IGNORE model input size (FOR NOW)
  * should only consider persisted, not active
  * specify time range + limit, default no time but 100 limit
  * use min / max (not avg) and compare to pod resources (as persisted)
  * use percentage as hieuristic for each resource req / lim
  * based on %, reccommend adjustment for each resource (round to full numbers, target middle of green range)
      cpu:
      - 0 - 40% = orange (very under), 
      - 40 - 65 = yellow (under),
      - 65 - 85 = green (recommended),
      - 85 - 95 = yellow (over)
      - 95 - 105 = orange (very over)
      - 105+ red 
      mem:
      - 0 - 40% = orange (very under)
      - 40 - 65 = yellow (under),
      - 65 - 80 = green (recommended),
      - 80 - 90 = yellow (over)
      - 90 - 93 = orange (very over)
      - 93+ red (anything above is dangerously close to OOM) 

[ ] API for recommendations (eventually we will run this nightly and persist it)

[ ] Create recommendations UI

---

Model Instance actions

- stop / destroy instance
- download logs (no filtering, just all of it)
- view instance history (actions on instance + full pod dump)

---

[ ] need to add loader on requests load, maybe a global loader ?
[ ] make email required during signup
[ ] user session refresh bug, showing "Session expired" and clearing user name 
  Angular is running in development mode.
  auth.service.ts:37 no session, no refresh
  auth.service.ts:295 session_start_time = 1750048724742
  auth.service.ts:296 session_max_age_seconds = 300
  auth.service.ts:297 check = true

[ ] ensure logout on session expiry or invalidation

[ ] release

---

[ ] dynamically update models in workers
  [ ] load balance models onto workers (maybe do it ON CHANGE + every 30s)

[ ] models admin page

[ ] release

---

[ ] work requests admin page
  [ ] permissions check ('ADMIN')
  [ ] add sidebar / menu button
  [ ] duplicate requests page
  [ ] show ALL user's requests
  [ ] limit to status + request date + result status (cannot view sensitive data)
    [ ] filter input + result data out on backend api
  [ ] add filters
    [ ] user id
    [ ] anon session id
    [ ] model
    [ ] date from (no time)
    [ ] date to (no time)

[ ] release

---

[ ] add k8s events to modelinstance

[ ] model instance history page ??

---

[ ] active instances page
  [ ] permissions check ('ADMIN')
  [ ] load active instances (might need a new api?)
  [ ] display:
    - model
    - instance start time
    - instance status (pod status)
    - instance events (raw k8s events, jsonified)
    - assigned request id (annotation)
  [ ] filters
    [ ] model
    [ ] instance start from
    [ ] instance start to
    [ ] instance (pod) status
  [ ] actions
    [ ] stop instance

---

[ ] document anon request process + share "curl" commands

--

[ ] perf improvements
  [ ] session cache + refresh, only do a DB check on session failure

---

[ ] cron job to clear requests based on age (7 days)

---

[ ] node auto-scaling
  [ ] design
    * should monitor pod statuses (e.g.g pending + Scheduler states)

  [ ] implementation
    [ ] integrate with existing scaling manager / workers
    [ ] add scheduler status to pod status
    [ ] if pod Pending or Evicted, check for scheduler statuses
    [ ] scale nodes based on required models
    [ ] scale down ??
      * add pod affinity to pack pods better
      * if node is empty, cordon + terminate
      * what about "almost empty" nodes ? - maybe eventually fix, it will always scale down when not being used


---

[ ] valdate user signup details + username + password on api 

---

[ ] fix python-framework schema setting in DB (does not work with the pg8000 driver)

---

[ ] compound caching

---