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

## Phase 5 — model per phase/skill (2026-11-18, Nam: "bat dau phase 5")

- Docs checked by two `claude-code-guide` lookups (haiku): skill `model:` lasts one turn; project settings `model` is the session default; `PreModelSwitch` (v2.1.251+) can deny a switch (`permissionDecision: "deny"`, reason shown to the person; timeout blocks; fallbacks and resume do not fire it; `to_model` is a model ID).
- Asked Nam with options; Nam: "1a, 3a"; on "is Opus for every phase overkill" — answered with the price table (claude-api skill: Opus 5.5 $4/$20, Sonnet 5.5 $2/$10 per MTok), the per-phase view, and that every eval ran on Opus; Nam: "a" → N24, ADR-0031.
- Built: `HK.model_switch`, `HK.project_model`, `DEFAULT_MODEL = "opus"`, PreModelSwitch entry, `pls hook model`; install writes `model` when absent. Tests `test_project_model.py`; `test_project_hooks.py` expectations extended with the new event and the `model` entry.
- Phase 5 round 1: accept with fixes (M1 lockout on `opusplan` / `opus[1m]`, L1, L2 fixed; L3 kept). Python 3.10 not verified (interpreter removed, as in phase 4).
- Phase 5 round 2: accept, no findings. Committed. Phase 5 done.
- 2026-11-18: Nam continues phase 6 from another account; HANDOFF "Next" line written.

## Phase 6 — CI (2026-11-18, Nam: "làm phase 6", new account)

