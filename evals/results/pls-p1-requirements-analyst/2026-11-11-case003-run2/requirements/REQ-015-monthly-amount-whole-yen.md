# REQ-015 — 月額 is a whole number of yen, 0 or more

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A12
- **Type (EARS):** unwanted behaviour

## Requirement

If the 月額 of a contract is not a whole number of yen of 0 or more when the contract is saved, then the system shall refuse the save.

## Acceptance criteria

1. Saving with 月額 `-1` is refused.
2. Saving with 月額 `1000.5` is refused.
3. Saving with 月額 `0` and with 月額 `120000` succeeds.

## Notes for P2

- **`[unverified]`** — the KB has no entry on limits for numeric input (minimum, decimal places), on the screen or through the API. P2 must verify before designing. Listed in `index.md` under "To verify in P2".
