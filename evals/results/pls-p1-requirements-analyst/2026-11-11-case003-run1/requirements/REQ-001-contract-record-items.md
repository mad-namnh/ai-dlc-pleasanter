# REQ-001 — Contract record and its items

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A2
- **Type (EARS):** ubiquitous

## Requirement

The system shall hold one record per contract with a 取引先, carrying the items 契約名, 取引先, 契約開始日, 契約終了日, 自動更新 (あり／なし), 月額 (円), 担当者, 担当部門 and the attached PDF file of the contract.

## Acceptance criteria

1. A contract created with all nine items is read back with the same values for 契約名, 取引先, 契約開始日, 契約終了日, 自動更新, 月額, 担当者 and 担当部門.
2. 自動更新 accepts only あり or なし.
3. A PDF file attached to a contract on the edit screen can be opened from that contract afterwards.
4. The edit screen shows the nine items under exactly these Japanese labels.

## Notes

- How 取引先 and 担当部門 are entered (free text or a list) was not said: `[assumed]` 取引先 is free text and 担当部門 is chosen from the customer's departments — index question 14.
- Who can be chosen as 担当者 was not said (A10): `[assumed]` any user of the system — index question 1.
- A checkbox 「更新確認済」 (A14) is **not** part of this requirement: index question 8.
