# REQ-006 — A contract in 解約 is not reopened

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A3, A11
- **Type (EARS):** state-driven

## Requirement

While a contract is in 解約, the system shall refuse every change of its status.

## Acceptance criteria

1. For a contract in 解約, a change of status to 有効, 更新検討中 or 更新済 is refused for 総務担当 and for 総務課長 (through the API), and the status stays 解約.
2. On the edit screen of a contract in 解約 no action that changes the status is offered.
