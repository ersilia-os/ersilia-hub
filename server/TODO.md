[x] Add node name to pod info (and automatically model_instance_log)

[x] Add input size to request table
[x] Add input size to stats query + filter (greater_than_eq + less_than_eq)
[x] Add group_by_instance_size flag (keep model_id but also add instance_size)
[x] Fix stats query (model_id stuff)

[ ] stats frontend
  [ ] simple table
  [ ] filters
    * date from + to filter (no time, only date)
    * model ids filter
    * model_size filters
    * group_by options (model ID should be forced, model_size optional)

  [ ] download to CSV

[ ] release

---

[ ] install metrics server
[ ] investigate metrics server integration (check API)
[ ] Create model_instance_monitor (thread)
  [ ] when starting a model, start monitor thread
  [ ] get metrics from metric server and keep in-mem (limit to 30min, configurable metrics threshold, 4s default)
  [ ] 

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

