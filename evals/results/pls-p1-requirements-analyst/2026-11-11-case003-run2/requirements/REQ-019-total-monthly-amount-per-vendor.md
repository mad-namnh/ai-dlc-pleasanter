# REQ-019 — Total of 月額 per 取引先

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A7 (unprompted), A13
- **Type (EARS):** ubiquitous

## Requirement

The system shall show, for each 取引先, the total of the 月額 of its contracts.

## Acceptance criteria

1. With two contracts of 取引先 X at 月額 10000 and 25000, the total shown for X is 35000.
2. After the 月額 of one of them is changed to 20000, the total shown for X is 45000.
3. *(Who reads the total, what for, and which contracts count: not answered (A14). `[assumed]` 総務担当 and 総務課長; contracts not in 解約 — question 8. Criteria 1 and 2 use contracts in 有効.)*

## Notes for P2

- KB D16, D23: Pleasanter writes totals to a linked parent record; existing parents are not recalculated when the setting is added. Whether 取引先 becomes a record of its own is a design decision, and it interacts with the migration of REQ-020.
- The person said this may come after the first release if time is short (A7, A14). Whether it is in the first release is for G1 to decide.
