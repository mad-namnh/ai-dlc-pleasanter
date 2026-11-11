# REQ-021 — Contracts still in force are in the app from the first day

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A7, A14`
- **Type (EARS):** ubiquitous

## Requirement

The system shall contain, from its first day of operation, every contract of the current Excel file that is still in force.

## Acceptance criteria

1. The number of migrated records equals the number of in-force contracts in the source list 総務部 hands over (about 140 of about 180).
2. Contracts of the Excel file that have already ended (解約) are not migrated.
3. For a sample of migrated contracts, every field of REQ-001 matches the source row; the PDF is attached where the source has one.
4. Every migrated contract has 契約名, 取引先, 契約終了日 and 担当者 (REQ-002 does not protect bulk writes — KB D27).
5. Migrated contracts have status 有効 `[assumed]` (index #12); 総務部 prepares the source data `[assumed]` (index #12).
6. Migration is finished before go-live, which must be before 2027-04-01 (A7).

## Notes

- Migrated contracts whose 契約終了日 is already within 60 or 30 days at go-live: whether they get a reminder is open (index #10).
- The Excel file is customer business data: it stays out of git and chat (project CLAUDE.md, hard rule 4).
