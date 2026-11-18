# Log — team rollout after the feature freeze

## 2026-11-18 — start (Nam: "bắt đầu đóng băng")

- Precondition: tree clean except two untracked plan folders that are not this task's (`plans/2026-11-12-permission-allow-list/`, `plans/2026-11-16-d42-screen-check/`, left untouched, Nam's choice). Nam committed the open work: `581bf7d` (KB D40 C), `7d6d32f` (settings deny rules). Suites before: Python 747 OK (exit 0), node 16/16.
- Plan committed: `7c2acb9`.
- Model: claude-opus-5-5 (main session) — Critical tier allowed.

## Phase 1 — gate model and stg control

### Trace (read-only)
- `profile set` accepts any approver of the effective profile for every field (`pls_profile_records.set_field`).
- G4 is required only when `environments.json` role is not `dev` (`pls.py` apply / bootstrap / migrate / test); `profile set role` writes that file → a G1–G3 approver could make stg count as dev and drop the G4 requirement. `assert_writable` still needs `allow_write` + a key in the local connection, so N12 (no stg key on dev machines) stops the write, but the shared `environments.json` would change for Nam too.
- **New bug:** the head form with a range, `G1–G3: A, B; G4: Nam`, is not recognised (`approvers` head regex has no range): the parts fall to the name form, so `B` gets all four gates and a name `G1–G3: A` appears. The list form `G1, G2, G3: A` is correct. Verified with `approvers()` on the three strings.

### Commits planned
1. `fix(pls)`: a gate range in the head form grants only those gates; a name with ":" grants nothing.
2. `feat(pls)`: G4 delegation with an end date (`G4 until YYYY-MM-DD: B`); Approvers / Operators / role changed only by a G4 approver without an end date; new permanent G4 approver refused; at least one kept. Gate records checked against the profile on the record's date. Docs: ADR-0020 "As built", `docs/setup.md`, HANDOFF.
3. Proposed patches (protected / Nam's): `templates/project/CLAUDE.md` (stage `project` without customer approval, Approvers example, Operators stg); ADR-0020 status and decision wording.

Scope note: Operators added to the owner-only fields (not named in the plan) — same stg-control hole (who confirms manual deploys on stg); reported to Nam.

### Commit 1 — range fix
- Tests `test_a_range_before_the_colon_grants_only_that_range`, `test_a_text_with_a_colon_is_never_a_name` (`test_gate.py`): FAIL on parent `7c2acb9` (5 failures, worktree `../_agent-scratch/parent-range`), pass after the fix.
- Suites: Python 3.12 749 OK (exit 0); Python 3.10.21 749 OK, 2 skipped (exit 0); node 16/16.
- Review: deferred to one review of phase 1 (commits 1 + 2) — Critical, one reviewer call.
