# Plan — AU5: role tests without hand work (test users and their keys)

- **Task (Nam, 2026-11-11):** AU5 in `docs/plan.md` Step 4d — start by deciding whether a probe of user creation through the API is needed; same way as AU2 (ADR + probe first, Nam runs the probe).
- **Tier:** Critical (new write path to a tenant-level object; passwords and API keys of test users are secrets; touches TB-14, TB-15, ADR-0008 key rules). Main session Opus 5.5.
- **Status:** ADR-0018 (Proposed) and the probe script written; independent review; then Nam runs the probe on dev and decides. No `pls` code before that. Nothing committed while the decision is pending.

## Facts
- KB (`skills/pls-kb-pleasanter/references/api.md`) has only `POST /api/users/get`; no observed user create, update, delete or key issue.
- ADR-0008: role tests run with `pls test`, each spec/step picks a key by `as_key`; keys are `env:` / `file:` references in the operator's `.pls/connections.json`; "test users' keys belong to the test users"; two roles on one key are refused.
- TD-11 / TD-13: multi-user HTTP run deferred; needs a key created by each role's test user.
- Pleasanter manual (not observed): `POST /api/users/create` (`LoginId`, `Name`, `Password`, `MailAddresses`), `/api/users/{id}/update`, `/api/users/{id}/delete` — tenant manager only; response `{Id, StatusCode, Message}`. An API key is issued **by the user themself** after login (User > API settings > Create); no documented way to issue one for another user.
- Pleasanter source (`Implem.Pleasanter` on GitHub, `main`, not necessarily 1.5.x; not observed): web actions `POST /users/authenticate` (anonymous), `POST /users/createapikey`, `POST /users/deleteapikey`, `SwitchUser`. Undocumented as API.

## Answer to "is a probe needed?"
Yes, and the user creation alone is not the deciding question: a created user is useless to `pls test` without a key. The probe asks both:
1. documented API: create / read back / duplicate LoginId / delete a test user (stage A);
2. undocumented web path: can `pls` log in as that user and issue its key without a person (stage B), and does the API accept a session without a key.

## Steps
1. ADR-0018 Proposed (options A–D), README row.
2. `probe-user-create.py` in this folder (operator runs it; dev only, not a sandbox, `assert_writable`, typed confirmation; deletes what it created; prints no password, key or server address).
3. Review (`pls-x-reviewer`, opus/high) of ADR + probe; fix.
4. Nam runs the probe, pastes the JSON; KB entry via `pls-kb-curator`; Nam decides ADR-0018.
5. Build only the chosen option (separate commit(s)).
