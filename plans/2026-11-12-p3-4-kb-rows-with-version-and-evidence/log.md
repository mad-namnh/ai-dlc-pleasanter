# Log — P3-4 KB rows with version and evidence

Counts: subagent calls 0/6, review rounds 0/2, fix attempts 0/3.

- 2026-11-12 | source read for the ~10 s row: Script.json at tag Pleasanter_1.5.2.0 (WebFetch raw.githubusercontent.com) — ServerScriptTimeOut 10000, Changeable false, HttpClientTimeOut 100000. Plan written while P3-3 is in review.
- 2026-11-12 | test `test_kb_rows_have_id_version_and_evidence.py` written first; on the KB of parent `dfdd63c` (before any KB edit): 5 failures (two rows without ID; D4a, D5, D11 without version/marker; 7 probed entries without "Probe contained"; api.md without "Evidence:").
- 2026-11-12 | subagent 1/6: `pls-kb-curator`, `sonnet`, medium — edits 1–7; it reported rows claiming more than their probe (D8, D21, D24, D28, D30), written as "Not covered". Follow-up message (same call): D4a duplicate wording trimmed. `git status`: only KB reference files changed by it. KB test: 5 OK.
- 2026-11-12 | README KB 0.24 (curator proposed 0.25; current was 0.23); register D34, D35; TD-36; HANDOFF.
- 2026-11-12 | subagent 2/6: `pls-x-reviewer`, `sonnet`, medium, round 1/2 — accept, 2 Low; F-2 fixed (test requires "Not covered"; curator follow-up normalised the D33 label). Parent check: see the first entry (5 failures on the parent's KB).
