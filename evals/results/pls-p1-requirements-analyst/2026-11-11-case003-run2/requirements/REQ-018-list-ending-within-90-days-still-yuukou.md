# REQ-018 — 総務担当 see the contracts ending within 90 days that are still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A16 (the need behind constraint C1; replaces the "not ticked" list of A13)
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide to 総務担当 a list of the contracts whose 契約終了日 falls within the next 90 days and whose status is 有効.

## Acceptance criteria

1. A contract in 有効 ending in 30 days is in the list.
2. A contract in 更新検討中, 更新済 or 解約 ending in 30 days is not in the list.
3. A contract in 有効 ending in 91 days is not in the list.
4. When a 総務担当 moves a listed contract to 更新検討中, it leaves the list.

## Notes for P2

- **`[unverified]`** — same reason as REQ-017: the KB has no entry on a filter "date within the next N days". Filtering on status is covered (schema: views, `ColumnFilterHash` on `Status`). Listed in `index.md` under "To verify in P2".
- Constraint C1 (KB D9): the list must not be built on "checkbox 「更新確認済」 not ticked"; the person agreed to the status ("dùng trạng thái cũng được", A16).
