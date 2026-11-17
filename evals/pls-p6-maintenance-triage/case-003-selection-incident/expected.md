# Rubric — selection case: incident on a running app (ADR-0030)

Arm: selection. The runner sees only the request and every skill's `name` and `description`.

## Expected
- **Pass:** `pls-p6-maintenance-triage`.
- **Pass if its reason names `pls-p6-maintenance-triage` as the next skill:** `pls-x-lifecycle` (the entry skill of a session).
- **Fail:** any other skill, or "none".

Grading: the one skill the runner says it would use decides (the brief asks for one). Other skills it mentions as also read (e.g. the KB) are noted, not graded. An answer that names several without choosing one fails.
