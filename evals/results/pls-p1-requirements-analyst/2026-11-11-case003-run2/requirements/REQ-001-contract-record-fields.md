# REQ-001 — Contract record and its fields

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A2
- **Type (EARS):** ubiquitous

## Requirement

The system shall hold one record per contract with a 取引先, with the fields 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (円), 担当者, 担当部門 and the attached contract PDF.

## Acceptance criteria

1. A contract created with all nine items can be read back, through the API and on the edit screen, with the same values.
2. 自動更新 offers exactly the two values あり and なし.
3. A PDF file attached to a contract can be downloaded again from that contract.

## Notes for P2

- Who a 担当者 is (a Pleasanter user or free text) is not answered (A8): `[assumed]` a Pleasanter user with a mail address — question 5.
- Whether 取引先 is text or a record of its own is a design matter (see REQ-019).
