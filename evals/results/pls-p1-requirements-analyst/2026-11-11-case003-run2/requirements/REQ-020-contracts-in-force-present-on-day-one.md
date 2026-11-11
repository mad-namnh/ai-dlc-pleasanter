# REQ-020 — Contracts in force are in the app on the first day

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A7
- **Type (EARS):** ubiquitous

## Requirement

The system shall hold, on its first day of use, every contract of the 総務部 Excel file that is still in force (about 140 of about 180).

## Acceptance criteria

1. The number of contracts in the app on the first day equals the number of contracts in force in the Excel file handed over for the migration.
2. For a sample of 10 migrated contracts, 契約名, 取引先, 契約終了日 and 担当者 equal the Excel row.
3. No contract of the Excel file that has already ended is in the app.
4. *(Status of the migrated contracts: not said. `[assumed]` all 有効 — question 14.)*
5. *(Not automatically testable against the customer's file: the Excel file is customer data, is not put into git and is handled by the customer's operator; the count and the sample are checked by a person.)*

## Notes for P2

- First day of use: before 2027-04-01 (A7).
- KB D13, D18: `bulkupsert` needs a unique business key per contract; the Excel file has not been seen, so no key is known. KB D27: required fields are not enforced on import (REQ-002).
- How the attached PDFs of existing contracts get in was not discussed.
