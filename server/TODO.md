[x] install metrics server
[x] investigate metrics server integration (check API)

```
# kubectl get --raw "/api/v1/nodes/ip-10-0-3-164.eu-south-2.compute.internal/proxy/metrics/resource"
resource = api.get_namespaced_custom_object(group="metrics.k8s.io", version="v1beta1", namespace="ersilia-core", plural="pods", name="ersilia-hub-server-78554c56f7-klmrl")


core_api = client.CoreV1Api()
metrics = core_api.connect_get_node_proxy_with_path(name="ip-10-0-3-164.eu-south-2.compute.internal", path="metrics/resource")
metrics.split("\n")
```

[x] Implement NodeMonitor
  [x] track active nodes
  [x] create a thread per active node
  [x] thread does metric scraping and calls PodMetricsController.ingest
  
  * eventually monitor node resources + active pods

[ ] Create model_instance_monitor (thread)
  [ ] when starting a model, start monitor thread
  [ ] on thread start, add pod to PodMetricsController
  [ ] monitor pod liveness / existence
  [ ] on pod terminated, persist podmetrics in DB + remove pod from metrics controller -> terminate thread
    * need to add DB layer to persist model / pod metrics

[ ] Add controller for loading model_instance (persisted OR current)
  [ ] active models:
    * full pod !!! NEED TO ADD RESOURCES TO PERSISTED POD !!!
    * all running averages per metric
  
  [ ] persisted models:
    * full pod (final state??)
    * all running averages per metric

  [ ] slice of values (for all metrics, no filters for now) - only active models
  
  [ ] recommendations for a model (global, not instance)
    * need to calculate per input size (or input size range ??)
    * should only consider persisted
    * specify time range + limit, default no time but 20 limit
    * use min / max (not avg) and compare to pod resources (as persisted)

[ ] Add api to match controller

[ ] Frontend
  [ ] list active models with their running averages in-line (maybe a custom component, not table)
  [ ] need to somehow visualize current pod resources requests / limits and thresholds (heatmap of how close / far to the threshold)
  
  [ ] separate "recommendations" screen for per-model analysis

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