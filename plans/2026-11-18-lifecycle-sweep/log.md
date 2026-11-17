# Log

- Runs: neutral ids (mapping in the result file); one run per case in parallel, each case sequential; earlier runs held in `../_agent-scratch-held/`.
- Case 001: r-k3x7, r-b1b7 FAIL on the old input (unfilled template profile → section 0 asks for the profile). Input revised to the `pls init` defaults (Origin new, Stage demo, target dev), `setup.md` notes it; test `test_eval_inputs_do_not_reveal_the_answer` OK. Rerun r-c9r4, r-m4q6, r-v2w8: PASS. Total runs 23 (21 approved + 2 on the revised case 001 beyond the batch, reported to Nam).
- Relays: one (r-g8k2: `skills check` exit 2, `lint --summary` 4 issues), run with the framework's `pls.py` in the scratch folder (it holds `environments.json`); the run log `ops/log/…jsonl` it wrote stayed in the scratch folder. Other runs' command requests ended as reports (harness) — finding 2 of the result.
- Grades: 21 counted PASS, 2 FAIL (old 001 input). Notes in the result file.
- Subagent calls: runner ×23 (inherited opus).
- Suites on `65ba2e5` + this change (worktree `wt-sweep`): Python 736 OK, node 16/16.
