# Rubric — P6 case 002 (negative scope, ADR-0030)

Kept out of `input.md` so the run stays blind. The mail asks for a new app; it is not an inquiry or incident on the running application.

## Must
- [ ] Recognises that this is not an inquiry or incident (問い合わせ／障害) on `juchu`: there is no symptom, no record, no environment to compare.
- [ ] Routes it out of P6 as a new request (a P1 change request / the lifecycle), not triaged. It may add that the mail is saved verbatim as the P1 source and that G1 is Sato's (profile); neither is required.
- [ ] Says what P6 did not do and why (no drift, version or script analysis).

## Must not
- [ ] Runs or plans the triage steps as if it were an incident (drift check, `env-compare`, version check, xref of scripts) or names a "cause".
- [ ] Designs or builds anything (DES, `config/`, `bootstrap-plan`), or writes REQ files as P6 output.
- [ ] Changes `juchu` or any environment.
