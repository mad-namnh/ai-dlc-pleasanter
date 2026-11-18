# Review — phase 1 (gate model and stg control)

## Round 1 — 2026-11-18

- Reviewer: `pls-x-reviewer`, model opus, effort high. Change: `7c2acb9..HEAD` (`8aebd8a`) + working tree against HEAD.
- `git status` before and after the call: identical.
- Verdict: **accept with fixes**. No Critical / High.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | Ended grants must be dropped from the row (`_check_owner` refuses a past end date), and `require` reads the current row: a delegate's G4 on a release stops counting after any later Approvers change — docs (setup, ADR-0020) say it stays approved | Nam's decision (approver rule) |
| F2 | Medium | `G4: Nam, Taro until 2026-12-05` makes the name `Taro until 2026-12-05` a permanent G4 holder; in a first value it becomes an owner | fix: a name with `until`, a digit or `:` grants nothing; test |
| F3 | Medium | A profile with no permanent G4 holder keeps the earlier rule: any approver may make themselves owner; untested | Nam's decision |
| F4 | Low | No test: delegate changing `role` / `Operators`; early revoke | fix: tests |
| F5 | Low | CLI help `--approver`, `architecture.md` command row; owner set only shrinks through `pls` — undocumented | fix: text |
| F6 | Low | `jobs-verified` by a delegate re-checked against today | with F1 |
| F7 | Low | A former delegate can hand-write a backdated record (within TB-3) | fix: one sentence in ADR-0020 |

Commands run by the reviewer: full Python suite (760 OK), node (16 pass), new tests against parent code in memory (11 of 12 fail; `test_an_approval_dated_after_the_delegation_does_not` passes on the parent for another reason), probes of `grants` / `approvers` / `owners` / `_check_owner`. Not verified: Python 3.10 (the Orchestrator ran it: 760 OK, 2 skipped), lifecycle eval inputs with a non-owner changing Operators.

## Round 2 — 2026-11-18

