# Review — TD-39 write guard before every bootstrap site and migration (Critical)

## Round 1 — accept with fixes (0 Critical, 0 High, 1 Medium, 3 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `2930a42`; `git status` and a hash of the diff equal before and after.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | After a guard stop, `migrate` said "run migrate again", but the re-run was refused (m1 "already migrated — never sent twice") and `apply` refused (m2 pending): the release was stuck | Fixed: a forward re-run skips folders whose last forward run is `migrated` (printed, never sent twice) and runs only the rest; all already migrated → still refused, with "next: pls apply"; `uncertain` / `migrating` still refuse. Test: stop → guard back → re-run sends only m2 → a third run is refused → `apply` writes |
| F2 | Low | `docs/setup.md` still said bootstrap / migrate check the guard once | Fixed |
| F3 | Low | No tests for migrate role change, stg migrate with G4 removed, normal stg runs; weak role-change assertions | Tests added (stg normal migrate and bootstrap under their G4, stg migrate G4 removed, migrate role → prod; role-change test now checks the stop line and no `uncertain`) |
| F4 | Low | Double period; bootstrap stop gave no next step | Fixed: message trimmed; the bootstrap stop line says the created sites are bound and a re-run creates only the sites without an id |

## Round 2 (final) — accept with fixes (0 Critical, 0 High, 1 Medium, 3 Low)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Medium | The new resume rule skipped a folder whose forward run was `migrated` even after a later `--rollback`, sent the others and pointed to `apply` (reproduced by the reviewer) | Fixed: a folder with any rollback run is never skipped (falls to `state_problem` → refused, no "next: pls apply"); tests: forward → rollback → forward refused without the apply hint; the reviewer's mixed state refused with nothing sent |
| R2-2 | Low | `migrate --rollback` after a guard stop refuses the whole release (a folder never migrated) | Recorded: new TD-40 (with `pending` ignoring rollbacks); fails safe |
| R2-3 | Low | Resume rule missing in the architecture migrate row; failed→resume untested | Fixed: row says it; test (m1 migrated, m2 failed → re-run sends only m2) |
| R2-4 | Low | Bootstrap stop line said the sites "are bound" before `bind` ran | Fixed: "are bound next" |

Not reviewed again: round 2 was the last allowed round; the fixes are verified by their tests and both suites.
