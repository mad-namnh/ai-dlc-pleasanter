# REQ-017 — List of contracts ending within 90 days

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A13
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a list of the contracts whose 契約終了日 falls within the next 90 days, sorted by 契約終了日.

## Acceptance criteria

1. With contracts ending in 10, 90 and 91 days, the list holds the first two and not the third.
2. The list shows the contract ending in 10 days before the one ending in 90 days.
3. *(Other filters and an export of the list: not answered (A13). `[assumed]` none — question 9.)*

## Notes for P2

- **`[unverified]`** — the KB has the view sorter and the `Overdue` filter of Issues sites (D24), but no entry on a filter "date within the next N days". P2 must verify before designing. Listed in `index.md` under "To verify in P2".
- A13 does not say which statuses the list holds; as written it holds every status.
