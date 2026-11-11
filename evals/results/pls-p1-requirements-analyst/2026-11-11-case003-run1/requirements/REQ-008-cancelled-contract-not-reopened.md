# REQ-008 — A contract in 解約 is not reopened

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A3
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract is in 解約, then the system shall refuse any change of its state.

## Acceptance criteria

1. As 総務担当, moving a contract in 解約 to 有効, to 更新検討中 or to 更新済 is refused and the contract stays in 解約.
2. As 総務課長, the same three moves are refused and the contract stays in 解約.
3. A contract in 解約 can still be read by the users who may read it (REQ-010, REQ-011).

## Notes

- Whether the other items of a contract in 解約 may still be changed by 総務担当 was not said; this requirement covers the state only, as A3 does ("Hợp đồng đã 解約 thì không mở lại nữa").
