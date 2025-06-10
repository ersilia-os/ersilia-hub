[x] debug model issues (maybe increase timeout ?)

[ ] fix csv output

[ ] add Permissions to api
  [x] add permissions table + DAO + Objects
    * userid -> permissions csv
  [x] add permissions cache to Auth + reload on timer
  [x] add user_has_permission(one_of: List[]) to auth controller
  [x] add permissions to API handler (pass list of allowed permissions)
  [x] add static permissions Enum (for now only ADMIN permission, for full access to everything)
  [x] add ADMIN permission to existing apis

[ ] release

---

[ ] add permissions to user login response
[ ] add permissions cached on frontend

[ ] user session refresh bug, showing "Session expired" and clearing user name

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

  [ ] actions for:
    [ ] set status -> REQUESTED / FAILED
    [ ] view sensitive data (LOG ON BACKEND + reload full request)

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
    
[ ] make email required during signup

[ ] add model instances log to DB
  [ ] timestamp, event, pod dump, correlationid (e.g. workrequestid)
  [ ] add dump at pod creation + termination
  [ ] ensure k8s EVENTS are in the pod details

[ ] release

---

[ ] document anon request process + share "curl" commands

--

[ ] perf improvements
  [ ] session cache + refresh, only do a DB check on session failure

---

[ ] stats table based on model requests 
  * model_id, request_id, processed (bool), result_success (bool), request_timestamp, processed_timestamp
  * add updates to existing work_request DAO

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

