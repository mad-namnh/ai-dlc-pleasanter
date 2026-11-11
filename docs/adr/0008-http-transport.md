# ADR-0008: HTTP transport with local connections (no browser in the loop)

- **Status:** Proposed — implemented in `pls` 0.5 (`tools/pls/pls_http.py`). First real run on dev (2026-11-05, Nam's terminal): connection, export of keys from environment variables and the 総務 test suite work; fixes from that run: BOM in `connections.json` (PowerShell 5), numbers compared by value. Multi-user role run deferred (demo stage)
- **Date:** 2026-11-05
- **Related:** ADR-0003 (production deploy), ADR-0005 (secrets), TD-11, TD-13, slice-03 lessons 3–4

## Context

Until slice #3, every call to Pleasanter went through a logged-in browser tab (runner `pls-runner.js`):
- payloads and exports travelled as base64 through the agent conversation — the most token-heavy step, repeated after every page change (the runner is lost on navigation);
- role tests needed a person to log out and log in as the test user (TD-13).

The browser was needed only because the agent sandbox had no network path to Pleasanter. A person, or an agent running on a normal workstation, can call the API directly.

## Decision

`pls` gets an HTTP transport using the Pleasanter API with API keys:

| Command | Does |
|---|---|
| `pls http-check --env E` | reads one site with every configured key; shows whether writes are allowed |
| `pls export --env E --site S …` | `getsite` → `.pls/exports/` |
| `pls bootstrap B` | creates the sites of `releases/B/bootstrap.json`, then `bind` (ADR-0007) |
| `pls apply R` | the planned multi-site release: preflight (`UpdatedTime`), ordered apply, reverse-order restore on failure, then export + `mark-applied` |
| `pls test SPEC… --env E --site S [--var k=v] [--release R \| --yes]` | same spec format as the runner; each spec's `as_key` picks the role's key, so role tests need no login switch |
| `pls backup --env E --site S --out DIR` | every record, for migrations (ADR-0004) |

**Connections are local, never in git:** `.pls/connections.json` (gitignored; template `connections.example.json`) holds the URL per environment, key references and `allow_write`. Keys are referenced as `env:NAME` (environment variable) or `file:NAME` (file under `.pls/`); literal keys are refused. Each person uses their own keys; test users' keys belong to the test users. On dev, `pls test-users` creates a test user per role and issues its key into the operator's `.pls/test-users/` (ADR-0018).

**Write guard:** environments.json `role` dev or stg **and** local `allow_write: true`; `role: prod` is never written by this tool. `apply` and `bootstrap` ask the operator to type the release id (agents do not pass `--yes` unless the person asks).

**The browser runner stays** as a fallback for a person on dev only; agents do not use it (ADR-0014 TB-7, design review 2026-11-09). Both transports read and write the same files (plan, payloads, rollbacks, test specs, results), so a release can be planned by one and applied by the other. Where they behave differently: see "Differences between `pls` over HTTP and the browser runner" below.

## Limits

- An API key cannot render the edit screen: `editPage` steps (is a button shown?) are skipped and the test is reported `pass-api-only`. Coverage counts it, the result says so. Button visibility is covered by the process access control (D20) and by the API refusal; a UI check with the browser runner is needed only for a new kind of design.
- API keys are as powerful as their user. Use test users with the role's rights, not admin keys, for role tests.

## Consequences

- ADR-0003 option A (runner in the customer network) can use the same `pls apply` with the customer's own keys and connection file; the agent never sees them.
- Token cost of P3–P5 drops to the size of the commands and their summaries.

## Findings from the first real run (2026-11-05)

- A role test run with another role's key does damage: refusals it expects succeed (a fixture was deleted). `pls test` and `pls http-check` now refuse/warn when two roles resolve to the same key.
- Fixtures belong in the spec, created with the 総務 key by step-level `as_key`, so a run never depends on IDs typed by hand.

## Differences between `pls` over HTTP and the browser runner (2026-11-10, design review G4)

The runner is a fallback for a person on dev. Both read the same plan, payload, rollback and test-spec files; they differ as follows. Closed on 2026-11-10: `exec` without `expectHttp` now fails on any status other than 200 in both; a restore that throws no longer stops the other restores in the runner.

| Aspect | `pls` over HTTP | Browser runner | Consequence |
|---|---|---|---|
| Who the requests run as | the key of the spec or step (`as_key`), default key otherwise | the logged-in user | The runner refuses, unsent, a spec or step with `as_key` (status `error`): role tests run with `pls test` |
| Result file | `transport: "http"`, per test `as: <key>` | `transport: "browser"`, per test `as: "session-user"`, `executed_at` | A result says which transport produced it |
| `editPage` (button shown?) | skipped, test becomes `pass-api-only` | real check of the edit screen | UI checks need the runner (see Limits) |
| Write guards | role, `allow_write`, G4 outside dev, mail / jobs checks, confirmation | only "the plan was made for dev" (`env_role`) and the plan-steps rule | The runner never writes stg or prod (ADR-0014 TB-7) |
| Records of a run | `apply-log.json`, plan status, run log, read-back with `mark-applied` state | returns JSON only | After a runner apply the person exports every site and runs `pls mark-applied` |
| Read before each write | each site read again right before its own write | same | — |
| Restore after a failed apply | each restore read back; `rolled-back` only when verified | restore answered 200 = restored, not read back | A runner `rolled-back` is confirmed by export + `mark-applied` |
| Request timeout | per connection (1–600 s); a timeout after sending is `uncertain` | the browser's own | No `uncertain` state in the runner |
| Migrations | `pls migrate` (guards, recorded in `plan.json`) | `bulkUpsert` for a dev plan, nothing recorded | Guarded runs use `pls migrate` |
| Comparing expectations | numbers by value (1.0 = 1), objects regardless of key order | `JSON.stringify` equality | An expectation on an object or a float may differ; write scalar expectations |
| Unexpected error inside a test | only transport errors become `error`; a programming error stops the run | any error becomes that test's `error` | — |
| New site id in a bootstrap answer | `Id` | `Id` or `Response.Id` | — |

## Tests outside dev and the typed confirmation (2026-11-10, design review WS2-F5 / C4)

- `pls test` on an environment whose role is not `dev` sends tests that create, change or delete records only with the person's word: `--release <id>` naming the release under test, whose recorded G4 approval covers it (same record and content binding as `apply`; the release must target that environment), or, without a release, the environment name typed at a terminal, or `--yes` on the person's instruction. Read-only specs and tests on dev ask nothing. Smoke tests after a stg apply therefore run as `pls test … --env stg --release <R>`.
- A typed confirmation (`apply`, `bootstrap`, `migrate`, `kb-verify`, `test`) counts only when stdin is a terminal. Text piped into the command is refused: it was `--yes` without the flag. An agent's shell has no terminal, so an agent can confirm only with `--yes`, which the skills allow only on the person's instruction for the target they name.
- Not done: the kind of confirmation (`typed` / `--yes`) is not written to `apply-log.json` (review suggestion; TD-19 keeps the run-log items).

## Open questions (2026-11-09, recovery states)

`apply` and `mark-applied` now read sites back after a failure. Each site is classified as applied, not applied or differs, and a failure never ends in an applied state. Two Pleasanter 1.5.x behaviours are assumed and not yet probed:

1. **`updatesite` is atomic.** A write that times out is either fully stored or not stored at all. If it can store part of a payload, such a site reads back as "differs", and only the status `recovery-required` catches that case.
2. **A restore reads back equal to `rollback-<site>.json`.** The rollback payload comes from a live export, so it should come back unchanged. If Pleasanter canonicalises it on save (D8), every successful rollback over HTTP ends `recovery-required` instead of `rolled-back`. That is safe but noisy; a KB probe on dev should confirm it.
3. **`getsite` returns the stored `Permissions` of a site that inherits from a parent.** Read-back and drift now compare the title and, when git manages them, the permissions a payload writes. If a site with `InheritPermission` set to a parent returns the parent's list or an empty list, every such release reads back as "differs" and later drift checks refuse. Probe it on dev before relying on permission drift for inheriting sites. If the list is not stable, compare only `inherit` for those sites.
