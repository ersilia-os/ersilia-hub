
[x] add permissions to user login response

[ ] add request_timestamp, pod_ready_timestamp (get from ModelInstanceLog) + processed_timestamp to WorkRequest

[ ] split Input + Result into separate WorkRequestData table
  * id
  * input
  * result
  * request_date (to simplify cleanup)

[ ] add indexes to WorkRequest to facilitate stats
[ ] add queries for stats
  * what we want, PER MODEL:
    - success count
    - fail count
    - total, max, min, avg model execution time (job submit till job result)
    - total, max, min, avg processing time (request submit till request complete/fail)
    - total, max, min, avg model execution time FOR SUCCESSES (job submit till job result)
    - total, max, min, avg processing time FOR SUCCESSES (request submit till request complete/fail)
  * what we want to filter on:
    - userid (or sessionid)
    - modelid
    - request_timestamp

[ ] add stats functions to controller
[ ] add stats to api
[ ] add filters load to controller + api
  * FOR NOW, we don't filter the filters
  * return:
  - all models
  - all account (auth) types
  - all userid / sessionid (split by auth type)
  
* NO ROLLUP, for now


[ ] add permissions cached on frontend
[ ] need to add loader on requests load, maybe a global loader ?
[ ] make email required during signup
[ ] user session refresh bug, showing "Session expired" and clearing user name 

[ ] sidebar
  [ ] permissions check ('ADMIN')
  [ ] add sidebar / menu button
  [ ] global sidebar service
  [ ] add html directly to app component

[ ] stats frontend
  [ ] simple table
  [ ] filters
    * toggle between anon vs user account
    * date from + to filter (no time, only date)
    * model ids filter
    * userid filter (but for anon, it's actually SESSION)
  [ ] group_by
  [ ] download to CSV

[ ] release

---

[ ] add k8s events to modelinstance

[ ] model instance history page ??

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

