# ADR-0018: Test users and their API keys for role tests on dev

- **Status:** Accepted (2026-11-11) — option C with B as the fallback, decided by Nam after the probe; nothing built. The CLAUDE.md Mandatory 1 exception is applied (`20fe494`); test users join their groups as ADR-0019 (Accepted, option B) says
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** ADR-0008 (HTTP transport, `as_key`, keys in `.pls/`), ADR-0017 (groups from the permission design), ADR-0014 (TB-14 shared tenant resources, TB-15 API key privilege), ADR-0009 (KB verification); TD-11, TD-13; `docs/plan.md` Step 4d AU5

## Context

`pls test` already runs a spec or a step as a role (`as_key`, ADR-0008), and refuses two roles that resolve to the same key. What is missing is the users: at stage demo, role tests are `deferred` because nobody created one test user per role on dev and a key for each (TD-11, TD-13). In the trial `pls-demo-contracts`, REQ-012-style checks ("role X is refused") could therefore not run in P4. AU5 asks for these tests without hand work.

Two things are needed per role, and they are different problems:
1. **A user** that belongs to the role's principal (for `principal: "Group"`: a member of the group bound by `pls principals`).
2. **An API key of that user.** The key is what `pls test` sends; a key of the operator would test the operator's rights, not the role's.

What is known (manual, not observed by us):
- `POST /api/users/create` (`LoginId`, `Name`, `Password`, optional `MailAddresses`), `/api/users/{id}/update`, `/api/users/{id}/delete`: **tenant manager only**; answer `{Id, StatusCode, Message}`. https://pleasanter.org/en/manual/developers-guide/api/user-operations/api-user-create/
- An API key is issued **by the user themself** after logging in (User > API settings > Create). The manual describes no way to issue a key for another user, and no API for it. https://pleasanter.org/en/manual/developers-guide/api/basics/api-key/
- The Pleasanter source (`Implem.Pleasanter`, branch `main`, not necessarily 1.5.x) has the web actions `POST /users/authenticate` (anonymous), `POST /users/createapikey` and `POST /users/deleteapikey` behind them. They are the screens' endpoints, not a documented API.

Constraints:
- Users are **tenant-wide**, like groups (TB-14). The operator's dev key is a tenant administrator (ADR-0017).
- A test user's password and key are secrets: never in git, never in a log line or a result file, never in chat (CLAUDE.md Mandatory 1 and 4). The only place for them is the operator's `.pls/` (gitignored), as `file:` key references (ADR-0008).
- ADR-0017 (Accepted) rule 3: a group created by `pls` gets **one member, the operator**; rule 2: `pls` never updates an existing group. A test user in a group therefore needs a superseding ADR either way: rule 3 changed to let test users join at the group's creation (`GroupMembers`, observed), and rule 2 changed (or a person) for groups that already exist — such as the three groups of the trial, created on 2026-11-11.
- CLAUDE.md Mandatory 1 lets keys be written only to "the operator's own key files under `.pls/`". A test user's password or key written by `pls` is not the operator's own credential: options B–D need Nam's explicit reading or change of that rule (a protected path) before they are built.

## Open questions

Answered by the probe `plans/2026-11-11-au5-role-test-users/probe-user-create.py` (operator, MADLAB dev 1.5.2, runs of 2026-11-11 19:03 and 19:05; KB `api.md` "Users and groups"):
- [x] Does `/api/users/create` create a user with the operator's key, and is the answered `Id` the `UserId`? **Yes, yes.** A new user reads back with `Disabled`, `Lockout`, `TenantManager` false (TenantManager not sent); the record also holds secret fields (`SecretKey`, `SecondaryAuthenticationCode`).
- [x] Does the server refuse a second user with the same `LoginId`? **Yes**: HTTP 500, 「このログインIDは既に使用中です」 (unlike group names).
- [x] After `/api/users/{id}/delete`, does `/api/users/get` still return the user, and does a key issued to it still work? **No and no**: the lookup finds nothing and the key answers 401 "Unable to authorize."
- [x] Can the new user log in with the password given at creation? **Yes**, with no password change asked: `/users/authenticate` with `Users_LoginId`, `Users_Password`, `ReturnUrl` (exact names; the page also has a hidden `LoginId` and `Users_ChangedPassword*`), no anti-forgery token.
- [x] Logged in as that user, does `/users/createapikey` issue a key that the API then accepts? **Yes** (`/api/users/get` with the key: HTTP 200, StatusCode 200).
- [x] Does the API accept a logged-in session without an `ApiKey`? **Yes** for `/api/users/get`; other calls with a session not verified.

