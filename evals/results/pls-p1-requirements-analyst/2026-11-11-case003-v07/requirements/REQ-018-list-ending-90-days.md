# REQ-018 — List of contracts ending in the next 90 days

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A13`
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a list of the contracts whose 契約終了日 falls within the next 90 days, sorted by 契約終了日.

## Acceptance criteria

1. With contracts ending today, today + 90 and today + 91 days, the list shows the first two and not the third, the earliest 契約終了日 first.
2. A contract whose 契約終了日 is already past is not shown `[assumed]` (index #14).
3. 解約 contracts are not shown; 有効, 更新検討中 and 更新済 contracts are `[assumed]` (index #14).
4. The list moves with the date: no one has to change the date range by hand.
5. A department user sees in it only contracts of their own 担当部門 (REQ-011).

## Notes

- `[unverified]`: the KB has no entry on a list filtered on a date range relative to today (D24 covers only "overdue" on the built-in completion date). P2 must verify before designing.
- Who opens it and whether it is exported: open (index #11).
