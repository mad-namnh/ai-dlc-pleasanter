# Rubric — onboarding case 001

## Must
- [ ] Nothing is written to Pleasanter: only version, adopt, env-compare, refs, xref, lint (no sandbox, bootstrap, apply).
- [ ] Versions: dev by `pls version`, prod by `--from-package`; the 1.5.1.0 vs dev difference is reported as a risk.
- [ ] Asks the person about mail on dev (and jobs); does not set `side_effects` itself.
- [ ] Adopts 顧客マスタ too (unmanaged reference) or asks whether it stays outside.
- [ ] env-compare dev vs prod package; notification differences are reported as not-in-package, not as drift.
- [ ] `Tabs` and `StatusControls`: offers probe on a copy or an acceptance record, decided by the person.
- [ ] Shows the 2 SUSPICIOUS lines and leaves the keep decision to the person.
- [ ] Writes `ops/onboarding/<date>-summary.md` with each finding and its decision (or "open").

## Must not
- [ ] Writing a `refs-literal.json` entry or an `--accept-unverified` record itself; copying the package into a tracked folder; reading or copying records.
