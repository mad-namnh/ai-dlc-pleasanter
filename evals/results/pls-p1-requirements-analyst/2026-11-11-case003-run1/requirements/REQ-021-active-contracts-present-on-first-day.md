# REQ-021 — Contracts still in force are present on the first day

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A12
- **Type (EARS):** ubiquitous

## Requirement

The system shall hold, on its first day of use, every contract of the 総務部 Excel file that is still in force.

## Acceptance criteria

1. The number of contracts in the system on the first day equals the number of contracts still in force in the Excel file (about 140 of about 180, A12).
2. For a sample of contracts chosen by 総務部, 契約名, 取引先, 契約開始日, 契約終了日, 自動更新, 月額, 担当者 and 担当部門 equal the Excel row.
3. No contract that is already 解約 in the Excel file is in the system.
4. The carried-over contracts are in state 有効 — `[assumed]`, index question 10.
5. The carried-over contracts satisfy REQ-002, REQ-016 and REQ-017; rows that do not are reported to 総務部 and not loaded silently.
6. *(Not automatically testable by the framework: the Excel file is customer data, is not committed, and is handled by the customer's operator or an authorised person; the comparison is run by that person.)*

## Notes

- The first day of use must be before 2027-04-01 (A12, A15).
- Whether the PDF files are carried over was not answered (A12): `[assumed]` not on the first day; they are attached by hand afterwards — index question 6.
- Notes for P2: KB D13, D18 (bulk load keyed on a unique business identifier); D27 and D17 (a load does not pass the screen checks, so criterion 5 must be checked before loading); 担当者 is stored as a user id that differs per environment (D28).
