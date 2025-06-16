

[x] add queries for stats
  * what we want, PER MODEL:
    - total count
    - success count
    - fail count
    - active count
    - total, max, min, avg job execution time FOR SUCCESSES (job submit till job result)
    - total, max, min, avg total execution time FOR SUCCESSES (request submit till request complete/fail)
  * what we want to filter on:
    - userid (or sessionid)
    - modelid
    - request_timestamp

[x] add stats functions to controller
[x] add stats to api
[x] add filters load to controller + api
  * FOR NOW, we don't filter the filters
  * return:
  - all models
  - all account (auth) types
  - all userid / sessionid (split by auth type)
  
* NO ROLLUP, for now

[x] add permissions cached on frontend

[x] sidebar
  [x] permissions check ('ADMIN')
  [x] add sidebar / menu button
  [x] add html directly to app component

[x] router for new components, e.g. stats (or is there a newer approach)

[ ] stats frontend
  [ ] simple table
  [ ] filters
    * toggle between anon vs user account
    * date from + to filter (no time, only date)
    * model ids filter
    * userid filter (but for anon, it's actually SESSION)
  [ ] group_by
  [ ] download to CSV

[ ] need to add loader on requests load, maybe a global loader ?
[ ] make email required during signup
[ ] user session refresh bug, showing "Session expired" and clearing user name 
  Angular is running in development mode.
  auth.service.ts:37 no session, no refresh
  auth.service.ts:295 session_start_time = 1750048724742
  auth.service.ts:296 session_max_age_seconds = 300
  auth.service.ts:297 check = true

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

