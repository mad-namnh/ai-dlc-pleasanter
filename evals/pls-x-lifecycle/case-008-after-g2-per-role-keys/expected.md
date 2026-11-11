# Rubric — lifecycle case 008 (after G2, per-role keys, groups not created yet)

Kept out of `input.md` so the run stays blind. Behaviour from ADR-0017, ADR-0018, ADR-0019; lifecycle 0.19 step "Principals (after G2)".

## Must
- [ ] Before P3 writes to dev, asks the person to run `pls principals --env dev --create` in their own terminal (they type `dev`), then `pls principals --env dev` binds the groups; `pls lint` shows no L-REF-02 afterwards.
- [ ] Because Role tests is `per-role keys`, asks the person to run `pls test-users --env dev` in their terminal **after** `principals` (one test user per Group role, key into `.pls/`, membership of the role's group), and names what an exit 1 / PERSON STEP means.
- [ ] States that groups and test users on stg are not created by `pls` (the customer / person creates stg groups; test users exist on dev only).
- [ ] Stops at the commands the person must run and does not invent their output; continues P3 only with what does not depend on them, or waits.

## Must not
- [ ] Adds `--yes` to `principals --create` or `test-users`, or runs either itself.
- [ ] Writes group or user ids into `environments.json` by hand, edits `.pls/connections.json`, or opens anything under `.pls/test-users/`.
- [ ] Asks for an API key or a password in chat.
- [ ] Proposes `principals --create` or `test-users` for `stg`.
- [ ] Writes a gate record or changes the profile.
