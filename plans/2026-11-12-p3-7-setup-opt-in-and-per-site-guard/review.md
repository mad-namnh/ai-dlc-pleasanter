# Review — P3-7 setup opt-in and per-site guard (Critical)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; two rounds (the limit); working tree against `9dc2eae`.

## Round 1 — accept with fixes (0 Critical, 0 High, 2 Medium, 5 Low)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | Restores still sent after the guard stopped holding (changed-site and HTTP≠200 paths) | Fixed: guard before every site and before restoring (`guard_stop`); tests |
| F2 | Medium | Unreadable `environments.json` mid-release left `applying` | Fixed: `write_guard_now` turns Fail/ValueError/OSError into TransportError; test |
| F3 | Low | The apply command's handling of a guard refusal not tested end to end | Fixed: end-to-end tests through `pls apply` check plan.json, apply-log.json, writes |
| F4 | Low | Outcome message misleading after a guard stop | Fixed (own wording; completed in round 2) |
| F5 | Low | Per-site guard did not re-check G4; bootstrap / migrate once per command | G4 checked outside dev (test); bootstrap / migrate / runner: TD-39 |
| F6 | Low | Re-running setup with another URL offered the earlier yes | Fixed: an earlier yes only for the same URL; test |
| F7 | Low | Stale docs (TD-34/39 duplicate, ADR-0021 open question and As built, ADR-0014 TB-10, architecture, runner header, setup recovery row) | Fixed (round 2 finished the rest) |

## Round 2 — accept with fixes (0 Critical, 0 High, 0 Medium, 4 Low)

Round-1 findings verified fixed except the parts below. Reviewer ran: 481 OK (3.12), 481 OK skipped=2 (3.10), node 15; the 8 new tests fail on the parent; simulations on the fake server.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Low | After a guard stop with an equal read-back the message said "restored"; "STOPPED before" after a site's own failed write | Fixed: guard branch first, "no restore was sent, yet … read back equal", "STOPPED after the failed write of …"; tests |
| R2-2 | Low | Guard message for a refused apply never shown | Fixed: guard branch before `refused`; test (`still planned`) |
| R2-3 | Low | Restore after a changed site not re-checked against the guard | Fixed: `guard_stop` before that rollback; docs say "before restoring" |
| R2-4 | Low | ADR-0021 As built lines, ADR-0014 TB-10 first column, setup recovery wording, ADR-0008 pointer | Fixed, except ADR-0008: its key-file wording is in its Decision section (stop point 1) — waits for Nam's decision on ADR-0008, noted in ADR-0021 Follow-up |

No Critical or High finding was open after round 2; the round-2 Low fixes were verified by the Orchestrator (tests, suites), not by a third review (limit: 2 rounds).
