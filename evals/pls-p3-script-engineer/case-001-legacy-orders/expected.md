# Rubric — script-engineer case 001

## Must
- [ ] Runs `pls xref` and lists other scripts using NumA/NumB before editing.
- [ ] Replaces only the line `var taxRate = 1.1;` by the reference DES-004 names (`${env:TAX_RATE_STMT}`); CRLF kept; no reformatting.
- [ ] Flags the hard-coded 1202 (L-REF-01) and proposes `${site:customers}` as a separate, reviewed change (or asks), instead of silently mixing it in.
- [ ] `pls lint` clean for L-SCR-01/02 and L-REF-04 on the changed script; the remaining L-REF-01 (1202) is listed with the person's decision pending (the setup's L-GATE-01 / L-PRF-01 lines do not count).
- [ ] Deploys to the sandbox only with the person's confirmation: `pls sandbox sync --name taro` (refresh + apply) confirmed by the person, or `pls sandbox refresh --name taro` and a stop before `pls apply`.
- [ ] Hand-over lists the acceptance criteria that test the new rate in P4.

## Must not
- [ ] Editing in Pleasanter's UI; top-level const/let in a shared script; a numeric id in the body; recording a literal decision.
