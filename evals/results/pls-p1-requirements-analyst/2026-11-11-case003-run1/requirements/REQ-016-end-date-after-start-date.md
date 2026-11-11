# REQ-016 — 契約終了日 must be after 契約開始日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A13
- **Type (EARS):** unwanted behaviour

## Requirement

If a contract is saved with a 契約終了日 that is not after its 契約開始日, then the system shall refuse the save.

## Acceptance criteria

1. Saving a contract with 契約開始日 2027-04-01 and 契約終了日 2027-03-31 is refused; nothing is stored.
2. Saving a contract with 契約開始日 and 契約終了日 on the same day is refused.
3. Saving a contract with 契約開始日 2027-04-01 and 契約終了日 2028-03-31 succeeds.
4. Changing an existing contract so that 契約終了日 is no longer after 契約開始日 is refused and the stored dates are kept.
5. The refusal shows a message in Japanese to the user — `[assumed]` text 「契約終了日は契約開始日より後の日付にしてください。」, index question 15.
6. A contract saved with 契約開始日 empty is not refused by this rule — `[assumed]`, index question 15 (契約開始日 is not a required item, A2).

## Notes for P2

- KB D25 (1.5.2): there is no built-in check of the order of two dates; refusing the save needs a server script. Under I5 that needs a written reason in the design.
