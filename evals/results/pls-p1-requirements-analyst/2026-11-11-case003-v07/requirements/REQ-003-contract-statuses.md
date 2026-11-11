# REQ-003 — Contract statuses

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A10`
- **Type (EARS):** ubiquitous

## Requirement

The system shall give every contract exactly one of the statuses 有効, 更新検討中, 更新済 and 解約.

## Acceptance criteria

1. The status of a contract offers exactly 有効, 更新検討中, 更新済 and 解約.
2. A new contract is saved with status 有効 `[assumed]` (index #20).
3. The API `get` of a contract returns its current status.

## Notes

- Transitions are REQ-004 to REQ-008. Transitions outside the path 有効 → 更新検討中 → 更新済 / 解約, and what follows 更新済, are open (index #7).