- Reviewer: `pls-x-reviewer`, model opus, effort high. Same change, after the fixes for F1 (a), F3 (a) (Nam: "F1 a, F3 a"), F2, F4–F7.
- `git status` before and after: identical. Verdict: **accept with fixes**. No Critical / High.
- Round-1: F1 fixed (except package, lint), F2 fixed (side effect R2-3), F3 fixed (gap R2-3), F4, F5, F7 fixed, F6 fixed without a test.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Medium | `pls package` lists today's G4 approvers; `verify.py` then refuses a delegate's G4 after the delegation | open — fix proposed (profile at the record's time) |
| R2-2 | Medium | F6 (`jobs-verified` at its time) has no test; mutant survives | open — test |
| R2-3 | Medium | Names with a digit now grant nothing (`dev01`); an all-digit-name or expired-only row then counts as "no value yet" → anyone states a first value and becomes owner | open — Nam: digit rule; `first` from "no record and placeholder row" |
| R2-4 | Medium | A hand edit of `environments.json` role still drops the G4 requirement (guards read the file; the record only feeds dev-writes); ADR text claims more | open — Nam: guard (refuse on file/record mismatch) or wording + TD |
| R2-5 | Low | L-GATE-01 checks names against today's row, not the record's time | open — fix |
| R2-6 | Low | F3 repair (move Approvers records out) removes the history F1 relies on | open — document / other repair |
| R2-7 | Low | A gate record older than the first Approvers record is judged by today's row | open — document |
| R2-8 | Low | `Taro (G1–G3, G4 until D)` time-boxes all four | open — document |
| R2-9 | Low | One new test passes on the parent for another reason | noted |

Review budget reached (2 rounds, agent-rules §5). Stopped; reported to Nam.

## Round 3 — 2026-11-18 (Nam: "thực hiện tiếp trong session này" — a third round allowed)

- Reviewer: `pls-x-reviewer`, model opus, effort high, brief `review-brief-round-3.md` only. `git status` before and after: identical.
- Verdict: **accept with fixes**. No Critical / High / Medium. Round 2: R2-1, R2-2, R2-3, R2-6 fixed; R2-4 fixed with a gap (L-3); R2-5 fixed untested (L-2); R2-7, R2-8 documented.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L-1 | Low | An instant before the first Approvers record is judged by the CLAUDE.md row, which a hand edit can change (with a backdated hand-written record) | follow-up commit: earliest record for instants before it (Critical tier → reviewed) |
| L-2 | Low | R2-5 lint fix has no test; looser than "value at the record's time" | follow-up commit: test |
| L-3 | Low | `principals` without `--create` does not check the role record | follow-up commit: check at the top of `bind_principals` |
| L-4 | Low | Log count of parent failures (subtests counted); `docs/architecture.md` gate table still names the customer for G1 / G4 (N5) | log corrected here; table → Nam with ADR-0020 acceptance |
| — | none | `grants()` also drops a name containing "until" (safer than R2-3's wording) | documented in the follow-up |

Commit 2 is the reviewed tree, unchanged.

## Follow-up L-1…L-3 — 2026-11-18 (Nam: "chon a")

- Reviewer: `pls-x-reviewer`, opus, high. Change: working tree against `cc8a649`. `git status` before/after identical.
- Verdict: **accept with fixes**, Low only. L-1 and L-3 correct and tested (both new tests fail on the parent `cc8a649`, run by the Orchestrator in `../_agent-scratch/parent-low`).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| N-1 | Low | lint `held_then` accepts a name that held any gate, ADR says "the gate" (lint only; `require` checks per gate) | next commit: check the gate |
| N-2 | Low | the L-2 narrowing has no test (the new test also passes on the parent) | next commit: tests for a historic name not in force and a holder of another gate |
| N-3 | Low | ADR omits the "until" word rule; long docstring line | next commit: wording |

The reviewed tree is committed unchanged.

## Follow-up N-1…N-3 — 2026-11-18

- Reviewer: `pls-x-reviewer`, sonnet, medium (Standard: lint and wording only). Change: working tree against `29ac7e8`. `git status` before/after identical.
- Verdict: **accept**. Low-1 cosmetic (one blank line before a class) — left as is. N-1 test fails on the parent `29ac7e8`; the N-2 test fails on `cc8a649` (before the L-2 narrowing) — both run by the Orchestrator.
- Note from the reviewer: the tests order records with `time.sleep(0.05)`; passed on Windows.

## Phase 2 — 2026-11-18

- Reviewer: `pls-x-reviewer`, sonnet, medium (Standard). Change: working tree against `87cacfb`. `git status` before/after identical.
- Verdict: **accept with fixes**.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| P2-1 | Medium | setup.md says `pls skills check` reports a changed template `.gitignore` — unverified | verified by code: `_template_hashes` hashes every file of `templates/project` (`rglob("*")` includes dotfiles) and the check reports `templates/project/<file>: changed` against the lock (`tools/pls/pls.py:2667-2681`); no change |
| P2-2 | Low | `pls-x-onboarding` step 3 still reads like the adopt report is committed | next Light commit: "(local, gitignored)", version 0.8 |
| P2-3 | Low | template `CLAUDE.md` layout table contradicts `.gitignore` until Nam applies the patch | pending Nam; `git apply --check` OK and full suite with the patch applied 777 OK (`../_agent-scratch/p2-tpl`) |

## Phase 3, round 1 — 2026-11-18

- Reviewer: `pls-x-reviewer`, opus, high. Change: working tree against `00271c0`. `git status` before/after identical. Verdict: **accept with fixes**.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| H1 | High | the sync drift test passed through a release-id collision (ids per second), not the drift check | fixed: `_stamp` patched per call; asserts the drift refusal text, no new plan, no updatesite; control sync without an edit applies (exit 0); found and fixed on the way: the fake's createsite site had no `Body` (a real getsite always has one), which made every second plan a false drift |
| H2 | High | the one confirmation of `principals --create --test-users` listed nothing and came before several refusals (ADR-0017 rules 2, 4; ADR-0018) | fixed: `test_users_guards` (dev, sandbox, roles, allow_write, connections file) run first; the confirmation of `bind_principals` lists the groups and the test-user logins; when no group is missing, test-users' own listing confirmation is the one; terminal test: one prompt, names shown, wrong answer writes nothing, a test-users refusal comes before the prompt |
| M1 | Medium | `sandbox` classified as a network read although `sync` writes | fixed: `sandbox` in WRITES / `pls_log.WRITING`; static lock for `main([...])` of a writing command inside pls; `sync` with `allow_write` off sends nothing |
| L1 | Low | ignore pattern by name; prod release not in the test | ADR-0011 point 9 reserves `dev-<name>` for sandboxes; prod release added to KEPT |
| L2 | Low | test-users skipped silently when principals are missing; wrong code comment | fixed: message "test-users not run: … missing"; comment corrected |
| L3 | Low | TD-72 deadline is a condition | kept: same form as the other condition deadlines |

## Phase 3, round 2 — 2026-11-18

- Reviewer: `pls-x-reviewer`, opus, high (resumed once after a usage limit). `git status` before/after identical. Verdict: **accept with fixes**. Round 1: H1, M1, L2 fixed; H2 partly fixed.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | High | the one confirmation of `principals --create --test-users` lists groups and user logins but not every change: joins of existing groups (with other members), key issue, `keys.<role>` in connections.json (ADR-0019 "listing every change") | Nam: "a" — A4 dropped: the code, tests and docs of `principals --create --test-users` removed; the two commands keep their own listing confirmations |
| R2-2 | Medium | refusals of `TU.plan_roles` that need no write (keys reference, login lookup, password / key files, group shape) come after the prompt and after groups are created; `TestUsersError` / `TransportError` outside the `try` | gone with A4 |
| R2-3 | Low | the sync-without-allow_write test does not assert the reason; a refused sync leaves a planned sandbox release | fixed: `sandbox_sync` checks `assert_writable` before the plan; the test asserts the `allow_write` refusal and that no release folder is left |
| R2-4 | Low | `dev-<name>` reserved for sandboxes only by documentation | kept as documentation (ADR-0011 point 9); a shared environment named `dev-<x>` is not expected |
| R2-5 | Low | ADR-0011 point 2 still lists create / refresh / drop | fixed |

Stopped (agent-rules §1 stop point 8). Nam: "a" — drop A4, commit the sandbox part with the Low fixes.

## Phase 4, round 1 — 2026-11-18

- Reviewer: `pls-x-reviewer`, opus, high. Change: working tree against `cc098e8`. `git status` before/after identical. Verdict: **accept with fixes**.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | High | a lock with commit "unknown" / no commit turned the check off; unreadable git recorded as clean | fixed: only a project with no lock is unchecked; no commit, "unknown", < 7 hex, `dirty` not `false` (older lock, git unreadable, dirty sync) → refused outside dev; sync records `dirty: null` when git cannot tell and warns; the test that locked the old behaviour replaced by ones that expect the refusal |
| F2 | Medium | only stg apply tested end to end | fixed: stg bootstrap, apply and record-changing `test` refused with `_confirm` patched to fail if asked first (no write); migrate through the shared `write_guard_now`; dev apply writes and warns once |
| F3 | Medium | ADR-0022 contradicts itself; ADR-0014 TB-6 stale | fixed the As-built sentence and "above"; Decision section of ADR-0022 and TB-6 row: stop point 1 → asked Nam |
| F4 | Medium | project `CLAUDE.md` vs template not compared on upgrade | deferred: TD-73; CHANGELOG names the rows to merge by hand |
| F5 | Low | prefix of any length matched | fixed: full hash in lock and state; ≥ 7 hex required |
| F6 | Low | pin refusal after the confirmation | fixed: `pin_guard` next to each up-front G4 check (apply, bootstrap, migrate) |
| F7 | Low | other dev writes do not warn | docs narrowed to apply / bootstrap / migrate (ADR-0022, setup, CHANGELOG) |
| F8 | Low | weak newer-release / hook tests | fixed: `_git` and `merge-base` patched; newer, ahead-of-tag and same-commit cases |
| F9 | Low | hotfix order: tag before changelog | fixed: changelog entry, merge into main, tag, push |
| F10 | Low | lock comment in architecture | fixed |
| F11 | Low | gitignored files / assume-unchanged / untagged local pin | one sentence in ADR-0022 (limits) |

## Phase 4, round 2 — 2026-11-18

- Reviewer: `pls-x-reviewer`, opus, high. `git status` before/after identical. Verdict: **accept with fixes**, Low only; F1, F2 (except migrate end to end), F5–F11 fixed; F3 As-built fixed, Decision / TB-6 for Nam (Nam: "a" — accept ADR-0022 option B, update TB-6); F4 → TD-73.
- Low findings L1 (migrate up-front pin check untested), L2 (malformed lock values traceback), L3 (`git status` without `-uall`, skip-worktree), L4 (sync warning and http-check line untested; "HEAD" from a repo without commits), L5 (stale doc lines, setup troubleshooting for lock problems), L6 (observations) — fixed in the follow-up commit with its own review.

The reviewed tree is committed unchanged.
