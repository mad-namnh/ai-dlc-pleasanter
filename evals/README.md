# Evals

Each skill has cases built from real work (slices). A case is:

- `input.md` — what the skill receives (request, current configuration summary, approved inputs)
- `expected.md` — a **rubric**: must-have properties (pass/fail) and anti-patterns (fail if present). Not a golden text — wording may differ.

## Running (v0.1, manual)

1. Create a scratch project repository (copy of `pls-demo-inquiry` at the stated baseline, or the files listed in `input.md`).
2. Invoke the skill with the input.
3. Grade the output against `expected.md`: every **Must** item passes and no **Must not** item appears → case passes.
4. Record the result in `results/<skill>/<date>.md` with the model and skill version used.

Automated grading is future work (tech debt). Add a case whenever a slice or an incident reveals a behaviour the skill must keep (I9).
