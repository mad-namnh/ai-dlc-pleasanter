# REQ-012 — Department users cannot change contracts

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A4`
- **Type (EARS):** unwanted behaviour

## Requirement

If a user of 各部門の担当者 tries to create, edit or change the status of a contract, then the system shall refuse it.

## Acceptance criteria

1. A department user tries to create a contract through the API; it is refused (HTTP 403) and no record is created.
2. The same user tries to update a contract of their own 担当部門 through the API; it is refused and the record is unchanged.
3. On the edit screen the same user sees no save button for a contract of their own department.
4. A status change attempted by the same user is refused.

## Notes

- Read-only rights at site level are verified: writes and actions → HTTP 403, but buttons of actions without access control are still shown to read-only users (KB D19, D20).
