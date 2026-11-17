# Plan — eval-method ideas from NVIDIA SkillEvaluator: risk analysis before an ADR and a Tier 1 trial

- **Date:** 2026-11-16
- **Tier:** Critical (changes the evaluation contract; brings third-party software onto the operator's machine)
- **Status:** decisions D1–D4 taken (log.md); trial done (`trial-report.md`); ADR-0030 written as Proposed, review rounds 1 and 2 fixed (`review.md`); Nam accepted before round 2 ("chap nhan"); round 2 fixes changed the Decision section, so Nam confirms acceptance of the revised text before the Status line is changed
- **Source looked at:** `https://github.com/NVIDIA/SkillEvaluator` at `d2e0253` (2026-11-16), package version 0.9.0, support level "Experimental". Cloned read-only into the session scratchpad; the source was not run — only the PyPI package 0.9.0 in the trial.

## Task

Nam (2026-11-16): do (1) and (2), but first assess whether they could damage the framework's architecture.

1. An ADR that adopts three eval-method ideas: k attempts per case (pass@k), a no-skill baseline arm (skill lift), negative / edge activation cases.
2. A one-off, read-only trial of SkillEvaluator Tier 1 keyless checks on `skills/`.

## What the two steps touch

| Area | Step 1 (ADR) | Step 2 (trial) |
|---|---|---|
| `tools/pls`, write guards, gates G1–G4, I1–I8 | no | no |
| I9 (escaped defect → eval) | strengthens it (method) | no |
| Eval contract (`evals/README.md`, HANDOFF "How we work", eval brief, runner agent) | yes | no |
| Protected paths (`evals/**/expected.md`, `.claude/agents/**`, `.claude/skills/**`) | yes — new rubrics and brief changes are patches Nam applies | no |
| Skill text / versions | no | no (findings are input only) |
| Network, third-party code | no | yes (PyPI download, local run) |

Conclusion: neither step reaches the write path or an invariant that holds the write path. The risks are to the **validity of eval evidence** (step 1) and to **repository integrity and data leaving the machine** (step 2).

## Risks — step 1 (ADR)

| ID | Risk | Real? | Mitigation in the ADR |
|---|---|---|---|
| R1 | **Contaminated baseline.** The runner works in this repository with Read/Grep/Glob; a "no-skill" run can still open `skills/` and the KB, and `CLAUDE.md` / architecture text describe the framework. Lift then looks smaller than it is, or the result is meaningless. Blindness today also rests on the brief only (agent-rules §4). | Yes | Define the baseline precisely (D1); its brief names no skill and forbids `skills/`; the runner reports whether it opened any; the result file labels the isolation as instruction-based. |
| R2 | **SkillEvaluator's layout `skills/<skill>/evals/`.** Rubrics inside a skill folder would be installed into customer project repositories and would be readable by the runner that reads the skill — breaks blindness and `skills/README.md` "never put a case's answer into a skill". | Yes, if the format is copied | ADR states: case folders stay under `evals/<skill>/`; no SkillEvaluator dataset files inside `skills/`. A test may assert it. |
| R3 | **Scale of eval runs.** k attempts × 2 arms multiplies runs; interview cases (P1 case 003) need a person-role relay per run. ADR-0029's approval of P1 / P2 / lifecycle evals was given for single runs. *(Superseded by the ADR text: ADR-0030 states it amends ADR-0029's approval — the k with-skill runs are covered, baseline and selection batches are asked.)* | Yes | k and scope per skill tier (D2); a new batch approval names k and arms; interview cases run k without a baseline unless Nam asks. |
| R4 | **False precision.** With 1–3 cases per skill, pass@k and lift are anecdotes; a number could be read as a verdict or turned into a gate. | Yes | Results stay advisory (I6: deterministic checks decide); every result with < 10 cases or no negative case is labelled provisional; no threshold blocks a commit or a gate. |
| R5 | **Rubric changes on protected paths.** Negative / edge cases need new `expected.md` files. | Process only | Agent writes `proposed-*.patch`; Nam applies (stop point 3). |
| R6 | **Contradiction with ADR-0029.** ADR-0029 (Accepted, not built) moves rules out of skill text and says a generated reference needs no eval. | Low | New ADR names ADR-0029 and leaves that rule unchanged; it only changes *how* an eval that is run is run. *(Superseded: ADR-0030 also amends ADR-0029's eval approval, named in its Related line.)* |
| R7 | **Model routing.** Evals are exempt from routing; a cheaper baseline model would invalidate lift. | Low | Both arms and all k attempts on the model the result file records. |

## Risks — step 2 (Tier 1 trial)

| ID | Risk | Real? | Mitigation |
|---|---|---|---|
| T1 | **Writes into the repository.** Default report folder is `reports/` under the working directory; `validate` runs Tier 3 autopilot, which creates `evals/` inside a skill; `ci init` opens a pull request on GitHub (outward-facing). | Yes | Run only `quality-check` and `pii-scan`; never `validate`, `tier1`, `tier3`, `create-eval-dataset`, `ci init`. Target a copy of `skills/` under `../_agent-scratch/skillevaluator-trial/`; working directory and `-o` there. `git status` before and after; a difference is a failed trial. |
| T2 | **Data leaving the machine.** LLM stages send skill text to a provider when a provider variable is set. | Yes | Run with `SKILL_EVAL_LLM_PROVIDER`, `NVIDIA_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` unset in the command; no `--llm`, no `--llm-verify`. |
| T3 | **Supply chain.** Installs a third-party package and its dependencies; full Tier 1 also downloads SkillSpector / Gitleaks binaries. | Yes | Pinned `skillevaluator==0.9.0` through `uv` into a tool folder in the scratch area (not the project venv, not `pyproject`); only the two pure-Python commands, so no scanner download (to confirm with `--help` before running). Removed after the trial. |
| T4 | **Score-chasing.** The quality score follows a generic Agent Skills rubric (correctness 0.35, discoverability 0.25, reliability 0.25, efficiency 0.15) and metadata conventions (`metadata.author`, `metadata.id`) that are not ours. Editing skills to raise it changes skill text without an eval. | Yes | Findings are input to Nam only; any skill change follows the normal path (eval). The trial changes no skill. |
| T5 | **Customer-like data in the report.** `pii-scan` may quote matches. | Low | Report stays in the scratch area; the summary in this plan folder names rule and file, not the matched text. A real hit is a Mandatory 3 incident reported to Nam. |

## Pre-existing state

The working tree holds uncommitted work that is not this task's (`HANDOFF.md`, ADR-0014, ADR-0023, KB files, `.claude/settings.json`, three untracked plan folders). Stop point 9: nothing of this task is committed until Nam says how that work stands.

## Decisions for Nam

- **D1 baseline:** (a) without the skill under test, KB available — recommended; (b) bare model, nothing of the framework; (c) both.
- **D2 k and scope:** k = 3 for P1, P2, lifecycle; others k = 1 — recommended; or k = 3 for all.
- **D3 trial scope:** `quality-check` + `pii-scan`, keyless, no scanner download — recommended; or full Tier 1 with scanner download.
- **D4 order:** trial first, then the ADR (Proposed) — recommended; or both now.

## Steps after the decisions

1. Trial (step 2) as above; summary `trial-report.md` here. — done
2. ADR `docs/adr/0030-eval-repeats-no-skill-baseline-and-activation-cases.md` **Proposed** and its README row. — done
3. Review by `pls-x-reviewer` (Critical). — round 1 done, all findings fixed (`review.md`)
4. After Nam accepts ADR-0030 (separate commits, each reviewed): `evals/README.md`, HANDOFF evals line, the test that `skills/` holds no eval data, patches for the runner brief / agent definition / new rubrics (protected paths).
5. Commit of this task only after the pre-existing uncommitted work is settled (stop point 9).

## Acceptance criteria (ADR step)

1. ADR-0030 is Proposed (Status line not Accepted), follows `docs/adr/0000-template.md` sections, and is listed in `docs/adr/README.md`.
2. It records Nam's choices verbatim: baseline without the skill under test with the KB kept; k = 3 for P1, P2, lifecycle; the decision rule and cost recording.
3. It prevents risk R2: no eval dataset, rubric or expected output inside `skills/`, with a test planned.
4. It keeps the existing eval rules: blindness, person-role and `pls` relays, hand grading, the eval model rule, ADR-0029's generated-reference rule; it does not contradict an Accepted ADR.
5. Results stay advisory (I6); provisional label for thin evidence.
6. Changes to protected paths are named as patches for Nam, not made.
7. Unknowns (harness behaviour, reported token figures) are open questions, not assumptions.
8. English only; no customer data; no plan or finding codes cited as the reason in a way that would be unresolvable (plan folder path allowed in an ADR).
