# REQ-002 — Required items

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A2
- **Type (EARS):** unwanted behaviour

## Requirement

If a user saves a contract on the edit screen while 契約名, 取引先, 契約終了日 or 担当者 is empty, then the system shall refuse the save.

## Acceptance criteria

1. On the edit screen, saving a new contract with 契約名 empty is refused and no contract is created; the same for 取引先, for 契約終了日 and for 担当者, each tested alone.
2. Saving a contract with the four items filled and every other item empty succeeds.
3. Changing an existing contract so that one of the four items becomes empty is refused and the stored value is kept.

## Notes for P2

- KB D27 (1.5.2): "required" is a screen setting only; a write through the API or an import is not refused. The requirement is therefore stated as screen behaviour, as the KB tells P1 to do. Whether writes outside the screen must also be refused was not asked for.
