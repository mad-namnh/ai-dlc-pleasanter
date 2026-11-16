# ADR-0029: Deterministic phase checks over skill text — knowledge from one source, phase outputs with a schema, project hooks

- **Status:** Accepted (Nam: A2, B1 blocking, C1 on 2026-11-16) — Parts A and B built, C not yet
- **Date:** 2026-11-16
- **Deciders:** Nam
- **Related:** I4, I6, I8, I9 (`docs/architecture.md` §2); §5 P1–P3 "Checks", §7.3 (hooks listed, not built); ADR-0004 (classification), ADR-0016 (agent team), ADR-0020 (gate records), ADR-0023 (KB shapes); TD-21 (no PreToolUse hook yet), TD-51, TD-64, TD-65, TD-66 (skill text behind code); plan `plans/2026-11-16-deterministic-phase-checks/plan.md`

## Context

The write path is held by code: `assert_writable`, gates G1–G4, 22 lint rules, `classify`, `VERIFIED_KEYS` / `pls scope`, L-SEC-01, drift and read-back. A weak model or a vague request cannot put an unsafe configuration on Pleasanter.

The work **before** the write path is held by prose. P1–P4 are driven by about 780 lines of `SKILL.md` plus references. Their outputs (`requirements/REQ-*.md`, `design/DES-*.md`) are free markdown; only `design/slot-ledger.json` and `traceability.json` have a structure a tool reads. The architecture names checks for P1 ("every REQ has EARS form + acceptance criteria"), P2 ("every in-scope REQ has a design element; ladder reasons present") and P3 (hooks: write guard, secret guard, post-edit lint), but no tool runs them; the hooks of §7.3 are not built (TD-21). So:

1. **Results depend on the model and on how the person words the request.** A strong model follows the procedure; a weaker one skips steps, and nothing notices before a gate, where a person must find it by reading.
2. **Skill text falls behind the code.** A rule lands in code first (`classify`, KB, `pls principals`, `pls scope`); the skill that should tell the designer about it changes only with an eval. Open rows on 2026-11-16: TD-51 (D40/D41a conditions missing from the impact checklist), TD-64 (Dept roles), TD-65 (`pls scope` not called), TD-66 (checklist still advises touching child records after a summary change, against ADR-0028).
3. **Evals are thin** (P1/P2 a few cases; P3 two results; P4–P6 almost none) and usually run on one model, so the effect of a model change is unknown. (Eval coverage is a separate item; this ADR only reduces how much depends on it.)

Nam's message 2026-11-16 (verbatim): "đồng ý, viết ADR và plan theo thứ tự 2, 1, 3" — agreeing to the proposal "LLM proposes, tools decide" and to the order: (2) one source for rules, (1) phase outputs with a schema and a check command, (3) hooks in the project template.

## Part A — Design knowledge from one source (order 1)

The rules a designer must apply exist in code and KB: `classify` branches (data-impacting / permission-impacting), KB rows that set a design condition (D16, D40, D41a, D42, …), `VERIFIED_KEYS`. The P2 impact checklist restates them by hand.

### Option A1 — Drift test only
Each `classify` branch and each KB entry marked as a design condition carries a stable rule id; a test fails when the impact checklist does not name every id. The checklist stays hand-written.
- Pros: small; no generated skill text. Cons: every new rule still needs a skill edit and an eval; the test only says *that* text is missing.

### Option A2 — Generated reference, drift test as its first step (recommended)
- Rule ids as in A1 (a `rule` id per `classify` branch; `design_condition` text per KB entry in `probes/index.json`).
- `pls skills --gen` (or a build script) writes `skills/pls-p2-solution-designer/references/impact-rules.md` from them: one row per rule with its trigger, its class and the condition the design must state. The hand-written `impact-checklist.md` keeps only the walk procedure and points to the generated file.
- A test fails when the generated file is not up to date.
- **Eval rule:** the generated file is data. Changing a rule's text needs no eval of the skill; changing the generator or the hand-written procedure does. *(This changes the eval rule of `HANDOFF.md` "How we work" for this one file — Nam's decision.)*
- Pros: TD-51, TD-66-type drift cannot recur; a new `classify` rule reaches the designer in the same commit. Cons: a generator to keep; rule texts must be written for designers (reviewed like KB text).

