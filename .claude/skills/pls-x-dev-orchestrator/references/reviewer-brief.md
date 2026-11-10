# Brief for `pls-x-reviewer`

Fill every field. No narrative, no reasoning, no conclusions of the Orchestrator: the reviewer forms its own.

- **Task statement:** <the task as Nam gave it, verbatim>
- **Acceptance criteria:** <the numbered list from the plan>
- **Change to review:** commit range `<parent>..<head>` on `brownfield-adr`, or "working tree against `<parent>`"
- **Rules that apply:** `CLAUDE.md`, `docs/agent-rules.md`, `docs/review-criteria.md` (criteria: <ids relevant to the change, or "choose">), ADRs: <numbers>
- **Commands you may run:** read-only git (`diff`, `log`, `show`, `status`), reading files, `python -m unittest discover -s tools/pls/tests`, `node --test tools/pls/tests/test_runner.mjs`
- **You must not:** edit, create or delete any file; stage or commit; run a state-changing command; contact Pleasanter
- **Return:** verdict (accept / accept with fixes / reject); findings, each with severity (Critical / High / Medium / Low), evidence (`file:line`, command and output) and the failure scenario; what you ran; what you could not verify
