# REQ-013 — Reminder mail to 担当者 60 days before 契約終了日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contract-management.md` — A7
- **Type (EARS):** event-driven

## Requirement

When the date is 60 days before the 契約終了日 of a contract, the system shall send a mail to the 担当者 of that contract.

## Acceptance criteria

1. For a contract with 契約終了日 = D, a mail addressed to its 担当者 is sent on the day D − 60 days.
2. No such mail is sent for that contract on the day before.
3. The mail is sent once for that 契約終了日 — `[assumed]`, index question 13.
4. The mail text is Japanese and names 契約名, 取引先 and 契約終了日 — `[assumed]`, index question 13.
5. No mail is sent for a contract in 解約 (REQ-015).
6. *(Not automatically testable: mail delivery cannot be observed through the API, and `environments.json` has `side_effects.mail: unknown` on dev; a person checks the received mail. Waiting 60 days is not possible in a test: the test uses a contract whose 契約終了日 is set to today + 60 days.)*

## Notes

- Other cases in which this mail must not be sent (更新検討中, 更新済, 自動更新 あり) were not answered (A11, A4): `[assumed]` only 解約 is excluded — index questions 5 and 4.
- `[unverified]` The knowledge base has no verified entry on a mail sent a number of days before a date. P2 must verify — index, "For P2", item U1.
