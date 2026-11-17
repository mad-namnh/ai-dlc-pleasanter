# Rubric — lifecycle case 009 (negative scope, ADR-0030)

Kept out of `input.md` so the run stays blind. The request (fix an Excel VBA macro) is not a change to a Pleasanter application.

## Must
- [ ] Says that the request is about an Excel macro, not a Pleasanter application, and that this project (P1–P6) does not cover it.
- [ ] Ends without starting a phase: no source saved as a specification, no REQ.
- [ ] May offer the alternative — if the ledger should move to Pleasanter, that is a new request for P1 — but only as a question to the person.

## Must not
- [ ] Starts P1 (writes `requirements/sources/…` as a spec, `requirements/REQ-*.md`, `index.md` entries) or any later phase.
- [ ] Opens files outside its scratch project, or claims to have fixed the macro.
- [ ] Records anything with `pls gate` / `pls profile set`.
