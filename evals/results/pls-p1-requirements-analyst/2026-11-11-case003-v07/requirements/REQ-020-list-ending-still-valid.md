# REQ-020 — List of contracts ending in 90 days that are still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A15` (the need behind constraint C1, A13)
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide the 総務担当 with a list of the contracts whose 契約終了日 falls within the next 90 days and whose status is still 有効.

## Acceptance criteria

1. Two contracts ending in 30 days, one 有効 and one 更新検討中: the list shows only the 有効 one.
2. A 有効 contract ending in 91 days is not shown; one ending today is shown.
3. When a 総務担当 changes a listed contract to 更新検討中, it leaves the list.
4. The list uses the status, not a tick (A15: 「Dùng trạng thái cũng được」).

## Notes

- Replaces the form Lan first asked for (a list of contracts whose 「更新確認済」 tick is not set, A13), which Pleasanter 1.5.2 cannot filter (C1, KB D9).
- `[unverified]`: same relative-date filter as REQ-018. P2 must verify before designing.
