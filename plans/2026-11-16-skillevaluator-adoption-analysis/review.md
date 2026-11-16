# Review — ADR-0030 (round 1)

- **Reviewer:** `pls-x-reviewer`, model opus, effort high; 2026-11-16. Change: working tree against `904927f` (ADR-0030, README row, plan folder). `git status` before and after the call identical.
- **Verdict:** accept with fixes — 0 Critical, 0 High, 4 Medium, 9 Low. Both suites run by the reviewer: Python 646 OK, node 16/16.

## Findings and disposition

| ID | Sev | Finding (reviewer's evidence, condensed) | Disposition |
|---|---|---|---|
| M1 | Medium | Baseline scratch copy of a `pls-demo-*` project holds `.claude/skills/<skill under test>` (`../pls-demo-inquiry/.claude/skills` has KB, P1, P2); the forbidden-path rule did not name that root | Fixed: Part 2 — baseline scratch setup removes every `.claude/skills/*` except the KB and records it; forbidden paths named for the framework and the scratch folder |
| M2 | Medium | Repeated runs and arms can read sibling folders under `../_agent-scratch/` (runner has Read/Grep/Glob from the framework root) | Fixed: Part 1 — a run may open no `../_agent-scratch/` folder but its own; folders of earlier runs of the same case are moved out of `../_agent-scratch/` before the next run; included in the opened-files check |
| M3 | Medium | "Activation" cases did not measure activation: the brief always names the skill | Fixed: Part 3 split into scope cases (skill loaded) and selection cases (runner gets only the skill descriptions and chooses); real harness selection stated as not measured, open question added |
| M4 | Medium | ADR narrowed ADR-0029's eval approval ("single runs") without saying it amends it | Fixed: "single runs" reading dropped; ADR-0029's approval stated to cover the k with-skill runs; only baseline and selection runs need a batch approval; named as an amendment in Related, Consequences and the README row |
| L1 | Low | "1–3 cases per skill" wrong (lifecycle has 8) | Fixed: counts per skill |
| L2 | Low | Must-not hits ignored by lift and the removal rule | Fixed: Part 2 lift and Part 5 steps 1 and 4 |
| L3 | Low | Arms differ by the skill plus what it references; the KB holds design rules | Fixed: Part 2 wording |
| L4 | Low | Opened-file list is self-reported | Fixed: open question (transcript check by the Orchestrator) |
| L5 | Low | Cost of the first baseline sweep understated | Fixed: Consequences → Cost with the counts |
| L6 | Low | TD-51 cited but only in uncommitted other work | Fixed: TD ids dropped from Context; refers to ADR-0029 Context |
| L7 | Low | plan.md stale | Fixed: status and steps updated |
| L8 | Low | Runner reads `CLAUDE.md` by its definition anyway | Fixed: Part 2 and the open question narrowed |
| L9 | Low | Vietnamese quotes without gloss | Fixed: English gloss added |

# Review — ADR-0030 (round 2)

- **Reviewer:** `pls-x-reviewer`, model opus, effort high; 2026-11-16. Change: working tree against `HEAD` (the reviewer found HEAD at `75f9b3b`, ADR-0029 Part A built, which touches no reviewed path). `git status` before and after the call identical.
- **Verdict:** accept with fixes — 0 Critical, 0 High, 2 Medium, 5 Low. Round-1: all resolved except M1 partly (→ F1). Suites by the reviewer: node 16/16; Python 652 run, **1 failure** `test_impact_rules.test_the_generated_reference_is_up_to_date` — caused by the uncommitted KB edit of other work (`behaviours.md`), not by this change (documents only); whoever commits that KB work regenerates `impact-rules.md` in the same commit.

| ID | Sev | Finding (condensed) | Disposition |
|---|---|---|---|
| F1 | Medium | Baseline forbidden-path rule left skill copies in sibling project repositories and `skills/README.md` (which names a P1 case 001 Must item) open; the README leak also exists in the with-skill arm today | Fixed: Part 2 allow-list (own scratch, `input.md`, KB, `CLAUDE.md`, `docs/` except review criteria, `templates/`); `skills/README.md` forbidden in both arms through the brief patch (Consequences) |
| F2 | Medium | k calls per case and a second holding place contradict `docs/agent-rules.md` §3–§5 and ADR-0016's single scratch place; no patch named | Fixed: holding place named `../_agent-scratch-held/` as the one exception; "one call per run, k runs per case"; `docs/agent-rules.md` patch added to Consequences |
| F3 | Low | Selection cases had no forbidden-path rule | Fixed: own scratch folder and `input.md` only |
| F4 | Low | Cost of resumed runs / person role and Part 5 averaging ambiguous | Fixed: sum of the runner's completion notices, person role separate; "averaged over the k runs" |
| F5 | Low | Generated reference of ADR-0029 Part A not covered | Fixed: counts with the skill for lift; never trimmed under Part 5 |
| F6 | Low | plan.md stale (R3, R6, status) | Fixed |
| F7 | Low | KB has no eval cases | Fixed |
