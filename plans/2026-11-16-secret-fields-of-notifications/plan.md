# Plan — credential fields of notifications and reminders (settings coverage WS6c)

- **Date / branch / parent commit:** 2026-11-16 / `brownfield-adr` / `2dca8a3`
- **Objective:** L-SEC-01 and its refusals (unpack, harvest, adopt, release-plan) catch credentials in notification and reminder fields whatever their text looks like, not only by pattern.
- **Tier:** Critical (secrets, I7).
- **Scope:** new `tools/pls/pls_secret_fields.py`; `pls.secrets_in` adds its names. Fields (Pleasanter_1.5.2.0 `Libraries/Settings/Notification.cs`, `Reminder.cs`, source-derived): `Token` of Notifications / Reminders (incl. `Processes[].Notifications`); webhook URL in `Notification.Address` of types 2, 6, 7, 10 and `Reminder.To` of types 2, 6, 7, 9; `Headers` naming a credential header; credential query parameter in an HttpClient (9) `Address`.
- **Out of scope:** `${secret:…}` resolution (ADR-0005 forbids secrets in SiteSettings; no form is allowed); mail addresses (L-MAIL-01, ADR-0010).
- **Files:** `tools/pls/pls_secret_fields.py` (new), `tools/pls/pls.py`, `tools/pls/tests/test_secrets_never_reach_the_repository.py`, `docs/architecture.md` (L-SEC-01 row), this folder.
- **Invariants and ADRs touched:** I7, ADR-0005 (implements Decision principle 5; Decision text unchanged).
- **Stop points expected:** none (a guard is made stricter, not weaker).
- **Acceptance criteria:**
  1. Each listed field, when filled, is named by `secrets_in` (dict or JSON text, any depth); values are never printed.
  2. Mail notifications, an HttpClient URL without a credential, a plain header and empty fields are not flagged.
  3. `unpack` of an export with a Slack webhook URL writes nothing; `lint` reports L-SEC-01 for a token written into `config/`.
  4. New tests fail on the parent; both Python suites (3.12, 3.10) and the node suite pass.
  5. Review: no open Critical / High.
- **Tests:** `CredentialFieldsTest` (3 tests) in `test_secrets_never_reach_the_repository.py`.
- **Subagents planned:** `pls-x-reviewer` (opus, high — Critical, secrets).
- **Documents to update in the same commit:** `docs/architecture.md` L-SEC-01; `HANDOFF.md` resume line.
