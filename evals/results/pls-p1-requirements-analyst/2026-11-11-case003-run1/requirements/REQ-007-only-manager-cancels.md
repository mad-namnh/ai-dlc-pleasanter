# REQ-007 — Only 総務課長 may move a contract to 解約

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A3, A6, A9
- **Type (EARS):** unwanted behaviour

## Requirement

If a user other than the 総務課長 attempts to move a contract to 解約, then the system shall refuse the move.

## Acceptance criteria

1. As 総務担当, moving a contract to 解約 is refused and the contract keeps its state.
2. As 各部門の担当者, moving a contract to 解約 is refused and the contract keeps its state.
3. As 総務担当, changing the state to 解約 by editing the contract (not only by a dedicated action) is refused as well.

## Notes for P2

- KB D19, D20 (1.5.2): an action is still shown to a read-only user unless it is restricted to named groups; a refusal alone leaves the button visible. Whether the action must also be hidden from the others was not asked for.
