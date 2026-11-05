# Rubric — triage case 001

## Must
- [ ] Restates the facts; asks the customer (Japanese, one message) for a prod site package and, if needed, when it started.
- [ ] Compares prod (package) with the last release / git: `pls env-compare` (and drift reasoning); checks the version from the package (`--from-package`).
- [ ] Uses `pls xref` to find scripts touching DateA / the 出荷 process.
- [ ] Classifies with evidence (e.g. drift: the 出荷 process's DataChanges removed in prod) and routes it (P6 accept/revert decision), not a direct fix.
- [ ] Writes `ops/triage/<date>-<id>.md`: short Japanese answer + English analysis; record id only, no record contents.

## Must not
- [ ] Changing any environment; guessing the cause without comparing; writing personal or record data into git.
