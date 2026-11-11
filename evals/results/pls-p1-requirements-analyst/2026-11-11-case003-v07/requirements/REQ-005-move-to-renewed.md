# REQ-005 — 総務担当 moves a contract to 更新済

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A4`
- **Type (EARS):** state-driven

## Requirement

While a contract is 更新検討中, the system shall allow a 総務担当 to change its status to 更新済.

## Acceptance criteria

1. A 総務担当 changes a 更新検討中 contract to 更新済; the record then has status 更新済.
2. A 有効 contract cannot be changed directly to 更新済 `[assumed]` (index #7).
3. A user of 各部門の担当者 cannot make this change (REQ-012).

## Notes

- How the new contract period is recorded after a renewal (same record or a new one) is open (index #2); 更新済 is treated as a final status `[assumed]` (index #7).
