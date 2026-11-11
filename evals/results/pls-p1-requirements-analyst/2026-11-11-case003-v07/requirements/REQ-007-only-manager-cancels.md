# REQ-007 — Only the 総務課長 may set 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A3, A4`
- **Type (EARS):** unwanted behaviour

## Requirement

If a user other than the 総務課長 tries to change a contract's status to 解約, then the system shall refuse the change.

## Acceptance criteria

1. A 総務担当 tries to change a 更新検討中 contract to 解約, on the edit screen and through the API; the change is refused and the status stays 更新検討中.
2. A user of 各部門の担当者 tries the same; it is refused (also REQ-012).
3. The 総務課長 can make the change (REQ-006).

## Notes

- Partly verified: an action can be restricted to named users or groups and is then refused for others through the API (KB D20, D10). Whether every way of changing the status (including the status field on the edit screen and API updates without an action) can be restricted to one person is not in the KB: P2 must verify before designing.
