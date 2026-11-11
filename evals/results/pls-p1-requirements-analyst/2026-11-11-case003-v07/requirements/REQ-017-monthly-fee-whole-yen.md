# REQ-017 — 月額 is a whole number of yen, 0 or more

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A12`
- **Type (EARS):** unwanted behaviour

## Requirement

If 月額 is not a whole number of 0 or more, then the system shall refuse to save the contract.

## Acceptance criteria

1. 月額 = -1 is refused; the record is not saved.
2. 月額 = 1000.5 is refused.
3. 月額 = 0 and 月額 = 50000 are saved.
4. *(Edit screen and API are tested separately; whether the API refuses too depends on the design — see notes.)*

## Notes

- `[unverified]`: the KB has no entry on minimum-value or whole-number checks for a number field. P2 must verify before designing.
- Whether 月額 is required is not stated: it is not in A1's required list, so empty is accepted.
