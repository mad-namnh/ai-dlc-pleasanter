# Review — TD-70 probe principal shapes

Reviewer: pls-x-reviewer (opus), round 1, 2026-11-18, working tree against e32c9b8. Verdict: **accept with fixes**, Low only. Reviewer ran the suite (738 OK), node 16/16, `check_probe` on all 29 KB probes (ok) and the new test against the parent module (12 failures).

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| L1 | Low | `ColumnName` / `ChoicesText` read with exact case | Fixed: compared without case; test |
| L2 | Low | a `Columns` list as JSON text not read | Fixed: parsed; test |
| L3 | Low | float id, permission entry inside a longer text or with four parts, `Users` as an object pass | Fixed: floats, `PERMISSION_IN_TEXT` (`User,5` without space anywhere), any number of parts, a non-empty object under Users/Groups/Depts refused; tests |
| L4 | Low | docs do not say only the listed shapes are checked (e.g. a column `DefaultInput`) | Fixed: ADR-0027 As built 2026-11-18 names it |
| L5 | Low | possible false refusals: label `Group, 3`, filter `-1` | Accepted (stricter only, no KB probe affected); written in ADR-0027 |

After the fixes: 3.12 738 OK; 3.10 738 OK (skipped=2); node 16/16; all 29 KB probes pass `check_probe`. Round 2 not needed (Low only).
