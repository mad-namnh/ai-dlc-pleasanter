# REQ-006 — 総務課長 moves a contract to 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A4`
- **Type (EARS):** state-driven

## Requirement

While a contract is 更新検討中, the system shall allow the 総務課長 to change its status to 解約.

## Acceptance criteria

1. The 総務課長 changes a 更新検討中 contract to 解約; the record then has status 解約.
2. Whether a 有効 contract can be changed directly to 解約 is open `[assumed]`: no (index #7).

## Notes

- Refusal for everyone else: REQ-007.
