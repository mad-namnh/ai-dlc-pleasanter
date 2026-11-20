# Phase 9 — scheduled drift check on the task owner's machine (A1, N19, N20, N25)

Tier: Standard (read-only against Pleasanter; no guard, gate or key handling changes). Parent: `0a008ae`.

## What is built

`pls drift-watch run | show | install | remove` — new modules `tools/pls/pls_drift_watch.py` (scope, baseline currency,
check, report) and `tools/pls/pls_drift_watch_schedule.py` (Task Scheduler XML, install / remove, notification,
background start). `pls.py` only wires the parser and passes its own functions (`export_site`, `drift_report`,
`classify`) in, so the modules stay testable without a server.

## Decisions (Orchestrator, under N25; reported to Nam)

| # | Decision | Why |
|---|---|---|
| D1 | Scope on a machine = the environments its `.pls/connections.json` names directly (not through a sandbox alias), role `dev` or `stg`, not sandboxes; plus the environments named with `install --env` (a developer names their own sandbox `dev-<you>`). `prod` is refused. | N20 without a new setting: a dev's machine has no stg connection (N12), so stg is checked only on Nam's / a delegate's. A sandbox shares its base's connection, so "own sandbox" cannot be told apart by itself; the person names it once. Customer environments: N16 |
| D2 | Sites: of a sandbox, only its own copies (`sandbox: true`); the shared sites it references are checked under the base environment | one site, one baseline |
| D3 | Baseline current = no applied release of the environment in the shared branch (`origin/HEAD`, or `--shared-branch`) that this folder lacks or holds in another state; after `git fetch`. A behind or unknown state refuses that environment's report (sandboxes are not compared: their releases are local, N22). No remote = the folder's own `releases/`, said in the report | plan: "refuses to report while the folder is behind the shared branch's releases/" |
| D4 | Results in `.pls/drift-watch/`: `last.json`, `last.md`, latest export per site (overwritten). Nothing committed, nothing under `ops/drift/` (the person records the decision there) | plan; agents cannot read `.pls/` (hook) → `pls drift-watch show` prints it |
| D5 | Notification only when the set of drifted sites / differences changed since the last run (not every 2 hours); PowerShell balloon, message passed in an environment variable, not in the command text | no repeated alerts; no command injection from site names |
| D6 | Job = Task Scheduler XML (`schtasks /create /xml`): weekly Mon–Fri, start 09:00, repeat every 2 h for 10 h, working directory = the project, `pythonw.exe` when present (no console window), runs only while the person is logged on, missed runs started when the machine is available, one instance at a time, 30 min limit | `/tr` cannot set a working directory and is limited to 261 characters; XML can |
| D7 | Concurrency: `running.json` lock (taken with exclusive create; older than 30 min = abandoned) shared by the job and the session-start start | the job and a session can start together |

## Not verified here (needs Nam, phase 10)

Registering the task on Windows, the balloon on Nam's desktop, a real `git fetch` against GitHub, a real export on dev.
