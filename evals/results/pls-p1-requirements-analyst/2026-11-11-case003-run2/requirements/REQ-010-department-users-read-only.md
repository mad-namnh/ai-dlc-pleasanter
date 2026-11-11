# REQ-010 — 各部門の担当者 change nothing

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A5
- **Type (EARS):** unwanted behaviour

## Requirement

If a 各部門の担当者 tries to create or change a contract, then the system shall refuse the operation.

## Acceptance criteria

1. A 各部門の担当者 creates a contract through the API: refused, nothing is created.
2. A 各部門の担当者 updates a contract of the own 担当部門 through the API (a field, or the status): refused, the contract is unchanged.
3. On the edit screen of such a contract no save action is offered to that user.
