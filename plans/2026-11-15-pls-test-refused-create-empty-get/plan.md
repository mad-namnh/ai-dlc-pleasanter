# Plan — `pls test`: a refused create and a get without a record

- **Tier:** Standard (test runner over the guarded HTTP transport; no guard or gate touched).
- **Source:** trial `pls-trial-store-promo` `design/probes/2026-11-15-budget-script-probe.md` §1, §4: (a) a `get` step answered HTTP 200 with an empty `Data` list raised `IndexError` (pls_http.py) and the run wrote no result file; (b) a create refused by a server script came back with the target site's own id (`create → 44971`, the site id), was saved as the record id, and the following `delete 44971` got HTTP 404.
- **Change:** `run_tests` (pls_http.py) and the browser runner (pls-runner.js), same rule: a create is a new record only on HTTP 200 with an `Id` other than the target site's id, otherwise a step error; a `get` with no record in `Data` is a step error. The run continues with the next spec and writes its result file.
- **Not known:** the HTTP status of the refused create on 1.5.2.0 (the trial log did not record it) — the rule does not depend on it.
- **Acceptance:** (1) empty get → spec status `error`, result file written; (2) refused create (site id, or non-200) → `error`, no later step acts on the id; (3) browser runner same; (4) new tests fail on the parent; (5) suites green incl. 3.10; (6) review: no open Critical/High.
