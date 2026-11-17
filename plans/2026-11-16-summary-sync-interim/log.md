# Log — summary change advice

- 2026-11-16 Implemented in worktree wt-sum (base 71f92f1). test_pls 63 OK. Review (pls-x-reviewer, sonnet, medium; subagent 1/6).
- Review: accept with fixes, Low only (review.md). Fixes: ADR-0028 "As built" section, nothing enforces `pls step` (L2). Found while fixing: KB D16 records an earlier API call to `synchronizesummaries` → 400, and the screen 同期 is source-derived only → note no longer says "do not touch child records" but names the child update as the observed fallback; ADR-0028 Context + open questions. Curator for D16 advice (opus, medium; subagent 2/6). Parent check: test_classify_summary_change_is_data_impacting FAILS on 71f92f1.
