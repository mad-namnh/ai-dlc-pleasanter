# REQ-008 — A cancelled contract is never reopened

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A10`
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract is 解約, then the system shall refuse any change of its status.

## Acceptance criteria

1. A 総務担当 tries to change a 解約 contract to 有効, 更新検討中 or 更新済, on the edit screen and through the API; each attempt is refused and the status stays 解約.
2. The 総務課長 tries the same; it is refused.

## Notes

- `[unverified]`: the KB has no entry on refusing every status change out of one status (edit screen and API). P2 must verify before designing; nothing here promises how.
