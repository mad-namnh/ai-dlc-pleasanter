# REQ-020 — Total 月額 per 取引先

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A14, A15
- **Type (EARS):** ubiquitous

## Requirement

The system shall provide a list that shows the total of 月額 for each 取引先.

## Acceptance criteria

1. With two contracts of 取引先 X with 月額 100000 and 50000, and one contract of 取引先 Y with 月額 30000, the list shows 150000 for X and 30000 for Y.
2. After the 月額 of one contract of X is changed to 60000, the list shows 110000 for X.
3. A contract with 月額 empty adds 0 to its 取引先's total.

## Notes

- A15: "Phần Teams và phần tổng 月額 có thể làm sau nếu cần." Whether this list belongs to the first release is for G1 to decide: `[assumed]` later, not in the first release — index question 9.
- Which states count in the total (e.g. whether 解約 contracts are included) was not said: `[assumed]` every contract counts — index question 9.
- `[unverified]` The knowledge base knows a total written from child records to a parent record (D16); whether a total per 取引先 can be shown as a list without that structure is not in the KB. P2 must verify — index, "For P2", item U5.
