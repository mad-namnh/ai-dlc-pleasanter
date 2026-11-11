# REQ-009 — 総務担当 create and change all contracts

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A6
- **Type (EARS):** ubiquitous

## Requirement

The system shall allow each 総務担当 to create contracts and to change every contract.

## Acceptance criteria

1. As 総務担当, creating a contract succeeds.
2. As 総務担当, changing an item of a contract created by another 総務担当 succeeds.
3. As 総務担当, changing a contract of any 担当部門 succeeds.
4. The right holds for each of the 3 総務担当 (role test with one test user of that role; the role tests are `deferred` in the project profile).

## Notes

- The change of state to 解約 is excluded (REQ-007); a contract in 解約 keeps its state (REQ-008).
