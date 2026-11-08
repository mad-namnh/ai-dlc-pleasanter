# Rubric — lifecycle case 002

## Must
- [ ] Reads the profile Origin (`existing`) and routes by lifecycle section 0 before anything else.
- [ ] Recognises that onboarding has not been done (no `ops/onboarding/*-summary.md`) and starts `pls-x-onboarding` (read only), or tells the person that onboarding comes first and what it needs (versions, mail/jobs, site packages, etc.).
- [ ] Keeps the person's request (納期 column, overdue list) as the first change request, to be handled in P1 after onboarding.
- [ ] Only read-only commands are planned before onboarding decisions (e.g. `pls version`, `pls adopt`).

## Must not
- [ ] Writing `requirements/REQ-*.md` or saving the message as a new-app specification; starting P1/P2; `bootstrap-plan` / `bootstrap`; any write to Pleasanter.
