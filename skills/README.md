# Skills

Framework skills for AI-DLC for Pleasanter. Naming: `pls-<phase>-<role>` (see `CLAUDE.md`).

| Skill | Phase | Version | Status |
|---|---|---|---|
| `pls-kb-pleasanter` | all (knowledge base) | 0.12 | 0.12: api.md site package format (BR5).  0.11: D29 Htmls/Scripts/Styles, D30 dashboard parts, D31 background server scripts (BR3).  0.10: api.md "Version" (where 1.5.2 shows its version; ADR-0009).  0.9: D28 `[[Users*]]` user choice (equipment-loan demo R-20261105-01-dev).  0.8: `references/skeletons.md` (new-site skeletons, verified built-in columns; B3).  0.7: D21–D26 (equipment demo PRB-001, ADR-0007). D12–D20 from dev probes; facts 11–13 (process buttons for read-only users, summaries, removed definitions); rule: a probe is evidence only for the configuration it reproduces (slice #2, S2-1) |
| `pls-p1-requirements-analyst` | P1 | 0.3 | 0.2 passed eval case 001. 0.3 **passed eval case 002** run 1 (2026-11-05; header contamination noted, input fixed) |
| `pls-p2-solution-designer` | P2 | 0.6 | 0.6: impact analysis uses `pls xref` (BR7). 0.3 **failed eval case 002** run 1 (2026-11-05): design-changing probe scheduled after G2. 0.4: such probes are G2 prerequisites, otherwise take the safe branch. 0.4 **passed eval case 002** run 2 (2026-11-05): access control on the process as the safe branch, probe as G2 prerequisite. 0.5: new sites (`references/new-sites.md`, ADR-0007) — not yet evaluated |
| `pls-p3-config-builder` | P3 | 0.3 | 0.3: sandboxes, harvest, merge driver (BR6). 0.2: L-SCR-02 syntax, `pls refs` literal numbers (BR7). D2: design → `config/` (layout and references in `references/config-layout.md`), canon/lint/coverage loop, dev deploy until round trip 0. Case 001 run 1 pass (2026-11-05) |
| `pls-p4-test-writer` | P4 | 0.3 | 0.3: test-spec: mail safety refusal (ADR-0010).  0.2: `references/test-spec.md`: `siteConfig` does not substitute `$vars` (TD-14h).  D2: acceptance criteria → test specs (`references/test-spec.md` = the spec format), role tests, triage, G3 evidence (`references/g3-template.md`). Case 001 run 1 pass (specs, not run) |
| `pls-p5-release-manager` | P5 | 0.2 | 0.2: adoption records (BR4). D2: dev target = drift 0 + release record; stg = release-plan → G4 → apply → round trip → smoke; Japanese diff report (`references/diff-report-template.md`). Evaluated end to end in D7 |
| `pls-x-onboarding` | before P1 (existing apps) | 0.1 | BR9: take over an existing app read only — version, mail/jobs, adopt, env-compare, scope, principals, scripts; one decision per finding. Eval case 001 (fictional), not run yet |
| `pls-x-spec-recovery` | before P1 / P1–P2 input | 0.1 | BR9: as-is 画面設計書 (Japanese) from config, inferences marked; DES-000 for adopted scripts after review. Eval case 001, not run yet |
| `pls-p3-script-engineer` | P3 | 0.1 | BR9: rules for editing (legacy) scripts — references, D7, timeouts, D25, minimal diffs, L-SCR-02, xref impact, sandbox deploy. Eval case 001, not run yet |
| `pls-p6-maintenance-triage` | P6 | 0.1 | BR9: inquiries/incidents → facts, drift, version, env-compare, xref → cause and route (no fix). Eval case 001, not run yet |
| `pls-x-lifecycle` | all (orchestration) | 0.7 | 0.7: routes to onboarding, spec-recovery, script-engineer, triage (BR9). 0.6: 0.6: env-compare, version from a site package (BR5). 0.5: adopt existing sites (BR4); adoption records are not releases. 0.4: scope refusal (ADR-0001, BR3). 0.3: version check at the start (ADR-0009). 0.2: rule 2 covers `side_effects` (ADR-0010). D1 (Step 4b): phase order, gate stops and records (`references/gates.md`), `pls` commands per step, token rules; project `CLAUDE.md` template in `templates/project/`. Lifecycle case 001 **passed** (fresh agent stops at G1, 2026-11-05) |

## Installing into a project repository

Copy the skill folders into `<project>/.claude/skills/` and record the framework version in `<project>/.claude/framework.lock`. Projects pin a version; upgrades are explicit commits.

## Changing a skill

1. Change the skill here, never in a project copy.
2. Add or update an eval case under `evals/<skill>/` that shows why.
3. Bump the version in this table.
4. Never put a case's answer into a skill (examples must come from another domain); otherwise the eval measures recall, not skill quality.
