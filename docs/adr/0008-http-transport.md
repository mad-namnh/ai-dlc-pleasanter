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
| `pls test SPEC… --env E --site S [--var k=v]` | same spec format as the runner; each spec's `as_key` picks the role's key, so role tests need no login switch |
| `pls backup --env E --site S --out DIR` | every record, for migrations (ADR-0004) |

**Connections are local, never in git:** `.pls/connections.json` (gitignored; template `connections.example.json`) holds the URL per environment, key references and `allow_write`. Keys are referenced as `env:NAME` (environment variable) or `file:NAME` (file under `.pls/`); literal keys are refused. Each person uses their own keys; test users' keys belong to the test users.

**Write guard:** environments.json `role` dev or stg **and** local `allow_write: true`; `role: prod` is never written by this tool. `apply` and `bootstrap` ask the operator to type the release id (agents do not pass `--yes` unless the person asks).

**The browser runner stays** as the fallback for sandboxed agents without a network path. Both transports read and write the same files (plan, payloads, rollbacks, test specs, results), so a release can be planned by one and applied by the other.

## Limits

- An API key cannot render the edit screen: `editPage` steps (is a button shown?) are skipped and the test is reported `pass-api-only`. Coverage counts it, the result says so. Button visibility is covered by the process access control (D20) and by the API refusal; a UI check with the browser runner is needed only for a new kind of design.
- API keys are as powerful as their user. Use test users with the role's rights, not admin keys, for role tests.

## Consequences

- ADR-0003 option A (runner in the customer network) can use the same `pls apply` with the customer's own keys and connection file; the agent never sees them.
- Token cost of P3–P5 drops to the size of the commands and their summaries.

## Findings from the first real run (2026-11-05)

- A role test run with another role's key does damage: refusals it expects succeed (a fixture was deleted). `pls test` and `pls http-check` now refuse/warn when two roles resolve to the same key.
- Fixtures belong in the spec, created with the 総務 key by step-level `as_key`, so a run never depends on IDs typed by hand.
