# Skills

Framework skills for AI-DLC for Pleasanter. Naming: `pls-<phase>-<role>` (see `CLAUDE.md`).

| Skill | Phase | Version | Status |
|---|---|---|---|
| `pls-kb-pleasanter` | all (knowledge base) | 0.4 | + D12–D15 (data behind removed definitions, bulkupsert, no record versions via API, permissions in updatesite), bulk/paging/principal API |
| `pls-p1-requirements-analyst` | P1 | 0.2 | eval case 001 **passed** with a fresh agent (run 2, 2026-11-05) — `evals/results/` |
| `pls-p2-solution-designer` | P2 | 0.2 | eval case 001 **passed** with a fresh agent (2026-11-05) — `evals/results/` |

## Installing into a project repository

Copy the skill folders into `<project>/.claude/skills/` and record the framework version in `<project>/.claude/framework.lock`. Projects pin a version; upgrades are explicit commits.

## Changing a skill

1. Change the skill here, never in a project copy.
2. Add or update an eval case under `evals/<skill>/` that shows why.
3. Bump the version in this table.
4. Never put a case's answer into a skill (examples must come from another domain); otherwise the eval measures recall, not skill quality.
