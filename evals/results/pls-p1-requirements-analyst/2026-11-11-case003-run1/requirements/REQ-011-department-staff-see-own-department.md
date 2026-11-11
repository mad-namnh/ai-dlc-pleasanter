# REQ-011 — 各部門の担当者 see only their department's contracts

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A6
- **Type (EARS):** ubiquitous

## Requirement

The system shall show each 各部門の担当者 only the contracts whose 担当部門 is that person's own department.

## Acceptance criteria

1. As 各部門の担当者 of department X, the contract list contains the contracts with 担当部門 X.
2. As the same user, the list contains no contract with another 担当部門.
3. As the same user, opening a contract of another 担当部門 directly (by its address or through the API) is refused.
4. After 総務担当 changes the 担当部門 of a contract from X to Y, the user of department X no longer sees it and a 各部門の担当者 of department Y sees it.

## Notes for P2

- `[unverified]` The knowledge base has no entry on restricting what a user sees per record (D19 and D20 cover a read-only right on a whole site and access to actions). P2 must verify on dev how this can be met before designing it — index, "For P2", item U3.
