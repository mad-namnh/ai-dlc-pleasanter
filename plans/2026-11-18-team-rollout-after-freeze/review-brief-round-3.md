# Brief for the independent review, round 3 (run by Nam from another account)

Give this file's brief to the subagent `pls-x-reviewer` (or a fresh session acting as reviewer) — nothing else from the implementing session.

- **Task statement:** Phase 1 of `plans/2026-11-18-team-rollout-after-freeze/plan.md` ("Gate model and stg control"), decided by Nam: every dev approves G1–G3 (their own tasks included); G4 only Nam; Nam may delegate G4, always with an end date; only Nam may delegate; the customer approves no gate; the main control for stg writes is the stg write key, held only by Nam or a time-boxed delegate. Decisions after review rounds 1 and 2 (Nam, verbatim): "F1 a, F3 a"; "1 đồng ý, 2a, 3 đồng ý" — as listed in `plans/2026-11-18-team-rollout-after-freeze/review.md`:
  - F1 a: a gate record (and a `jobs-verified` confirmation) is judged by the Approvers value in force at its instant;
  - F3 a: a profile with approvers but no G4 approver without an end date refuses every change of Approvers / Operators / role, with a lint finding;
  - R2-3: only a date-like token or a colon makes a text "not a name" (`dev01` is a name); a first Approvers value only while there is no Approvers record and the row grants nothing;
  - R2-4 a: a role in `environments.json` that differs from its role record refuses every command that reads the environment;
  - R2-6: the no-owner repair adds a record by hand and keeps the earlier records.
- **Acceptance criteria:**
  1. Approvers, Operators and any environment role are changed only by a G4 approver without an end date; a G1–G3 approver and a time-boxed delegate are refused; new tests fail on the parent commit `8aebd8a`.
  2. G4 delegation requires an end date, ends by itself, cannot be granted without one to a new name, cannot be passed on by the delegate; early revoke by a new `profile set`.
  3. Every decision above is built and tested; round-2 findings R2-1, R2-2, R2-5 fixed; R2-7, R2-8 documented.
  4. `docs/setup.md` and ADR-0020 "As built" describe the behaviour; ADR-0020 Status and Decision lines unchanged.
  5. The proposed patch `plans/2026-11-18-team-rollout-after-freeze/proposed-templates-project-CLAUDE.md.patch` (protected path, not applied) matches the decisions.
  6. No test weakened; both suites green (Python 3.12 and 3.10, node).
- **Change to review:** commit range `7c2acb9..HEAD` (`8aebd8a`) plus the working tree against `HEAD`. Earlier rounds: `plans/2026-11-18-team-rollout-after-freeze/review.md`. Not part of the change: `plans/2026-11-12-permission-allow-list/`, `plans/2026-11-16-d42-screen-check/`.
- **Rules that apply:** `CLAUDE.md`, `docs/agent-rules.md`, `docs/review-criteria.md` (criteria: choose), ADRs: 0014, 0020, 0021, 0024.
- **Commands you may run:** read-only git (`diff`, `log`, `show`, `status`), reading files, `python -m unittest discover -s tools/pls/tests`, `node --test tools/pls/tests/test_runner.mjs`
- **You must not:** edit, create or delete any file; stage or commit; run a state-changing command; contact Pleasanter
- **Return:** verdict (accept / accept with fixes / reject); findings, each with severity (Critical / High / Medium / Low), evidence (`file:line`, command and output) and the failure scenario; for each round-2 finding: fixed or not; what you ran; what you could not verify