### Option A3 — One rule table read by `classify` and the generator
`classify` is rewritten to read a JSON rule table that also feeds the checklist.
- Pros: a single place. Cons: refactor of a Critical function (ADR-0004) for no new behaviour; regex-and-code branches (`MultipleSelections`, Formulas) do not fit a table well.

## Part B — Phase outputs with a schema and `pls check` (order 2)

### Option B1 — Front matter in the existing markdown (recommended)
`REQ-*.md` and `DES-*.md` keep their prose for people and start with a YAML front matter block that `pls check` reads: REQ — id, status, EARS type, `shall` text, acceptance criteria ids, sources, open questions; DES — id, REQs, elements (site, path, rung, REQ), ladder reasons, classification, impact rows by rule id (Part A), probes needed (from `pls scope`). `pls check p1|p2|p3` reports what is missing:
- P1: EARS form and one `shall`; acceptance criteria present; every REQ names a source (interview answer or document); open questions listed; no duplicate id.
- P2: every in-scope REQ has an element; rung ≥ 3 has a reason; the classification is at least as strong as `classify` gives for the built change (once `config/` holds it); every impact rule triggered by the change (Part A ids) has a row; every key `pls scope` reports has a probe or a decision record.
- P3: `lint`, `scope`, every traceability config path exists.
- Pros: skills keep writing markdown; customers and reviewers read the same file; the check is cheap. Cons: front matter and prose can disagree (the check reads front matter only).

### Option B2 — JSON artifacts, markdown generated for people
- Pros: one structure, no disagreement. Cons: every skill and eval case changes at once; people edit JSON.

### Option B3 — No schema; `pls check` greps the markdown
- Pros: no change for skills. Cons: brittle; the same dependence on wording that this ADR removes.

### Gate coupling (both B1 and B2)
- **Blocking (recommended):** `pls gate G1` / `G2` refuse while `pls check p1` / `p2` reports findings, unless the approver accepts named findings with a reason, recorded in the gate record (ADR-0020). This touches gate records: stop point.
- **Advisory:** the check result is attached to the gate record; the gate is not refused.

## Part C — Hooks in the project template (order 3)

Built only after the hook contract is read in the official Claude Code documentation (TD-21: which exit code or output blocks a tool call), and shipped by `pls init` / `pls skills` as a Python script from the framework (no new dependency).

### Option C1 — Guards plus checks (recommended)
- PreToolUse: refuse Edit / Write to paths only `pls` writes (`releases/`, `gates/`, `ops/log/`, `.pls/`); refuse a Bash `pls` command with `--yes` the person did not type (agents never add it, `CLAUDE.md`).
- PostToolUse: after an edit under `config/` or `server-scripts/`, run `pls lint` for that site and return the findings to the agent.
- Stop: run `pls check` for the phase in progress and show the result (advisory; the gate decides, Part B).
### Option C2 — Stop hook only
- Pros: least intrusive. Cons: the guards stay in prose.

## Decision

**A2** (A1 as its first step), **B1** with **blocking** gate coupling, **C1**; build order A → B → C. Nam 2026-11-16 (AskUserQuestion, his answers verbatim): Part A "A2 generated file (Recommended)"; Part B form "B1 front matter (Recommended)"; gate "Blocking + accept (Recommended)"; hooks / evals "C1 + evals approved now (Recommended)". The C1 answer also approves the evals of the P1, P2 and lifecycle skills when their text changes under this ADR, without a further batch approval. The generated reference of Part A is data: a change of its rule texts needs no eval; a change of the generator or of the hand-written procedure does.

## Consequences

