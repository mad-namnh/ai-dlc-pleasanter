# Log — eval-inputs-setup-split

- 2026-11-17: Nam "ok tiếp tục"; patches of the ADR-0030 build applied by Nam (`a9deff5`), so the M1 wording and HANDOFF.md as a never-open path stand. Choices in plan.md. Classified Critical. HEAD a9deff5.
- Test `tools/pls/tests/test_eval_inputs_do_not_reveal_the_answer.py` written first: on the current inputs all 22 failed (reasons per input listed in the session); on `a9deff5` + the test only (worktree): FAILED (failures=1).
- 22 cases split: neutral `# Input` heading; notes moved to `setup.md` (descriptive title kept there). Requests that lived in sibling repositories (P1 002, lifecycle 001 / 005) are copied by the Orchestrator into `customer-mail.md`; P2 001 gets the configuration inline; lifecycle 005 / 006 describe the scratch project instead of "as case 001"; P5 002 states the prepared release instead of "case 001 is done"; `pls-demo-purchase` → `purchase`. Premise and request wording otherwise unchanged.
- `setup.md` added to the file names the `skills/` test refuses; `evals/README.md` case layout and Running step 1; ADR-0030 Status "patches applied" (Nam's choice) and README row.
- Patches: `proposed-eval-case-brief-setup.patch`, `proposed-eval-case-runner-setup.patch` (setup.md and other project repositories never opened); `git apply --check` OK.
- Verified in `../_agent-scratch/wt-split` (a9deff5 + all changes + both patches applied): Python 726 OK (exit 0), node 16/16. Worktree kept for the reviewer.
- Reviewer call 1 (pls-x-reviewer, opus, high).
- Review round 1: accept with fixes, 1 High / 2 Medium / 5 Low; all fixed except F8 (reported) (`review.md`). Re-verified: Python 726 OK, node 16/16. Subagent calls: 1 of 6. Reviewer call 2 (round 2, opus, high).
- Review round 2: accept with fixes, 6 Low, all fixed (`review.md`). Re-verified: Python 726 OK, node 16/16. Subagent calls: 2 of 6. Review rounds: 2 of 2.
