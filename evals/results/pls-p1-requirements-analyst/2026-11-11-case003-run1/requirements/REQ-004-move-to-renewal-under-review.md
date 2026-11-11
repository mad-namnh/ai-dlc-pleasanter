# REQ-004 — 総務担当 moves a contract to 更新検討中

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A3
- **Type (EARS):** event-driven

## Requirement

When a 総務担当 moves a contract that is in 有効 to 更新検討中, the system shall set the state of that contract to 更新検討中.

## Acceptance criteria

1. As 総務担当, moving a contract in 有効 to 更新検討中 succeeds and the contract is read back in 更新検討中.
2. The other items of the contract are unchanged by the move.
3. As 各部門の担当者, the same move is refused and the contract stays in 有効 (see REQ-012).

## Notes

- Whether 総務課長 may also make this move was not said: `[assumed]` no — index question 12.
