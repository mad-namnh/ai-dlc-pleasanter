# Rubric — selection case: new app from a customer mail (ADR-0030)

Arm: selection. The runner sees only the request and every skill's `name` and `description`.

## Expected
- **Pass:** `pls-x-lifecycle`.
- **Pass:** `pls-p1-requirements-analyst` (the first phase the lifecycle runs).
- **Fail:** any other skill, or "none".

Grading: the one skill the runner says it would use decides (the brief asks for one). Other skills it mentions as also read (e.g. the KB) are noted, not graded. An answer that names several without choosing one fails.
