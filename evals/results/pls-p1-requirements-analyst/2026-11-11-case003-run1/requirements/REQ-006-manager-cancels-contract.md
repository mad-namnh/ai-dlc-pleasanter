# REQ-006 — 総務課長 moves a contract to 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A3, A6, A9
- **Type (EARS):** event-driven

## Requirement

When the 総務課長 moves a contract to 解約, the system shall set the state of that contract to 解約.

## Acceptance criteria

1. As 総務課長, moving a contract in 更新検討中 to 解約 succeeds and the contract is read back in 解約.
2. As 総務課長, moving a contract in 有効 to 解約 succeeds — `[assumed]`, index question 3.
3. As 総務課長, moving a contract in 更新済 to 解約 is not offered — `[assumed]`, index question 3.
4. The other items of the contract are unchanged by the move.

## Notes

- From which states 解約 is possible was not answered (A9: "Còn làm được từ giai đoạn nào thì chị không rõ"). Criteria 2 and 3 rest on the assumption only.
