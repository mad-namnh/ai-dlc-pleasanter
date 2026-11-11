# REQ-011 — Department users see only their department's contracts

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A4`
- **Type (EARS):** ubiquitous

## Requirement

The system shall show a user of 各部門の担当者 only the contracts whose 担当部門 is that user's department.

## Acceptance criteria

1. A department user opens the contract list and sees exactly the contracts of their own 担当部門.
2. The same user cannot open a contract of another 担当部門 by its URL or through the API `get`.
3. When a contract's 担当部門 is changed, the users of the old department no longer see it and the users of the new department do.

## Notes

- `[unverified]`: the KB verifies read-only rights per site (D19, D15) but has no entry on visibility per record by the value of a field. P2 must verify before designing; nothing here promises how or that it can be done this way.
- Whether a contract can belong to more than one department is open (index #6).
