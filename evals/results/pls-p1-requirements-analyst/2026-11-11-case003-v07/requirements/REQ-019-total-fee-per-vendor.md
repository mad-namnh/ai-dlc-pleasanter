# REQ-019 — Total 月額 per 取引先

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A13`
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a list of the total 月額 for each 取引先.

## Acceptance criteria

1. With two contracts of 取引先 A (月額 10000 and 20000) and one of 取引先 B (月額 5000), the list shows A = 30000 and B = 5000.
2. 解約 contracts are not counted `[assumed]` (index #15).
3. After 月額 of a contract changes, the list shows the new total the next time it is opened.

## Notes

- `[unverified]`: the KB has no entry on totals grouped by a field in a list (D16 / D23 are totals written into a linked parent record). P2 must verify before designing.
- Whether 取引先 is managed as separate data is open (index #4).
