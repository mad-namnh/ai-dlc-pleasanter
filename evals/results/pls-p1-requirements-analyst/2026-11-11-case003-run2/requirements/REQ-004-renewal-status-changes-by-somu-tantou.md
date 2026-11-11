# REQ-004 — 総務担当 moves a contract to 更新検討中 and to 更新済

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A3
- **Type (EARS):** event-driven

## Requirement

When a 総務担当 moves a contract from 有効 to 更新検討中 or from 更新検討中 to 更新済, the system shall save the contract with the new status.

## Acceptance criteria

1. A 総務担当 changes a contract in 有効 to 更新検討中: the contract reads back as 更新検討中.
2. A 総務担当 changes a contract in 更新検討中 to 更新済: the contract reads back as 更新済.
3. *(Not covered: a move back from 更新検討中 to 有効 — `[assumed]` not allowed, question 13; any move out of 更新済 — `[assumed]` none, question 3.)*
