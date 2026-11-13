# Review — TD-24 `pls test-users --remove` (Critical)

## Round 1 — accept with fixes (0 Critical, 0 High, 1 Medium, 7 Low) — fixed 2026-11-13 (see round 2)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `17987f4`; `git status` and a hash of the diff equal before and after.

| ID | Severity | Finding | Planned fix |
|---|---|---|---|
| M1 | Medium | A password file does not prove the user found by LoginId is the one this machine created: machine A's stale file (user deleted by hand, files kept) + a new user made by operator B → A's `--remove` deletes B's user (tenant-wide, irreversible). Same weak check on create (`pls_test_users.py:205`) | Before deleting, require proof: the stored key works for that user (`TU.key_works` → 200; a key dies with its user, KB api.md:103), else PERSON STEP; or record the created uid next to the password file and require a match. Fix help text / docstring; note the limit in TD-24 |
| L1 | Low | `test_remove_…:54-56` takes `n` after the second remove — the assertion can never fail | take `n` before |
| L2 | Low | `pls_test_users.py:12` docstring says removal is not built | update |
| L3 | Low | ADR-0014 TB-14 and ADR-0019 common rules do not cover deleting users / dropping their membership — TB-14 is in a Decision section (stop point) | propose wording to Nam; note outside Decision |
| L4 | Low | Roles renamed / dropped from `design/roles.json` are not offered for removal, silently | list unmatched `.pls/test-users/<env>-*.password` as person notes |
| L5 | Low | Run log: removal logs LoginId, creation logs uid | log the uid (and LoginId) |
| L6 | Low | Inventory allows any `remove_test_users` to call itself (two functions share the name) | rename `TR.remove_test_users` (e.g. `delete_and_clean`), tighten the inventory |
| L7 | Low | Lifecycle skill names `test-users` but not `--remove` / no `--yes` by agents | add a line (skill version bump) |

## Round 2 (last) — accept with fixes (0 Critical, 0 High, 0 Medium, 5 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `fcdd0b2`. TD-24 files equal before and after (hash of `git diff` without `.claude/settings.json`, hashes of the new files). `.claude/settings.json` was modified at 12:25:33 during the review by neither the reviewer nor the Orchestrator (adds `$schema` and nine `Read(...)` deny rules): not part of TD-24, stop point 1.3 / 1.9, kept out of the commit, reported to Nam.

Round 1: M1 fixed (rename gap → L-C); L1, L2, L5, L6, L7 fixed; L3 dispositioned (proposed patches, `git apply --check` OK); L4 fixed for password files (rest → L-E).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L-A | Low | uid of a delete answered 200 is not logged when the lookup afterwards fails or still finds the user (`pls_test_users_removal.py` delete_and_clean) | fixed: metric `test_users_delete_answered` logged on HTTP 200, before the check; tested |
| L-B | Low | write guard read once before the confirmation; not re-read before each `delete_user` (TD-39 covers apply/bootstrap/migrate only; `test-users` create/remove and `principals --create` not named) | Nam 2026-11-13: tech debt → TD-41 |
| L-C | Low | ownership proof shows the key belongs to *a* live user, not to the uid found: test user renamed in Pleasanter + new user with the old LoginId → the new user is deleted / joined | documented as a limit: module docstring, TD-24 row, ADR-0018 note |
| L-D | Low | plan.md (Change, acceptance 3), review.md round 1 header, HANDOFF.md:7,9 stale after commit | fixed in the same commit |
| L-E | Low | leftover key file / `keys.<role>` of a dropped role reported only with its password file; create path on an unverified version gives two PERSON STEP lines, the second unclear | fixed: key files and references of dropped roles reported (tested); the line names the next step |

Acceptance 1–4, 6 met; 5: suites met; parent check run by the Orchestrator (log), not by the reviewer.
