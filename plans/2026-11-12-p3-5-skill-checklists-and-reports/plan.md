# Plan — P3-5 skill checklists, outputs, completion report, skills check, multi-CR usage warning (design review I1, I3, I4, I6)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent `d88121a`
- **Tier:** Standard. Three parts, one commit each:
  1. **Skill text** (this commit): checklists in script-engineer, P6, onboarding, lifecycle (I1); Outputs in P3-config and P5 (I1); lifecycle §1 runs `pls skills check` first (I3, agent part); lifecycle §2 rule 9 completion report (I6, EV-07); script-engineer time-limit row cites KB D35. Test `test_skills_have_checklist_and_outputs.py`.
  2. **`pls usage report` warns** when one session holds steps of several releases / change requests (I4).
  3. **`skills check` in `pls`**: message says the direction (project older / newer / edited) by comparing versions, not only hashes (I3). Whether `step` / `gate` refuse on an edited project copy is Nam's decision (a new refusal in every project) — asked before building.
- **Acceptance criteria (part 1):** 1. every working skill has a "## Checklist …" section; skills writing project files have "## Output(s)"; 2. lifecycle §1 names `pls skills check` first, §2 the completion report (files, commands with results, open items, decisions, EV-07); 3. versions bumped in `skills/README.md` with "not yet evaluated" where the procedure changed; 4. the structure test fails on the parent; 5. suites green.
- **Evals:** lifecycle 0.22 and the phase skills are not evaluated by this task (text additions only); ask Nam before a batch.
- **Subagents:** `pls-x-reviewer` sonnet/medium per part.
