# Review — kb-verify results of the store-promo KB gaps

## Round 1 (pls-x-reviewer, opus, high, 2026-11-14) — verdict: accept with fixes

Scope: working tree against `b00a551` (excluding `.claude/settings.json`, `plans/2026-11-12-permission-allow-list/`). Reviewer ran Python suite (589 OK) and node (15 pass); `git status` identical before and after.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| H1 | High | D36 written as verified "per creating group"; probes have one test user per role and no baseline, so only per-creator is observed | Fixed (curator): D36 per creator verified, group-wide reach source-derived, second member and baseline under Not covered; schema/api/review-findings/HANDOFF reworded; TD-46 for the missing probe |
| M1 | Medium | md detail cut at 300 chars drops NG lines now that every log line is kept | Fixed: NG lines first, cut marked "full log in the .json". Test |
| M2 | Medium | `StatusControls` in VERIFIED_KEYS drops the only refusal for status controls naming principals (ids not mapped between environments) | Fixed: `StatusControl.cs` 1.5.2.0 has `Depts`, `Groups`, `Users` (l.32–34); `pls_scope.unverified` reports a status control with any of them. Test |
| L1 | Low | VERIFIED_KEYS evidence is per checked path, not a full export round trip | Fixed: docstring says so |
| L2 | Low | docstring "three roles' test users" | Fixed: two roles' test users and the administrator |
| L3 | Low | D41 `verified_on` 1.5.2 while its probe run failed | Fixed (curator): split D41 (formula, verified) / D41a (after lookup, not established; probe moved) |
| L4 | Low | review-findings D36–D42 Issue/Recommendation columns stale | Fixed: rows rewritten |
| L5 | Low | revised D40 probe not proposed | Deferred on purpose (plan item 4): cause first, screen check by Nam; reported to Nam |
| L6 | Low | inventory checklist rows not updated | Fixed: rows 5 and 12 🟡 with the evidence |

## Round 2 (pls-x-reviewer, opus, high, 2026-11-14) — verdict: reject

All round-1 dispositions hold. `git status` identical before and after; reviewer ran Python 3.12 (591 OK) and node (15 pass).

| # | Sev | Finding | Disposition |
|---|---|---|---|
| R2-H1 | High | New entry id `D41a` crashes `KV.report` (`int("41a")`) after every probe write → kb-verify exits 3, no report | Reproduced (`ValueError: invalid literal for int() with base 10: '41a'`). Fixed after round 2: `pls_kbverify.entry_key` (number, then letter), used for both sorts; behaviours row regex `D\d+[a-z]?`. Tests: split ids sort and report; every entry of the framework probes reports (both fail on `b00a551`). No third review round run (limit 2) — Nam decides |
| R2-L1 | Low | index.json D41 run "pass" vs report "D41 fail" without a note | Open — KB file (curator); next curator call |
| R2-L2 | Low | revised D40 probe not proposed; Nam's acceptance of the narrowing not recorded | Reported to Nam with this round |
| R2-L3 | Low | non-NG reasons (errors, control) can still be cut in the md | Fixed: every line that is not `ok` goes first. Test |
| R2-L4 | Low | D36 main text: "that user can update" for both roles; probe updates as store_a01 only | Open — KB wording (curator); next curator call |

## Round 3 (pls-x-reviewer, opus, high, 2026-11-14; Nam: "Review vòng 3 rồi commit") — verdict: accept with fixes

Scope: the fixes after round 2. R2-H1 fixed and tested (parent `report` raises `ValueError` on `D41a`); suites 594 OK, node 15; `git status` identical before and after.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| R3-L1 | Low | R2-L3 partly fixed: step lines still precede a late reason (control line, NG after many creates) and can push it past the cut | Recorded: TD-47 (a) |
| R3-L2 | Low | `pls.py` half of the R2-H1 fix (row regex, `no_probe` sort) has no CLI test | Recorded: TD-47 (b) |
| R2-L1, R2-L4 | Low | KB text (round 2) | Recorded: TD-47 (c), next curator call |
