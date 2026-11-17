# Rubric — selection case: takeover of an app built without the framework (ADR-0030)

Arm: selection. The runner sees only the request and every skill's `name` and `description`.

## Expected
- **Pass:** `pls-x-onboarding`.
- **Pass if its reason names `pls-x-onboarding` as the next skill:** `pls-x-lifecycle`.
- **Fail:** any other skill (in particular `pls-x-spec-recovery` alone, which needs adopted sites, or `pls-p6-maintenance-triage`), or "none".

Grading: the one skill the runner says it would use decides (the brief asks for one). Other skills it mentions as also read (e.g. the KB) are noted, not graded. An answer that names several without choosing one fails.
