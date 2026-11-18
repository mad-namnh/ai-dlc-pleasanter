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

### Commit 2 — delegation and owner-only changes (not committed)
- Round 1 review: accept with fixes (F1–F7). Nam: "F1 a, F3 a". Fixed F1–F7; suites: Python 3.12 765 OK, 3.10 765 OK (2 skipped), node 16/16; new test file vs parent `8aebd8a`: 17 failures/errors of 18 results.
- Round 2 review: accept with fixes, no Critical/High; R2-1…R2-4 Medium open, R2-5…R2-9 Low (`review.md`).
- Budget: reviewer calls 2 of 2 rounds; subagent calls 2 of 6. **Stopped** (agent-rules §5): work kept uncommitted in the tree; decisions asked of Nam (R2-3 digit rule, R2-4 guard, a third review round).
- Nam (verbatim): "1 đồng ý, 2a, 3 đồng ý, 4 sua xong stop, toi chuyen account run review" — fix R2-1…R2-8, then stop; Nam runs round 3 from another account.
- Fixed: R2-1 (package approvers at the G4 record's time, test in `test_package_and_verify.py`), R2-2 (jobs-verified test), R2-3 (date-like names only; first value only from a placeholder row without record; tests), R2-4 a (`role_record_problem` in `env_conf` and `principals --create`; tests), R2-5 (lint names from the Approvers history), R2-6 (repair adds a record), R2-7 / R2-8 documented (ADR-0020), setup troubleshooting row.
- Suites: Python 3.12 771 OK (exit 0); node 16/16; Python 3.10 771 OK, 2 skipped (run before the last added assertion; the new test file re-run on 3.10: 21 OK). New test file vs parent `8aebd8a`: 20 failures/errors of 21 tests.
- Template patch `proposed-templates-project-CLAUDE.md.patch`: `git apply --check` OK; full suite with it applied in `../_agent-scratch/tpl-check`: 771 OK.
- **Stopped, not committed.** Round 3 brief: `review-brief-round-3.md`. After an accept: commit 2 (code + tests + docs + plan files), then Nam applies the template patch.
- Correction (review L-4): on the parent `8aebd8a`, 18 of the 21 tests of the new file fail; 3 pass as regression guards (`test_an_approval_dated_after_the_delegation_does_not`, `test_a_name_with_digits_is_a_name`, `test_a_recorded_value_is_never_replaced_as_a_first_value`). Earlier "20 of 21" counted subtests.
- Round 3 (Nam allowed it in this session): accept with fixes, Low only (`review.md`). Commit 2 = the reviewed tree. Reviewer calls: 3 (third allowed by Nam).
- ADR-0020 accepted by Nam (verbatim "chap nhan ADR20"): Status, Decision (option C, team rules), ADR-0012 Status pointer, ADR index, architecture §4 gate table (review L-4), TD-35. Suites: Python 771 OK, node 16/16.
- Follow-up L-1…L-3 (Nam "chon a"): suites Python 3.12 773 OK, 3.10 773 OK (2 skipped), node 16/16; L-1 / L-3 tests fail on parent `cc8a649` (2 failures), the L-2 test passes there (guards R2-5). Review: accept with fixes, N-1…N-3 Low. Reviewer calls on phase 1: 4 + this one = 5 of 6.
- N-1…N-3: suites Python 3.12 775 OK, 3.10 775 OK (2 skipped), node 16/16. Review: accept. Subagent calls on phase 1: 6 of 6 (Nam allowed the third review round). Phase 1 done.

## Phase 2 — shared project repository (2026-11-18, Nam: "bat dau phase 2")

- Trace (read-only): `pls coverage` reads `tests/results/` (`pls.py` `test_results`); `pls check p1` needs each REQ's source under `requirements/sources/` (`pls_phase_check.py:151`) → N11 as written would refuse G1 / weaken G3 evidence on another machine. `ops/log/` read only by `usage collect` (own actor); `design/probes/`, `ops/xref/`, `ops/adopt/`, `ops/triage/`, `ops/env-compare/` read by no check (skills read xref / adopt; both regenerable).
- Asked Nam with options; Nam: "chon a" → N21 (plan updated).
- Phase 2 built: template `.gitignore` (four folders), test `test_project_gitignore_keeps_what_pls_reads.py` (fails before the change: the four folders not ignored), architecture §3.2, setup.md, skills P6 0.4 / lifecycle 0.32 / spec-recovery 0.5, layout patch for the protected template. Suites: Python 3.12 777 OK, 3.10 777 OK (2 skipped), node 16/16; with the patch applied 777 OK. Review: accept with fixes (`review.md` "Phase 2").
- P2-2 (Light, wording): onboarding 0.8 — adopt report local; Python 777 OK, node 16/16; no review (Light). Phase 2 done; pending Nam: apply proposed-templates-project-CLAUDE-layout.patch.

## Phase 3 — per-developer sandboxes (2026-11-18, Nam: "bat dau phase 3")

- Read ADR-0011 and `sandbox_*`, `harvest`, `principals`, `test-users`: create / refresh / drop / harvest / merge built; refresh's release plan already refuses unharvested sandbox edits (drift). Asked four decisions; Nam: "1a 2a 3a 4a" → N22.
- Built: `sandbox sync` (refresh + apply), `principals --create --test-users` (one confirmation), template ignores `releases/R-*-dev-*/`, `releases/B-*-dev-*/`; ADR-0011 accepted; TD-72; architecture, setup, skills lifecycle 0.33 / script-engineer 0.7 / config-builder 0.12.
- New tests fail on the parent `00271c0` (sync, A4, gitignore: 3 of 3), pass after.
- Round 1 of phase 3: accept with fixes (H1, H2, M1 fixed; L1–L3 dispositions in review.md). Suites: 3.12 782 OK, 3.10 782 OK (2 skipped), node 16/16; the 5 new tests fail on the parent 00271c0.
- Phase 3 round 2: accept with fixes; R2-1 High open in the combined principals/test-users confirmation → stop point 8; asked Nam. Uncommitted.
- Nam: "a" → A4 dropped (code, tests, docs reverted to HEAD for principals / test-users; lifecycle skill back to 0.32); R2-3, R2-5 fixed; R2-4 kept as documentation.
- Final: suites 3.12 780 OK, 3.10 780 OK (2 skipped), node 16/16; sync tests fail on parent 00271c0. Committed. Phase 3 done.

## Phase 4 — version pinning, hotfix, changelog (2026-11-18, Nam: "bat dau"; decisions "1a 2a 3a" → N23)

- Found: the lock already records the commit; `skills check` already reports skill and template drift. Built: `pls_framework_pin.py` (state, problem, newer release, session notes); lock `tag` and `dirty`; `pin_guard` in `write_guard_now` and before tests that change records outside dev; `http-check` line; SessionStart hook `pls hook start` (docs checked by a `claude-code-guide` agent, haiku: event and matchers exist, plain stdout goes to the context, failure behaviour not documented → `|| true`, advisory). Pin notes kept out of `skills check` so the suite does not depend on this checkout's git state.
- Docs: `CHANGELOG.md` (v0.3.0), ADR-0022 "Pinned framework" + open question 1 answered (Status left Proposed — Nam's), architecture, setup "Framework versions".
- Phase 4 round 1: accept with fixes (F1 High fixed; F2–F11 fixed or disposed; F3 Decision/TB-6 asked of Nam; F4 → TD-73).
- Phase 4 round 2: accept with fixes, Low only. Reviewed tree committed; L1–L5 and ADR-0022 acceptance (Nam: "a") in a follow-up.
- Follow-up: L1 (stg migrate e2e, confirmation patched to fail), L2 (malformed lock → message), L3 (--untracked-files=all; skip-worktree in limits), L4 (sync warning and http-check line tested; failed rev-parse → unknown), L5 (docs: ADR-0022 full hash, architecture rows, setup lock row); ADR-0022 Accepted option B and ADR-0014 TB-6 text (Nam: "a").
- The question Nam answered "a" (2026-11-18, asked in Vietnamese; options as asked, translated): the Decision of ADR-0022 still says option A (tool not pinned) and ADR-0014 TB-6 says "tool code is not hashed"; (a) recommended: accept ADR-0022 with Decision "option B: pin by commit, writes to stg refused on a difference" (as N23) and update TB-6 to "handled by the framework pin (ADR-0022)"; (b) leave both, decide later. Nam: "a".
- Follow-up review: accept with fixes, Low only (R2-1…R2-6), all fixed in the same commit: a non-string tag refuses (test with the running commit equal to the pin); tests for `_framework_commit` (exit 128 / "HEAD"), the sync warning for an unknown commit, and `--untracked-files=all`; ADR-0022 Consequences and the `skills/README.md` pointer; TB-6 "Not covered"; a non-object lock is rewritten by sync and reported by check; this question recorded.
- Final suites of the follow-up: Python 3.12 803 OK, node 16/16; **Python 3.10 not verified** — its interpreter was installed in another session's scratchpad, which was removed (`py -0` lists it, it does not start); new tests fail on the parent 41d5852 (5 of the new cases). Phase 4 done; tag v0.3.0 on this commit.
