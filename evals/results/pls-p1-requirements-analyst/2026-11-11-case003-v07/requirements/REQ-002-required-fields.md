# REQ-002 — Required contract fields

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A1`
- **Type (EARS):** unwanted behaviour

## Requirement

If 契約名, 取引先, 契約終了日 or 担当者 is empty when a contract is saved on the edit screen, then the system shall refuse the save.

## Acceptance criteria

1. On the edit screen, saving a new contract with 契約名 empty is refused and the record is not created; the same holds for 取引先, 契約終了日 and 担当者, each tested on its own.
2. A contract with all four fields filled and the other fields empty is saved.
3. *(Edit-screen behaviour only: a required field is a screen check in Pleasanter 1.5.2 and does not refuse API writes or imports — KB D27. Tested on the edit screen, not through the API.)*

## Notes

- Data migrated in bulk (REQ-021) is not protected by this check (D27); the migration must check the four fields itself.
