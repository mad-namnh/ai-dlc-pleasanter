# REQ-013 — Reminder mail to 担当者 60 days before 契約終了日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md — A5, A11`
- **Type (EARS):** complex (event-driven + state)

## Requirement

When a contract's 契約終了日 is 60 days away and the contract is not 解約, the system shall send a reminder mail to the contract's 担当者.

## Acceptance criteria

1. A 有効 contract with 契約終了日 = today + 60 days: on that day one reminder mail is sent to its 担当者.
2. A 解約 contract with 契約終了日 = today + 60 days: no mail is sent (A5, A11: 「解約 thì không gửi gì」).
3. A 更新検討中 or 更新済 contract with 契約終了日 = today + 60 days: the mail is sent `[assumed]` (index #9 for 更新済).
4. A contract registered when fewer than 60 days remain gets no catch-up mail `[assumed]` (index #10).
5. "60 days" counts calendar days `[assumed]` (index #19).
6. The mail names the contract (契約名, 取引先, 契約終了日) `[assumed]` (index #23).
7. *(Not automatically testable: mail delivery. Test which records the reminder selects on a given day; check one real delivery by hand. Mail side effects of `dev` are `unknown` in `environments.json`.)*

## Notes

- `[unverified]`: the KB has no entry on mail sent on a date relative to a record's date (scheduled reminders); site notifications in the KB act on record changes (schema.md). P2 must verify before designing; nothing here promises how.
- Requires that 担当者 is a Pleasanter user with a mail address `[assumed]` (index #5).
