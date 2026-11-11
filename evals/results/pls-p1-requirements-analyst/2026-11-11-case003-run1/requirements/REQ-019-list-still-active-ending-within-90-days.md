# REQ-019 — List for 総務担当: ending within 90 days and still 有効

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A16 (the need stated behind constraint C1)
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide the 総務担当 with a list of every contract that is in 有効 and whose 契約終了日 falls within the next 90 days.

## Acceptance criteria

1. As 総務担当, a contract in 有効 with 契約終了日 = today + 30 days is in the list.
2. A contract in 更新検討中, 更新済 or 解約 with the same 契約終了日 is not in the list.
3. A contract in 有効 with 契約終了日 = today + 91 days is not in the list.
4. After a 総務担当 moves a listed contract to 更新検討中 (REQ-004), it is no longer in the list.
5. The list contains contracts of every 担当部門.

## Notes

- This requirement replaces the list "contracts where 更新確認済 is not ticked" asked for in A14, which Pleasanter cannot provide (constraint C1, KB D9). A16: "Dùng trạng thái cũng được, miễn là thấy được danh sách đó."
- Whether the checkbox 「更新確認済」 is still wanted is open — index question 8.
- `[unverified]` Filter on a date relative to today: same as REQ-018 — index, "For P2", item U4.
