# REQ-002 — Required fields

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A2
- **Type (EARS):** unwanted behaviour

## Requirement

If 契約名, 取引先, 契約終了日 or 担当者 is empty when a contract is saved on the edit screen, then the system shall refuse the save.

## Acceptance criteria

1. On the edit screen, saving a new contract with any one of the four fields empty is refused and the contract is not created (one check per field).
2. On the edit screen, saving with all four filled and every other field empty succeeds.
3. *(Scope of the check: KB D27 — "required" is enforced on the screen only; a contract written through the API or an import is not refused. `[assumed]` screen only is enough — question 16.)*
