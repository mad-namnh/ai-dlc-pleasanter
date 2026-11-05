# Rubric — P4 case 001

## Must
- [ ] Every acceptance criterion is mapped to a test, a `siteConfig` check or a named manual check. Required columns are screen-only (D27), so they are config or manual checks.
- [ ] Negative tests for every "cannot / only" criterion, run with the restricted role's key. For 社員:
  - loans 404;
  - writes 403 / 404;
  - 返却 refused.
- [ ] The 返却 display condition is tested: a second return → 400 (D10). The date order is tested: → 500 (D25).
- [ ] The overdue list is tested with records created by the test, and relative dates passed as `--var`.
- [ ] Fixtures are created with an authorised key inside the role specs, never taken from existing data.
- [ ] Test ids are in `traceability.json`; `g3-verification.md` is a draft awaiting the test run; the exact `pls test` commands are handed over.

## Must not
- [ ] Claim tests passed; edit config; bend expectations to the config without a reason.
