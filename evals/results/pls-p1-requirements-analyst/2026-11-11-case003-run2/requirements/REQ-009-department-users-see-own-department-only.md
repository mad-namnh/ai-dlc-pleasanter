# REQ-009 — 各部門の担当者 see only the contracts of their own 担当部門

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A5
- **Type (EARS):** ubiquitous

## Requirement

The system shall show a 各部門の担当者 only the contracts whose 担当部門 is that person's own department.

## Acceptance criteria

1. A 各部門の担当者 of department X can open a contract whose 担当部門 is X.
2. The same user cannot open a contract whose 担当部門 is Y, by its address or through the API, and does not find it in any list.
3. *(A contract without 担当部門 — the field is not required: `[assumed]` no 各部門の担当者 sees it — question 15.)*

## Notes for P2

- **`[unverified]`** — the KB has entries on permissions per site (D15, D19) and per process (D20), but none on limiting which records of one site a user can see. Nobody has shown that Pleasanter 1.5.x can do this as stated; P2 must verify it on dev before designing. Listed in `index.md` under "To verify in P2".
