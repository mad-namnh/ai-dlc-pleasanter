# REQ-003 — States of a contract

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A3
- **Type (EARS):** ubiquitous

## Requirement

The system shall hold every contract in exactly one of the states 有効, 更新検討中, 更新済 and 解約.

## Acceptance criteria

1. The state of a contract can be read and is one of 有効, 更新検討中, 更新済, 解約.
2. No other state can be chosen for a contract on the edit screen.
3. A newly created contract is in state 有効 — `[assumed]`, index question 11.

## Notes

- What follows 更新済 for the next contract term was not answered (A8): `[assumed]` 更新済 is the last state of that record and the next term is entered as a new contract — index question 2.
- How contracts with 自動更新 あり pass through the states was not answered (A4): `[assumed]` the same as other contracts — index question 4.
