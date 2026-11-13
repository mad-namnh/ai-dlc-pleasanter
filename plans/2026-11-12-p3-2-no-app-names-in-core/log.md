# Log — P3-2 no app names in core

Counts: subagent calls 0/6, review rounds 0/2, fix attempts 0/3.

- 2026-11-12 | Nam: "lam tuan tu cac task cua P3". Start with P3-2; plan written.
- 2026-11-12 | subagent 1/6: `pls-kb-curator`, `haiku`, low — 4 KB wording edits, no remaining hits; `git status` showed only KB paths changed by it.
- 2026-11-12 | new test FAILS on parent `a19fe9a` (worktree `../_agent-scratch/p32-parent`, removed). Suites: 448 OK (3.12), 448 OK skipped=2 (3.10), node 15 pass.
- 2026-11-12 | subagent 2/6: `pls-x-reviewer`, `sonnet`, medium, round 1/2 — accept, 3 Low; L2 fixed (login/logo), see `review.md`.
- 2026-11-12 | after the L2 fix: a suite run that took 33470 s (machine asleep) had one subprocess timeout in `test_output_on_a_cp932_console`; re-run: 448 OK (158 s); `test_scripts` on 3.10 OK; node 15 pass.
