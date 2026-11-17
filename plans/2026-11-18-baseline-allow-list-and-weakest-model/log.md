# Log

- Edits: ADR-0030 (lines of Decision part 2, Part 5 step 4, Open questions, Status), evals/README (allow-list, step 4), docs/adr/README row 0030; brief patch built in a temporary worktree, `git apply --check` clean.
- grep: runner definition reads `docs/agent-rules.md` only when the allow-list names it (line 10) — unchanged; agent-rules and orchestrator skill name no baseline allow-list.
- Review round 1 (opus/high): accept with fixes, 1 Medium / 6 Low; fixes and dispositions in review.md; patch rebuilt with a Reason header, `git apply --check` clean.
- Suites on `fdc30ca` + this change + the brief patch applied (worktree `wt-ad30b`): Python 736 OK, node 16/16.
- Subagent calls: reviewer ×1 (opus, high).
