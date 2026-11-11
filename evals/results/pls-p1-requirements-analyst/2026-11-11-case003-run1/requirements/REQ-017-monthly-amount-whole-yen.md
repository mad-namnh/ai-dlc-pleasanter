# REQ-017 — 月額 is a whole number of yen, 0 or more

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A13
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract is saved with a 月額 that is not a whole number of yen of 0 or more, then the system shall refuse the save.

## Acceptance criteria

1. Saving a contract with 月額 = -1 is refused; nothing is stored.
2. Saving a contract with 月額 = 1000.5 is refused.
3. Saving a contract with 月額 = 0 succeeds.
4. Saving a contract with 月額 = 120000 succeeds and 120000 is read back.
5. Saving a contract with 月額 empty succeeds (月額 is not a required item, A2).

## Notes for P2

- `[unverified]` The knowledge base has no entry on refusing a number below a minimum or with decimals. P2 must verify — index, "For P2", item U6.
