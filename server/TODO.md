
[ ] add permissions to user login response
[ ] add permissions cached on frontend

[ ] user session refresh bug, showing "Session expired" and clearing user name
    
[ ] make email required during signup

[ ] stats table based on model requests 
  * model_id, request_id, result_success (bool), request_timestamp, pod_ready_timestamp (get from ModelInstanceLog), processed_timestamp
  * index on model_id + proces
  [ ] migration + DAO + object
    * DAO select query should allow filter on modelid + request_timestamp + rollup_by_model + rollup_by_status (can be combined)
  [ ] controller
  [ ] add insertions to workrequestworker (ON COMPLETE / FAIL)
  [ ] api

[ ] stats frontend
  [ ] simple table
  [ ] filters
  [ ] rollup "toggles"
  [ ] download to CSV

[ ] model instance history page ??

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

