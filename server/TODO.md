

[ ] add recommendation engine on backend (just singleton, not thread stuff)
[ ] add hardcoded profile configs in engine
  * profileconfigs:
  - {id: cpu_min, cpu_max, etc. , min: int, max: int, profile: VERY_UNDER, UNDER, RECOMMENDED, OVER, VERY_OVER, CRITICAL}
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
  * load from in-mem json string LIST

[ ] implement profile_resources(metrics) -> ModelInstanceResourceProfile
  [ ] update instance objects + instance api

[ ] implement apply_profiles(ModelInstanceResourceProfile) -> 
  ModelInstanceRecommendations : { cpu_min: ResourceRecommendation
    cpu_max: ResourceRecommendation
    ...
  }
    ResourceRecommendation: {profile_state: over/under/recommended..., current_value: float, current_percentage: int, recommended_value: INT}
[ ] add ModelInstanceRecommendations to modelinstance (nullable)


[ ] add ModelInstanceResourceProfile + ModelInstanceRecommendations to frontend objects
[ ] add resource profile PERCENTAGE to cpu + memory info blocks
  * use values from ModelInstanceResourceProfile but colour from ModelInstanceRecommendations (profile_state)
  * percentage big and x / y below it -> BOTH in same colour
  * hardcode the colours per profile_state

---

[x] Add loading of persisted models to controller:
    * full pod (final "active" state, just before TERMINATED, i.e. sort desc by timestamp and filter out TERMINATE)
    * all running averages for all metrics

---

[ ] Implement recommendations engine
  * IGNORE model input size (FOR NOW)
  * should only consider persisted, not active
  * specify time range + limit, default no time but 100 limit
  * use min / max (not avg) and compare to pod resources (as persisted)
  * use percentage as hieuristic for each resource req / lim
  * LIST of profileconfigs:
    - {min: int, max: int, profile: VERY_UNDER, UNDER, RECOMMENDED, OVER, VERY_OVER, CRITICAL}
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

    [ ] on start, wait 5min before auto-running (ONCE) -> infinite "waiting" loop 
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