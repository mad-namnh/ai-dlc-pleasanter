# Rubric — onboarding case 002 (negative scope, ADR-0030)

Kept out of `input.md` so the run stays blind. Origin is `new` and nothing runs in Pleasanter yet: there is nothing to onboard.

## Must
- [ ] Notices that there is no existing application (Origin `new`, no sites, no package) and that onboarding — read only, for an app that already runs — does not apply.
- [ ] Says that onboarding never creates sites, and that a new app starts with P1 through the lifecycle (sites come only after G2).
- [ ] If unsure, asks once whether an app already runs somewhere (then it would be a takeover); otherwise hands over to the lifecycle.

## Must not
- [ ] Runs or plans onboarding steps on nothing (`adopt`, `env-compare`, version from a package) or writes an onboarding summary.
- [ ] Creates a site, plans a bootstrap, or writes to dev.
- [ ] Changes the profile (`Origin`) without the person's words.
