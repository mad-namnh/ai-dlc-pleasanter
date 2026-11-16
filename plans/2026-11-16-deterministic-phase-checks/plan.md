# Plan — deterministic phase checks (ADR-0029)

- **Date / branch:** 2026-11-16 / `brownfield-adr`
- **Origin:** Nam 2026-11-16, verbatim "đồng ý, viết ADR và plan theo thứ tự 2, 1, 3" (after the assessment of what depends on the model and on how a request is worded).
- **Objective:** what P1–P3 must contain is checked by `pls`, not remembered by the model; rules reach the designer from code and KB in the same commit.
- **Tier:** Critical for gate coupling (B4) and hooks (C); Standard for the rest.
- **Stop points:** ADR-0029 decision (all parts); gate change B4 (ADR-0020); protected path `templates/project/.claude/` (C, patch for Nam if it is protected); eval batches for skill changes.

## Workstreams (order agreed by Nam: A, then B, then C)

### A — Knowledge from one source
| Task | What | Acceptance |
|---|---|---|
| A1 | Rule id per `classify` branch (`CL-…`), `design_condition` + id per KB entry that sets one (`index.json`) | no classification change (existing tests green); ids unique (test) |
| A2 | Generator → `skills/pls-p2-solution-designer/references/impact-rules.md`; `impact-checklist.md` keeps the walk procedure and points to it | test fails when the generated file is stale; TD-51 / TD-66 rows appear in it |
| A3 | P2 skill points to the generated file and to `pls scope` (TD-65) | P2 eval (batch approval) |

### B — Phase outputs with a schema and `pls check`
| Task | What | Acceptance |
|---|---|---|
| B1 | Front matter schema for REQ / DES (templates in `templates/project/requirements/`, `skills/pls-p2-solution-designer/references/des-template.md`) | schema file + examples; eval-case expected outputs updated |
| B2 | `pls check p1` (EARS, one `shall`, acceptance criteria, source, open questions, unique ids) | tests per finding; runs on `pls-demo-*` copies under `../_agent-scratch/` |
| B3 | `pls check p2` (element per REQ, ladder reason ≥ 3, classification vs `classify`, impact rows by rule id, `pls scope` keys) and `p3` (lint, scope, traceability paths) | tests per finding |
| B4 | `pls gate G1/G2` refuse on findings unless accepted with a reason in the gate record | Critical review; ADR-0020 amendment text to Nam |
| B5 | P1 / P2 / lifecycle skills: "fill front matter, run `pls check`, fix until clean"; Dept roles (TD-64) | evals P1, P2, lifecycle (batch approval) |

### C — Hooks in the project template
| Task | What | Acceptance |
|---|---|---|
| C0 | Read the hook contract in the Claude Code documentation (TD-21) | notes with links in this folder |
| C1 | Hook script (Python, from the framework): PreToolUse guards (`releases/`, `gates/`, `ops/log/`, `.pls/`; `--yes` not typed by the person), PostToolUse `pls lint` for edited site, Stop `pls check` advisory | tests with recorded hook inputs; Windows and bash |
| C2 | `pls init` / `pls skills` install `.claude/settings.json` hooks into project repositories | `test_architecture_project_layout` updated; `pls-demo-*` copy smoke test |

## Not in this plan
- Eval matrix per model and more golden cases (assessment item 5): separate plan; needs eval batch approval.
- Intake questionnaire `pls request new` (item 4) and pattern library (item 6): after B, if P1 checks show the gap.

## Decisions needed from Nam before building (ADR-0029)
1. Part A: A2 (recommended) / A1 / A3; and the eval rule for a generated reference (data change without eval: recommended).
2. Part B: B1 front matter (recommended) / B2 JSON / B3 none; gate coupling blocking (recommended) / advisory.
3. Part C: C1 (recommended) / C2.
4. Eval batches for A3 and B5 (P1, P2, lifecycle) — approve now or per batch.

## Budget
Subagents: reviewer per task (opus for B4 and C, sonnet otherwise); evals as approved.
