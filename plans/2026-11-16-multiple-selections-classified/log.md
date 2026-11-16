# Log — multiple selections classified

- 2026-11-16 Source read (see plan). Worktree of 5554586 (`../_agent-scratch/wt-multi-select`).
- Found: the existing rule "column definition removed" (`p.count("[") == 1`) also matches the removal of any column attribute (e.g. `Columns[A].MultipleSelections` removed). It errs on the safe side (data-impacting), so it is not changed here; the new rule is placed before it so its own message applies.
- Suites: 3.12 624 OK; 3.10 624 OK (skipped=2); node 16/16. Parent check: the new test fails (1 failure).
- Review round 1 started (pls-x-reviewer, opus, high; subagent 1/6).
- Review round 1: accept with fixes (M1 ChoicesControlType config-only against the task statement; L1–L4) → review.md.
- Fixes: ChoicesControlType changed → data-impacting, not verified (task statement as written; radio buttons ignore multi-select, HtmlControls.cs l.589); MultipleSelections only when bool(before) != bool(after); ADR-0004 as-built line reworded (no claim about new columns) and an open question for the WS3b probe; inventory row; HANDOFF line. L4 (column attribute removal labelled "column definition removed") left as noted: errs on the safe side.
- 'removed false' hit the broad column-removed rule → own config-only branch for MultipleSelections with equal truth value.
- Suites after fixes: 3.12 624 OK; 3.10 624 OK (skipped=2); node 16/16. No Critical/High after round 1: no second round. Subagents 1/6.
- Committed (see git log); REPORT SENT
