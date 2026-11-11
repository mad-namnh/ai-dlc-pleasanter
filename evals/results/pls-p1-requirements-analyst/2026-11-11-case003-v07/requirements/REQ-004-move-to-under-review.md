# REQ-004 — 総務担当 moves a contract to 更新検討中

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A4`
- **Type (EARS):** state-driven

## Requirement

While a contract is 有効, the system shall allow a 総務担当 to change its status to 更新検討中.

## Acceptance criteria

1. A 総務担当 changes a 有効 contract to 更新検討中; the record then has status 更新検討中.
2. A user of 各部門の担当者 cannot make this change (REQ-012).
3. Whether 総務課長 may make this change is open `[assumed]`: no (index #16).
