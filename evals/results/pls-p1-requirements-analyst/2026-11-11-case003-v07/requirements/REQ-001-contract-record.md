# REQ-001 — One record per vendor contract with its fields

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A1`
- **Type (EARS):** ubiquitous

## Requirement

The contract site shall hold one record per vendor contract with the fields 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (円), 担当者, 担当部門 and the attached contract PDF.

## Acceptance criteria

1. A 総務担当 can create a contract on the edit screen and enter 契約名, 取引先, 契約開始日, 契約終了日, 自動更新, 月額, 担当者 and 担当部門; after saving, the API `get` of the record returns each value as entered.
2. 自動更新 offers exactly the choices あり and なし.
3. 契約開始日 and 契約終了日 accept a date; 月額 accepts a number in yen.
4. A PDF file can be attached to the contract and downloaded again from the record.
5. 取引先 is entered on the contract itself `[assumed]` (index #4); 担当者 is a Pleasanter user `[assumed]` (index #5); 担当部門 is one of the 6 departments `[assumed]` (index #6).

## Notes

- Whether a renewal updates this record or creates a new one is open (index #2).
- The 「更新確認済」 tick Lan asked for in A13 is not part of this requirement: its list form is impossible (C1, KB D9) and whether the tick itself is still wanted is open (index #13).