- Plan: `phase-06-ci.md` (Standard). Parent `2e869bb`. No `.github/` before.
- Linux check before building: WSL Ubuntu 24.04, Python 3.12, clone of `2e869bb`: 810 OK (3 skipped — all "node not installed"). Hence node in every Python job.
- OS choice (decided, reported): Ubuntu 3.10 + 3.12, Windows 3.12 (team machines; Git Bash hook tests). Actions pinned by major tag, not SHA (SHAs not verifiable offline) — limit in the report.
- Built: `.github/workflows/framework-ci.yml`, `tools/pls/tests/test_framework_ci_workflow.py`; docs: architecture §7 portability, ADR-0016 Limits (3.10 bullet, not Decision/Status), HANDOFF.
- Suites: Windows Python 3.12 815 OK; Python 3.10.21 (uv, `../_agent-scratch/py310`) 815 OK (2 skipped); node pass, 0 fail. New test: 5 of 5 fail on parent `2e869bb` (worktree, removed).
- Freshness step on Linux: passes on the commit; fails (`git diff --exit-code`) when the committed impact-rules.md is stale.
- Not verifiable here: the workflow on GitHub runners (needs Nam's push, stop point 4).
- Review round 1 (pls-x-reviewer, sonnet, medium): accept; L1 fixed (job-scoped, comment-free checks; three mutations fail), L2 disposition (first GitHub run on Nam's push). Subagent calls 1/6, rounds 1/2.
- Final suites: Windows 3.12 815 OK, 3.10 815 OK (2 skipped), node 16/16.
- 2026-11-18 Nam (mid-task): "làm tuần tự cho đến hết các phase, khi gặp vấn đề cần confirm thì bạn phân tích và đưa ra quyết định hợp lý và làm tiếp, sáng mai tôi review report". Decisions from here are made by the Orchestrator and logged with their reasoning; hard stop points (push, protected paths, ADR acceptance, Pleasanter writes) stay open for Nam.
- Phase 6 committed `bb94661`. REPORT for phase 6 goes into the overnight report.

## Phase 7 — `pls status`, golden path, docs (2026-11-18, under Nam's "decide and continue")

- Plan: `phase-07-status-golden-path.md` (Standard), decisions recorded there.
- Built `pls_status.py` + `pls status`; tried on copies of `pls-demo-contracts` / `-equipment` / `-inquiry` (git-tracked files only, no `.pls/`): contracts → applied-differs dev release, then DES-001 awaiting G3; equipment / inquiry → Origin not recorded, then REQ / DES front-matter findings (TD-68). Two fixes from that run: traceability links count as design (17 REQs wrongly "no DES" on contracts), equal neighbouring states share one line.
- Found while writing the golden path: a cloned project has no command that writes `.pls/connections.json` → TD-74, manual step in the golden path (no feature during the freeze).
- HANDOFF: old file kept verbatim in `plans/handoff-history/2026-11-18-handoff-before-cleanup.md`; new HANDOFF = phases table, open items, recent changes, How we work, Rules that hold, What this is, Repositories.
- Suites before review round 1: 3.12 and 3.10 failed only `test_every_subcommand_is_classified` (new command not classified) → `status` added to LOCAL in `test_write_guards.py`. New status test fails on parent `bb94661` (module missing).
- Review round 1 (sonnet, medium): accept with fixes — H1 recovery states, M1 tests, L1 limit; fixed. Suites after the fix: 3.12 826 OK, 3.10 826 OK (2 skipped), node 16/16.
- Review round 2 (sonnet, medium): accept, two Lows kept (review.md). Subagent calls on phase 7: 2/6, rounds 2/2.
- Phase 7 committed `a3cd70d`.

## Phase 8 — evals (2026-11-18/19, under Nam's "decide and continue")

- Decision (Orchestrator, Nam delegated decisions): run the with-skill arm only, as phase 8 lists — k = 3 for lifecycle 0.33 (cases 001–009; 010/011 are selection cases, a separate batch kind, not run), P1 0.8 (001, 002; 003 interview last), P2 0.14 (001, 002); k = 1 for onboarding, P3 config-builder, script-engineer, P5. No baseline / selection batch (ADR-0030 requires Nam per batch; not needed by the plan).
- Runner model: inherited, claude-opus-5-5 (ADR-0031 project model).
- Relay rule applied: `pls status`, `check p1`, `step` refused — they are not on the runner's local-only list (finding: the list predates `pls status`; proposal for Nam).
- Lifecycle 0.33 rounds 1–3 graded (scratchpad notes → result file): 001–007, 009 3/3 PASS; 008 2/3 — run 3 (r-2577) wrote `gates/` records with invented quotes to build the premise (Must-not). Case 008 input clarified (gate records and `.pls/connections.json` stay premises; setup.md note); 008 rerun ×3 started (r-bc1a, …).
- P1 / P2 round 1 started (r-99e8, r-03c4, r-1693, r-1e30) from templates built under `../_agent-scratch/tpl/` from `pls-demo-inquiry` commits per each case's setup.md (`539b61f`, `b70c810`, `3cf2c45`, `021a0d0`, rollback payloads of R-20261105-01 / -05 unpacked).
- 2026-11-19 ~03:00: usage limit hit (5-hour); runs resumed after reset.
- Lifecycle 0.33 batch done (k = 3 on 001–009, 008 rerun ×3 on the clarified input): `evals/results/pls-x-lifecycle/2026-11-19-v033.md`.
- P2 0.14: 001 3/3, 002 3/3 (rubric item 4 predates ADR-0028, graded met; proposal). Orchestrator relay error on r-80e5 (xref relayed before running it there) — corrected, noted in the result.
- P1 0.8: 001 3/3, 002 2/3 (r-cffb FAIL: 対応回数 not protected by an AC/derived REQ), 003 1 run PASS (note), runs 2–3 not run. Found TD-75 (interview source list split at the comma → `check p1` findings). Second usage limit ~08:00.
- Not run in phase 8: P1 case 003 runs 2–3; k = 1 evals of onboarding, P3 config-builder, P3 script-engineer, P5 — stopped for the usage limits and the morning review.
- Eval results committed `65301a7`; HANDOFF and runner-list patch `9e0cd04`. Phase 9 not started (stopped for the morning review and the usage limits). Subagent calls: reviewers 3 (phase 6: 1, phase 7: 2), eval runners 46 incl. resumes, person-role 1.
- REPORT SENT (2026-11-19 overnight report).

## Phase 9 — scheduled drift check (2026-11-19, Nam: "tiep thuc lam task")

- Model: claude-opus-5-5 (main session).
- Decisions asked upfront (options with a recommendation); Nam chose the recommended one each time → N25:
  1. Order: phase 9 first; the rest of phase 8 (P1 003 runs 2–3, k = 1 of onboarding, P3 ×2, P5) after it, before phase 10.
  2. Schedule: every 2 hours, Mon–Fri 9:00–19:00.
  3. Session start: the hook shows the last result with its time; when that result is older than 2 hours it starts a check in the background (does not block the session).
  4. Registering the job (`schtasks /create`): the agent writes code and tests only (tests check the command text, nothing registered); Nam runs the install in phase 10 with paste-ready commands.
- Built: `pls drift-watch run|show|install|remove` (`pls_drift_watch.py`, `pls_drift_watch_schedule.py`), hook start shows the last result / starts a stale one in the background; `run` / `show` not in the run log (ADR-0013 amendment line). Decisions D1–D7 in `phase-09-drift-watch.md`.
- New test file fails on parent `0a008ae` (module missing; worktree, removed).
- Review round 1 (pls-x-reviewer, sonnet, medium): accept with fixes, no Critical/High; L2 fixed with a test, L3/L4 documented, L5 kept (review.md). Round 2 not run (Low fixes only).
- Suites after fixes: Python 3.12 848 OK (exit 0), 3.10.21 848 OK (2 skipped, exit 0), node 16/16. Subagent calls phase 9: 1/6.
