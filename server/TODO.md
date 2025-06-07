

FIXES:

NOTES:

- document anon request process + share "curl" commands (and a simple python app ?)

- email required on signup

---

[x] fix signup with multiple users (get duplicate on second signup)

[x] csv result output
  [x] csv result toggle on load
  [x] change result json to csv (key -> column)
  [x] add csv download button on frontend

[x] add input to request view component

[x] csv file upload for INPUT
  [x] add file upload button
  [x] set input "text" to file content

[x] release

---

[ ] add Permissions to api
  [ ] add permissions table + DAO + Objects
    * userid -> permissions csv
  [ ] add permissions cache to Auth + reload on timer
  [ ] add user_has_permission(one_of: List[]) to auth controller
  [ ] add permissions to API handler (pass list of allowed permissions)
  [ ] add static permissions Enum (for now only ADMIN permission, for full access to everything)
  [ ] add ADMIN permission to existing apis

[ ] work requests admin page
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
    
[ ] release

---

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

