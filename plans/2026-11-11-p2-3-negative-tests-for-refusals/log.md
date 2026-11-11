# Log — P2-3 negative tests for refusals

Counts: subagent calls (not eval cases) 0/6, review rounds 0/2, fix attempts 0/3.

- 2026-11-11 | state: `brownfield-adr`, parent `f77b47a`, working tree clean; classified Standard; main session model `claude-fable-5-2`
- 2026-11-11 | measured (one-off script in the session scratch folder, Python 3.12 `sys.monitoring`): 261 refusal lines, 118 never run by the suite
- 2026-11-11 | asked Nam (scope and fix-commit rule are his): chose "ratchet + the items the review names" and "a check script + the rule in HANDOFF"
- 2026-11-11 | part 1 implemented: ratchet module (6 tests) + list (121 names of 273 refusals; `print` / `return` refusals are counted too, hence 273 not 261)
- 2026-11-11 | whole suite with an empty list: 1 failure (the ratchet test, 121 refusals reported) — shows the suite fails on an unlisted, untested refusal; with the list: Ran 363, OK (3.12, about 150 s instead of 115 s); 3.10: Ran 363, OK (skipped=2: the comparison needs 3.12)
- 2026-11-11 | a second demonstration (remove one line from the real list, run, restore) was denied by the permission rules as one shell command; not repeated — the stale-line direction will show when part 2 adds tests
