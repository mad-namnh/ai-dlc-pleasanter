# REQ-005 — Only 総務課長 moves a contract to 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A3, A5, A11
- **Type (EARS):** unwanted behaviour

## Requirement

If a user other than 総務課長 tries to move a contract to 解約, then the system shall refuse the change.

## Acceptance criteria

1. 総務課長 moves a contract in 更新検討中 to 解約: the contract reads back as 解約.
2. A 総務担当 tries the same through the API: refused, the status is unchanged.
3. A 各部門の担当者 tries the same through the API: refused, the status is unchanged.
4. *(From which statuses 総務課長 may move to 解約 is not answered (A11). `[assumed]` only from 更新検討中 — question 4. Criterion 1 holds under every answer.)*
