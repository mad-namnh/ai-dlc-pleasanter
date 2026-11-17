# Plan — ADR-0030 scope and selection cases (item 3)

Task (Nam, 2026-11-18): "ok lam theo thu tu" — item 3; "Dừng chờ apply (Recommended)": rubrics as a patch, then stop; the baseline / selection batch is asked when it comes.
Tier: Standard (eval contract content; rubrics are protected → patch).

## Acceptance criteria
1. First targets of ADR-0030 (lifecycle routing, P6, onboarding) each get a negative scope case (request outside the skill, skill loaded) and a selection case; plus one selection case whose answer is "none".
2. `input.md` holds the request and its premises only (test `test_eval_inputs_do_not_reveal_the_answer` green); `setup.md` names the arm.
3. Rubrics written before any run, as `proposed-scope-selection-rubrics.patch` (new files only), `git apply --check` clean.
4. `evals/README.md`, ADR-0030 Status and `docs/adr/README.md` say what is built and that nothing ran yet.
5. Both suites green on HEAD + this change; independent review.

## Cases
| Folder | Arm | Expected |
|---|---|---|
| `pls-x-lifecycle/case-009-not-a-pleasanter-request` | with skill | not a Pleasanter app: no phase started |
| `pls-p6-maintenance-triage/case-002-new-app-request` | with skill | not an incident: routed to the lifecycle (P1), no triage |
| `pls-x-onboarding/case-002-nothing-to-onboard` | with skill | Origin new, nothing to onboard: P1 via lifecycle, no site |
| `pls-p6-maintenance-triage/case-003-selection-incident` | selection | P6 (lifecycle if it says it routes to P6) |
| `pls-x-onboarding/case-003-selection-takeover` | selection | onboarding (lifecycle if it says onboarding first) |
| `pls-x-lifecycle/case-010-selection-new-app` | selection | lifecycle or P1 |
| `pls-x-lifecycle/case-011-selection-none` | selection | none |
