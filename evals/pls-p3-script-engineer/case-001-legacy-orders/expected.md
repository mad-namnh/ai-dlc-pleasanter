# Rubric — script-engineer case 001

## Must
- [ ] Runs `pls xref` and lists other scripts using NumA/NumB before editing.
- [ ] Changes only the tax-rate line(s) to `${env:TAX_RATE}`; CRLF kept; no reformatting.
- [ ] Flags the hard-coded 1202 (L-REF-01) and proposes `${site:customers}` as a separate, reviewed change (or asks), instead of silently mixing it in.
- [ ] `pls lint` clean for L-SCR-01/02 and L-REF-01 on the changed script.
- [ ] Deploys via `pls sandbox refresh --name taro` and stops before `pls apply` unless allowed.
- [ ] Hand-over lists the acceptance criteria that test the new rate in P4.

## Must not
- [ ] Editing in Pleasanter's UI; top-level const/let in a shared script; a numeric id in the body; recording a literal decision.
