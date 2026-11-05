# Skills

Framework skills for AI-DLC for Pleasanter. Naming: `pls-<phase>-<role>` (see `CLAUDE.md`).

| Skill | Phase | Version | Status |
|---|---|---|---|
| `pls-kb-pleasanter` | all (knowledge base) | 0.6 | D12–D20 from dev probes; facts 11–13 (process buttons for read-only users, summaries, removed definitions); rule: a probe is evidence only for the configuration it reproduces (slice #2, S2-1) |
| `pls-p1-requirements-analyst` | P1 | 0.3 | 0.2 passed eval case 001 (2026-11-05). 0.3: existing-element overlap check (slice #2, S2-4); eval case 002 added, not yet run |
| `pls-p2-solution-designer` | P2 | 0.3 | 0.2 passed eval case 001 (2026-11-05). 0.3: probe-combination rule, role/button check, principals, summary migration (slice #2, S2-1/S2-3); eval case 002 added, not yet run |

## Installing into a project repository

Copy the skill folders into `<project>/.claude/skills/` and record the framework version in `<project>/.claude/framework.lock`. Projects pin a version; upgrades are explicit commits.

## Changing a skill

1. Change the skill here, never in a project copy.
2. Add or update an eval case under `evals/<skill>/` that shows why.
3. Bump the version in this table.
4. Never put a case's answer into a skill (examples must come from another domain); otherwise the eval measures recall, not skill quality.
