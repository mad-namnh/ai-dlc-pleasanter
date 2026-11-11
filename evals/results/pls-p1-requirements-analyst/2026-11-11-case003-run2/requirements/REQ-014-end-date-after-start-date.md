# REQ-014 — 契約終了日 must be after 契約開始日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A12
- **Type (EARS):** unwanted behaviour

## Requirement

If the 契約終了日 of a contract is not after its 契約開始日 when the contract is saved, then the system shall refuse the save.

## Acceptance criteria

1. Saving a contract with 契約開始日 2027-04-01 and 契約終了日 2027-03-31 is refused; the contract is not created or not changed.
2. Saving with 契約開始日 2027-04-01 and 契約終了日 2028-03-31 succeeds.
3. *(The same day for both dates: `[assumed]` refused — "phải sau". A contract without 契約開始日 — the field is not required: `[assumed]` the rule does not apply — question 17.)*

## Notes for P2

- KB D25: Pleasanter has no built-in date-order check; a refusal needs a script. The message shown to the user is Japanese and is not given yet.
