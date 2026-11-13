# Review — AU1 rest: guarded KB probes (Critical)

## Round 1 — accept with fixes (0 Critical, 1 High, 1 Medium, 4 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `1f8ead4`; `git status` and a hash of the diff equal before and after.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | High | Nam chose "probe site deleted afterwards"; the ADR was marked Accepted with a substitute guard ("left harmless") he never saw — stop point (agent-rules §1 items 1, 2) | Stopped and asked. Nam (2026-11-13): "can build duoc viet xoa luon cho AU1, apply patch rồi review vòng 2". Built: guard 6 — delete via `deletesite` (route read in the 1.5.2 source), believed only when `getsite` no longer finds the site; refused / failed / 200-but-still-there → site kept harmless, probe `error`. ADR-0025 Accepted with his words. Tests for each path |
| F2 | Medium | The script name check is easy to get around; docs claimed the mail guard holds for more than mail | Fixed: escapes, `globalThis`, `this[…]`, `eval`, `Function`, `require`, `import` refused; ADR, docstring say plainly that the name check and the review of the probe file are the only controls against reaching other sites or the network; open question on `items` rights |
| F3 | Low | Forced teardown skipped on an unexpected exception | Fixed: teardown in `finally`; test with a crash in `run_tests` |
| F4 | Low | A script-only probe's permissions are not reset, docs said they are | Docs narrowed: only a roles probe's grant is removed, a script-only probe never touches permissions; test |
| F5 | Low | ADR said every unmet guard skips only that probe | Fixed: file rules refuse the whole run, environment conditions make that probe `error` |
| F6 | Low | Log named the wrong test as passing on the parent | Log corrected |



## Round 2 (final) — accept with fixes (0 Critical, 0 High, 3 Medium, 4 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `f9f5bc7`; `git status` and a hash of the diff equal before and after.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Medium | A delete was believed on any `getsite` answer other than 200 (a 5xx after the delete → site forgotten → a second site next run) | Fixed: only 404 counts; any other answer keeps the site in the state file, probe `error`; test (200 to deletesite, then 500) |
| R2-2 | Medium | The "way around a name" check missed `this` aliases, `constructor`, `fromCharCode`, computed access | Fixed both ways: refuses `this`, `constructor`, `prototype`, `__proto__`, `Reflect`, `Proxy`, `fromCharCode` / `fromCodePoint` and computed access other than `[0]` / `['literal']` (tests for the reviewer's bypasses, and plain code still allowed); wording in ADR and docstring narrowed to "refuses the obvious routes; the review of the probe file is the control" |
| R2-3 | Medium | `deletesite` outside the I3 write-path inventory | Fixed: `deletesite` in `WRITE_ENDPOINT` and both dynamic write detectors; `delete_probe_site` in `ALLOWED_WRITE_SITES` and `WRITE_RUNNERS` (called only from `http_cmd`); checked that the static scan now sees it |
| R2-4 | Low | No test for a failed teardown, nor for "not own" just before the delete | Tests added (teardown fails → `error`, site still deleted; site moved to the app folder → no deletesite sent, site kept) |
| R2-5 | Low | A role key file holding the operator's key ran role steps as the admin | Fixed: refused before any write; test |
| R2-6 | Low | `principals.admin` assumed to be the user behind the default key | Open question in ADR-0025 (fails safe: `error`, a person cleans up) |
| R2-7 | Low | ADR index row said "site left harmless" | Fixed |

Not reviewed again: round 2 was the last allowed round. The fixes are verified by their tests and both suites.
