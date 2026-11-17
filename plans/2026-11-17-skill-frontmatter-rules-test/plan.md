# Plan — a test for the Agent Skills frontmatter rules

- **Date:** 2026-11-17. **Asked by:** Nam ("ok, làm test description XML như task Standard riêng"). **Tier:** Standard (a new test, no change to `pls`).
- **Why:** P3 0.10 (`534c1cb`) removed `config/<site>/` from its `description`. Anthropic's Agent Skills documentation says a `description` cannot contain XML tags (a skill upload through the API or claude.ai may be refused). Nothing stops the next skill from doing the same; skills are installed into project repositories (ADR-0022).

## Scope

New test `tools/pls/tests/test_skill_frontmatter_follows_the_agent_skills_rules.py`, over every `SKILL.md` under `skills/` and `.claude/skills/` (read only), against the frontmatter rules of the same documentation page:

- `description`: present, not empty, at most 1024 characters, no XML tag (`<word…>` or `</word>`);
- `name`: equals the folder name, at most 64 characters, lowercase letters, digits and hyphens only, no XML tag, neither "anthropic" nor "claude".

Out of scope: `.claude/agents/*.md` (subagent definitions are not Agent Skills; the rule is not documented for them), changing any skill.

## Acceptance criteria

1. The test fails on `534c1cb~1` (P3 description with `<site>`) naming that skill, and passes on the current commit.
2. A failure message names the file and the rule broken.
3. Both suites green; no skill changed; no protected path changed.
4. Independent review (`pls-x-reviewer`), findings handled per the orchestrator skill.

## Steps

1. Write the test. 2. Show it failing on the parent of the P3 fix in a temporary worktree. 3. Both suites. 4. Review. 5. Commit by explicit paths (test, this plan folder).