- With the recommendation: `pls` gains `check` and a generator; `classify` branches and KB entries gain rule ids (no behaviour change); REQ / DES templates and the P1 / P2 / P3 / lifecycle skills change (evals of those skills: batch approval by Nam); `pls gate` changes for G1 / G2 (stop point, ADR-0020 amended by this ADR when accepted); the project template gains `.claude/settings.json` hooks and a hook script.
- Architecture §5 "Checks" of P1–P3 and §7.3 "Hooks" become built rows; I6 gains "phase completeness is computed by `pls check`".
- TD-51, TD-65, TD-66 close with Part A (generated rows); TD-64 with the P2 skill change of Part B.
- What stays with the model: understanding the customer and choosing among designs. The checks make missing pieces visible; they do not judge whether a design is good — G1 / G2 approvers still do.

## As built

- Part A (2026-11-16): `tools/pls/pls_impact_rules.py` holds the rules (26: 16 decided by `classify`, which now returns their ids under `rules`, and 10 design conditions); `python tools/pls/pls_impact_rules.py --write` generates `skills/pls-p2-solution-designer/references/impact-rules.md` with the KB "Do this" text of every cited row; `tools/pls/tests/test_impact_rules.py` fails when a `classify` branch has no rule or no sample, a cited KB row is missing, or the generated file is stale. `impact-checklist.md` keeps only the walk procedure; the DES impact table gains a rule column; P2 step 5 / 1b name the generated file, `pls scope` and department roles (TD-64 P2 part, TD-65 P2 part, TD-66 closed). The uncommitted D40 KB rows (TD-51) reach the designer when they are committed, through the same staleness test. **Deviation from the option text:** the 10 design conditions are written in `pls_impact_rules.py`, not as `design_condition` fields of `probes/index.json` — several name `pls` commands (`pls scope`, `pls principals`) rather than Pleasanter behaviour, and the probe index is about probes; each condition only restates its cited KB rows or the code (no pending KB observation), and the KB "Do this" text is still copied from the KB itself. `classify` also returns each rule's class, so the first release of a new site drops data rules with data items.

- Part B (2026-11-16): `tools/pls/pls_front_matter.py` reads the front matter (a YAML subset, no dependency; an unreadable line is named); `tools/pls/pls_phase_check.py` — `p1` (id, status, EARS type, sources that exist, exactly one `shall`, acceptance count, open questions in the index, listed in the index, unique ids) and `p2` (id, status, reqs that exist, classification, migration section when data-impacting, elements with site / setting / req / rung 1–5 and a reason from rung 3, impact rows whose rule is an id of `impact-rules.md` with an action, every REQ of a DES named by one of its elements, every G1-approved REQ in a DES, misnamed REQ / DES files reported as not read; as-is records `DES-000-as-is-<site>.md` of taken-over sites are not designs and are left out — the open question on brownfield front matter stays); `p1` also checks the EARS keyword of the declared type (When / While / If…then / Where); `pls check p3` = lint, `pls scope` per site, every traceability config path. `pls gate G1` / `G2` refuse an approval while a finding names one of its items, an item has no document to check, a REQ / DES file is misnamed, or (G2) a G1-approved REQ has no DES; `--accept-findings "<reason>"` records the findings and the reason (ADR-0020 amended). Templates (REQ, DES) carry the front matter; P1 0.8, P2 0.13, P3 0.9 and lifecycle 0.28 run the checks. **Not built of option B1's text** (TD-67): the classification against `classify` of the built change, an impact row for every rule the change triggers, and a probe or decision record for every `pls scope` key — they need the change's diff and the release, which P2 does not have yet.
## Open questions

- [ ] Hook contract (blocking exit code / JSON output, Windows behaviour) — *Claude Code documentation, before Part C*
- [x] Whether a generated reference file needs an eval when only its data changes — no (Nam 2026-11-16, A2)
- [ ] Front matter fields for brownfield documents (`pls-x-spec-recovery` writes as-is specifications) — *Part B design, with the onboarding skill*
