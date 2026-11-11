# REQ-016 — Checkbox 「更新確認済」 on every contract

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A13
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a checkbox 「更新確認済」 on every contract.

## Acceptance criteria

1. The edit screen of a contract shows the checkbox 「更新確認済」; a new contract has it unticked.
2. A tick saved on a contract reads back as ticked through the API.
3. *(Who ticks it and when: not answered (A17). `[assumed]` a 総務担当, at any time — question 10.)*

## Notes for P2

- Constraint C1 (KB D9): a list of contracts where this checkbox is **not** ticked cannot be built; that list is not a requirement. The need behind it is REQ-018 (A16).
- After A16 ("dùng trạng thái cũng được") it is open whether the checkbox is still wanted: `[assumed]` yes, as asked in A13 — question 11.
