# REQ-016 — 契約終了日 must be after 契約開始日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A12`
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract's 契約終了日 is not after its 契約開始日, then the system shall refuse to save the contract.

## Acceptance criteria

1. Saving a contract with 契約開始日 2027-04-01 and 契約終了日 2027-03-31 is refused, on the edit screen and through the API; the record is not created or not changed.
2. 契約終了日 equal to 契約開始日 is refused `[assumed]` (index #17).
3. 契約開始日 2027-04-01 and 契約終了日 2028-03-31 is saved.
4. With 契約開始日 empty, the check does not apply `[assumed]` (index #18).
5. The refusal tells the user why, in Japanese: 「契約終了日は契約開始日より後の日付を入力してください。」 `[assumed]` (index #22).

## Notes

- Pleasanter has no built-in date-order check; refusing such a save was verified with a script on save (KB D25, 1.5.2). The way to do it is for P2.
