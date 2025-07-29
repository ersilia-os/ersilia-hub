
[ ] Implement recommendations engine
  * IGNORE model input size (FOR NOW)
  * should only consider persisted, not active
  * specify time range + limit, default no time but 100 limit

  [ ] lock on execution, can only run one at a time
  [ ] in-mem state:
    - last updated
    - status: running | up_to_date | outdated (for future automation reasons)
    - recommendations:
      {model_id : { timestamp: str, cpu: resource_recomendations, memory: resource_recommendations}}
  [ ] hardcode profile configs: 
    * cpu_min
    * cpu_max
    * memory_min
    * memory_max
  [ ] execution:
    - load active models (list of strings) (eventually filter on active / not)
    - per model (separate function):
        - load persisted instances (existing function)
        - get min MIN over all (just the metrics values)
        - get max MAX over all (just the metrics values)
        - use profile_resources(metrics) on overall min/max
        - apply profiles (hardcode for now, but can persist later) 
          -> ResourceRecommendation: {profile_state: over/under/recommended..., current_value: float, current_percentage: int, recommended_value: INT}
          * this should give the current percentage value AND what the recommended value is
          * use the middle of the "recommended" bracket
        - update in-mem map of per-model recommendations


[ ] API for recommendations (eventually we will run this nightly and persist it)
  [ ] load
  [ ] run all
  [ ] run model


[ ] Create recommendations UI
  [ ] service / objects
  [ ] new page + sidebar link
  [ ] "toolbar" with state:
    * state
    * last execution 
  [ ] actions : run all

  [ ] custom components (similar to existing model instances)
    * block of model details
    * block per profile of recommendations
      * current usage , in brackets percentage
      * recommended range - min, max values, with percentages in brackets
      * colour all of it based on profile state (over , under, etc.)

  * NOTE: next "sprint", we'll add actions to apply recommendation

---

Model Instance actions

- stop / destroy instance
- download logs (no filtering, just all of it)
- view instance history (actions on instance + full pod dump)

[ ] dynamic model updates:
  [ ] add k8s_resources object to model (replace maxMem + disableMemLimit)
  [ ] when creating the model instance, apply k8s_resources to the template
  [ ] reload models in controller (consider enable / disable to also update the work_request_worker loadbalancing)

[ ] add actions to recommendations engine / ui
  * apply recommendation (per model, per profile) -> update and persist model -> reload anything required

[ ] model management page

---

[ ] Add request details to instances page
  * request state

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