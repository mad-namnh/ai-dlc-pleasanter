# REQ-021 — The 90-day list shows a 各部門の担当者 only the own department's contracts (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-009 impact analysis on REQ-017: A5 limits what a 各部門の担当者 may see, A13 asks for a list over all contracts; the list must not show them more than REQ-009 allows (`sources/2026-11-11-interview-vendor-contracts.md` — A5, A13)
- **Type (EARS):** state-driven

## Requirement

While the user is a 各部門の担当者, the list of REQ-017 shall contain only contracts whose 担当部門 is that user's own department.

## Acceptance criteria

1. With contracts of departments X and Y both ending in 30 days, a 各部門の担当者 of X sees only the contract of X in the list.
2. 総務担当 and 総務課長 see both.

## Notes for P2

- **`[unverified]`** — follows REQ-009: the KB has no entry on limiting which records of one site a user can see, in a list or otherwise. Listed in `index.md` under "To verify in P2".
- The total of REQ-019 has the same exposure (a total over contracts the reader may not see); its readers are an open point (question 8), so no requirement is derived for it yet.
