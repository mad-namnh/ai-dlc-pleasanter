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
