# Review — skill-frontmatter-rules-test

Round 1 (pls-x-reviewer, sonnet, medium, 2026-11-17): **accept**; 0 Critical / 0 High / 0 Medium / 2 Low. `git status` unchanged by the review.

| Finding | Severity | Disposition |
|---|---|---|
| Low-1: `frontmatter()` is a line parser, not YAML; quotes and a folded `>` stay in the value (no effect on the 12 current files; a quoted name fails loudly) | Low | Limit documented in the function's docstring |
| Low-2: `XML_TAG` flags any `<word …>` in prose | Low | Intended rule; `a < b > c` not flagged, covered by the self-test. No change |

Reviewer could not reach Anthropic's documentation (judged against the brief) and relied on `log.md` for the failure on `534c1cb~1`; its full Python run timed out, with the one failure it saw (`test_impact_rules`) caused by other work's uncommitted KB edit. The Orchestrator's run on `534c1cb` + this test only: 717 tests OK (log.md).
