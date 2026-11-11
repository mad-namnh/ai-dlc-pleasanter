# Log
- tests first: 3 new fail before the change (schema, session field, foreign session); "no transcripts" baseline passes.
- ratchets: refusal list shrank by the old usage refusal (now tested); NOT_IN_A_PROJECT gets "*.jsonl" (Claude Code transcript under the home folder).
- parent-commit worktree (../_agent-scratch/wt-parent-au6, removed): 1 FAIL + 2 ERROR as expected.
- 3.12: 387 OK.
- real check in pls-demo-contracts: foreign session found (C--…-ai-dlc-pleasanter); window step→last event; 1 request counted after a second command, nothing outside.
- resumed after the session ran out of tokens: docstring overclaim corrected (one window per session; limits listed); test added for criterion 3 (own-folder session named in the run log counted whole); ADR-0013, plan.md AU6, HANDOFF updated.
- suites: 3.12 388 OK; 3.10 388 OK (2 skipped); node 15 pass. Review: accept, 3 Low (review.md).
