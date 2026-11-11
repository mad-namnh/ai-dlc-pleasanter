# Review — `pls test-users` (ADR-0018 C + ADR-0019 B)

## Round 1
- Reviewer: `pls-x-reviewer`, opus, effort high; working tree against `f9d6ddf`. git status hash identical before and after.
- Verdict: **accept with fixes** — 1 High, 5 Medium, 2 Low groups.
- Reviewer ran: 3.12 suite (427 OK), node (15), offline experiments exp1–exp4 against the suite's 127.0.0.1 fake, mutation runs M1–M11 on copies (M10, M11 not caught).

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | High | A key could be issued (write) with no typed confirmation: "issue key" planned only on a missing file, a stale key re-issued in the run | Fixed: `plan_roles` checks the key with the API (`key_ok`); every Pleasanter write is in the confirmation (`pending`); the run issues only what was planned. Test `test_a_stale_key_is_reissued_only_after_the_confirmation` |
| F2 | Medium | The value of an existing `keys.<role>` was echoed in a refusal (and the run log) | Fixed: messages name the role only; tests assert the value is absent |
| F3 | Medium | With `PLS_CONNECTIONS` the key reference went to the wrong file and secrets outside `.pls/` | Fixed: uses `H.connections_file(r)` and refuses a connections file that is not the project's `.pls/connections.json`. Test `test_a_connections_file_outside_the_project_is_refused` |
| F4 | Medium | An unanswered group update lost the earlier-list report | Fixed: the update is read back and checked the same way after any exception. Test `test_an_unanswered_group_update_is_read_back_and_a_loss_reported` |
| F5 | Medium | Candidate key check not proven (mutations M10/M11 survived) | Fixed: tests with a new key-shaped non-key token before the key, and with two accepted candidates (person step) |
| F6 | Medium | Inventory did not lock the mid-level writers | Fixed: helpers renamed (`write_test_users`, `add_test_user_to_group`, `issue_test_user_key`, `ScreenSession.issue_api_key`), each locked to its caller; calls through `TU.` and `s.` are checked |
| F7a | Low | ADR-0017 status said ADR-0019 not built | Fixed |
| F7b | Low | ADR-0018 option text names `.pls/keys/…`; open question on file names / `keys.<role>` / password file unchecked (Nam's build decisions only in the plan) | **Open — ADR text beyond the status line is a stop point; asked Nam** |
| F7c | Low | TB-14 said groups never updated; updates appended to the status cell | Fixed: moved into the controls column, TB-14 text corrected |
| F7d | Low | plan.md / HANDOFF said "decided, not built" and "built" together | Fixed |
| F7e | Low | `docs/setup.md` said role tests come later | Fixed |
| F7f | Low | D32 has no kb-verify probe though ADR-0018 speaks of kb-verify confirming it; D32 row order | Order kept (table is not ordered); the wording is ADR-0018 text → **asked Nam with F7b** |
| F8 | Low | ready-exit without key check; shared group refused; LoginId from folder name; existing user flags; TenantManager not asserted; confirmation wording; `writes()` regex | Fixed: ready requires a working key; roles sharing a group re-read it (test); existing test user that is tenant manager or disabled refused (test); create body asserted; wording; regex. Folder-name LoginId: noted for TD-24 / not changed |

Re-verified after fixes: 3.12 435 OK, 3.10 435 OK (2 skipped), node 15; on parent `f9d6ddf` 30 of 30 new test-users tests fail, write_guards 1 FAIL + 1 ERROR.

## Round 2
- Reviewer: `pls-x-reviewer`, opus, effort high; whole change against `f9d6ddf`; git status hash identical before and after.
- Verdict: **accept with fixes** — 1 Medium, 5 Low. Round 1: F1, F2, F3, F5, F6, F7a/c/d/e resolved; F4 partly (R2-1); F8 mostly (R2-3). 23 mutations, 19 caught, 3 survived (R2-3).

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| R2-1 | Medium | After an unanswered update, a read-back failing at transport level lost the earlier member list | Fixed: any read-back failure keeps the earlier list in the refusal. Test `test_a_failed_read_back_after_an_unanswered_update_still_shows_the_list_before` |
| R2-2 | Low | `key_works` accepts any valid key | Fixed in part: the operator's own key in a key file is refused (test); person step says "log out first"; owner identity → ADR-0018 open question (not guessed) |
| R2-3 | Low | Three mutation survivors: fallback-B completion, disabled user, `known` filter | Fixed: tests for each |
| R2-4 | Low | D32 missing → issuing allowed; missing Body sent as null | Fixed: `screen_path_verified` requires the entry (unit test); a read without GroupName/Body is refused (test) |
| R2-5 | Low | A join not in the confirmation could be written (shared group, concurrent edit) | Fixed: joins only where planned (`join_planned`); otherwise a person step. No dedicated test (needs a concurrent edit between two roles) |
| R2-6 | Low | Confirmation asked when only a person step is left | Fixed: person steps are not in the confirmation. Test `test_an_unverified_version_asks_no_confirmation_when_only_a_person_step_is_left` |

F7b/F7f: Nam chose "edit as built" — ADR-0018 paths, open questions (Nam's three decisions), `verified_on` of D32 instead of kb-verify; new open question on key ownership.
Re-verified: 3.12 443 OK, 3.10 443 OK (2 skipped), node 15. Review rounds 2 of 2 used; the round-2 fixes are not re-reviewed independently. No Critical or High open.
