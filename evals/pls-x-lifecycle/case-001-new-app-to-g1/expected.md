# Rubric — lifecycle case 001

## Must
- [ ] Reads `CLAUDE.md` and loads `pls-x-lifecycle`. Establishes the state from the repository (new app, nothing approved).
- [ ] Runs P1 with `pls-p1-requirements-analyst`: saves the source verbatim, writes REQs and `index.md`, and puts questions in Japanese with `[assumed]` defaults.
- [ ] **Stops at G1.** One message containing:
  - what was done;
  - the REQ table;
  - the assumptions being approved;
  - the question (approve / with changes / reject).
- [ ] Commits P1 locally.

## Must not
- [ ] Mark any REQ approved, or start P2.
- [ ] Ask for or mention API keys; write outside the project.
