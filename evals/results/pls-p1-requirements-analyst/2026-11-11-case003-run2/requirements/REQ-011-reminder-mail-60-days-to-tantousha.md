# REQ-011 — Reminder mail to 担当者 60 days before 契約終了日

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-interview-vendor-contracts.md` — A6, A9
- **Type (EARS):** complex (state-driven + event-driven)

## Requirement

While a contract is not in 解約, when the date is 60 days before its 契約終了日, the system shall send a mail to the 担当者 of the contract.

## Acceptance criteria

1. A contract in 有効 whose 契約終了日 is 60 days ahead: one reminder mail is addressed to its 担当者.
2. A contract in 解約 whose 契約終了日 is 60 days ahead: no mail.
3. A contract whose 契約終了日 is 61 or 59 days ahead: no mail on that day.
4. *(Contracts in 更新検討中 or 更新済 at the 60-day point: not answered (A9). `[assumed]` the mail is sent — the literal reading of A6 — question 6.)*
5. *(Not automatically testable: the delivery of the mail and the passing of days; a person checks the received mail on dev.)*

## Notes for P2

- **`[unverified]`** — the KB has mail notifications sent when a record changes (schema: `Notifications[]`) and tenant-level scheduled scripts (D31), but no entry on a reminder sent a set number of days before a date. Nobody has shown how Pleasanter 1.5.x does this; P2 must verify it before designing. Listed in `index.md` under "To verify in P2".
- Mail on dev: `environments.json` has `side_effects.mail: unknown`.