Not answered by the probe:
- [ ] Is a deleted user kept in the trash box so that its `LoginId` stays taken (a second create with the same `LoginId` after the delete is not tried)?
- [ ] Where `pls` keeps a test user's password and key: file names under `.pls/`, whether `pls` adds the `keys.<role>: file:…` reference to `.pls/connections.json` itself, and whether the password file is removed once the key exists (see Mandatory 1 above).
- [ ] Lifecycle of test users: when they, their passwords and their keys are disabled or deleted (end of project, key rotation), and by whom.
- [x] Does `/api/groups/{id}/update` with `GroupMembers` replace the member list or add to it? **Replaces** (ADR-0019 probe); test users join groups as ADR-0019 option B says.
- [ ] Departments (`principal: "Dept"`): a test user's department is a user field; not covered.
- [ ] Password policy of the customer's dev (length, expiry, forced change): may differ from MADLAB dev.

## Options

Common rules for B–D: only on an environment with `role: "dev"` and `allow_write: true` that is not a sandbox (`assert_writable`); never stg (stg test users are the customer's) or prod; one test user per role, `LoginId` from the project and role name with a fixed prefix (`zz_test_…`); never tenant manager; a typed confirmation listing the users; the write joins the write-path inventory (`test_write_guards.py`) and the run log lists the created user ids (no names of real people, no secrets).

### Option A — Person step (as now, TD-11)
The operator creates each test user in the UI, logs in as it, creates its key and saves it under `.pls/`.
- Pros: no new write path; nothing undocumented.
- Cons: the step AU5 wants to remove; repeated for every project and every role; passwords chosen by hand.

### Option B — `pls` creates the users by the documented API; a person issues each key once
`pls` creates the missing test users (`/api/users/create`), with a random password written only to the operator's `.pls/` file, and adds them to the role's group at the group's creation. The person logs in once per test user, creates its key, and saves it where `pls` says (`.pls/keys/<env>-<role>.key`).
- Pros: only documented API; the password is never typed or seen by an agent.
- Cons: one UI step per role per project remains; groups that already exist need a person (or a change of ADR-0017 rule 2).

### Option C — B, and `pls` also issues the key through the web endpoints
After creating a user, `pls` logs in as it (`/users/authenticate` with the stored password), calls `/users/createapikey`, checks that the API accepts the key, and writes it only to `.pls/keys/<env>-<role>.key`.
- Pros: no person step at all — the AU5 "done when".
- Cons: depends on undocumented screen endpoints that may change between versions — it needs a KB entry per version and a refusal on a version where it is not verified (ADR-0009), with option B as the fallback; a tool now handles a password and logs in as another user.

### Option D — Session instead of keys
`pls test` logs in as the test user with the stored password and sends the API calls with that session, without a key.
- Pros: no key to issue or store.
- Cons: only if the API accepts a session without a key (unknown); a different transport for role tests than for everything else in ADR-0008.

## Decision

**Option C, with B as the fallback** (Nam, 2026-11-11). Nam also decided: CLAUDE.md Mandatory 1 gets an explicit exception for the dev test users `pls` creates (patch `plans/2026-11-11-au5-role-test-users/proposed-CLAUDE.md.patch`, applied by Nam); test users join their role's group through a new ADR that supersedes ADR-0017 rules 2–3 (needs a probe of `/api/groups/{id}/update` first).

Reasoning given before the decision: the probe showed on 1.5.2 that the login and key issue work, so the recommendation is **C, with B as the fallback** on a version where `pls kb-verify` has not confirmed the screen path. C is preferred over D: the result is an ordinary key, so `pls test` and ADR-0008 stay as they are, and D was observed for one call only. Before C is built: Nam's reading or change of CLAUDE.md Mandatory 1 (test-user passwords and keys in `.pls/`), and a superseding ADR for ADR-0017 rules 2–3 (test users in groups).

## Consequences

- What becomes easier: REQ-012-style "refused for role X" tests run in P4 at stage demo (AU5 "done when"); TD-11 / TD-13 closed for dev.
- What becomes harder / costs: TB-14 gains a tool write of users; a tool handles test-user passwords (C, D) and keys (C); a tenant-administrator key stays needed on dev (TB-15).
- The probe script is a one-off outside `pls`: it is not in the write-path inventory and leaves no run-log line; it stays in the plan folder as the record of the KB entry and is not run again.
- Follow-up work: KB entry from the probe (via `pls-kb-curator`); the chosen option in `pls`; P4 skill text (role tests at stage demo); ADR-0008 consequences (who creates test users' keys), ADR-0014 TB-14 / TB-15 rows; TD-11 / TD-13.
