# Skills

Framework skills for AI-DLC for Pleasanter. Naming: `pls-<phase>-<role>` (see `CLAUDE.md`).

| Skill | Phase | Version | Status |
|---|---|---|---|
| `pls-kb-pleasanter` | all (knowledge base) | 0.7 | 0.7: D21–D26 (equipment demo PRB-001, ADR-0007). D12–D20 from dev probes; facts 11–13 (process buttons for read-only users, summaries, removed definitions); rule: a probe is evidence only for the configuration it reproduces (slice #2, S2-1) |
| `pls-p1-requirements-analyst` | P1 | 0.3 | 0.2 passed eval case 001. 0.3 **passed eval case 002** run 1 (2026-11-05; header contamination noted, input fixed) |
| `pls-p2-solution-designer` | P2 | 0.5 | 0.3 **failed eval case 002** run 1 (2026-11-05): design-changing probe scheduled after G2. 0.4: such probes are G2 prerequisites, otherwise take the safe branch. 0.4 **passed eval case 002** run 2 (2026-11-05): access control on the process as the safe branch, probe as G2 prerequisite. 0.5: new sites (`references/new-sites.md`, ADR-0007) — not yet evaluated |
| `pls-x-lifecycle` | all (orchestration) | 0.1 | D1 (Step 4b): phase order, gate stops and records (`references/gates.md`), `pls` commands per step, token rules; project `CLAUDE.md` template in `templates/project/`. Lifecycle case 001 **passed** (fresh agent stops at G1, 2026-11-05) |

## Installing into a project repository

Copy the skill folders into `<project>/.claude/skills/` and record the framework version in `<project>/.claude/framework.lock`. Projects pin a version; upgrades are explicit commits.

## Changing a skill

1. Change the skill here, never in a project copy.
2. Add or update an eval case under `evals/<skill>/` that shows why.
3. Bump the version in this table.
4. Never put a case's answer into a skill (examples must come from another domain); otherwise the eval measures recall, not skill quality.
