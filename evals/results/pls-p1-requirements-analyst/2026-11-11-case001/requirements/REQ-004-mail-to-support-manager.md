# REQ-004 — Notify the サポート責任者 by mail on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「責任者にはメールで知らせてほしい。」)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 escalates an inquiry, the 問い合わせ site shall send a mail to the inquiry's サポート責任者.

## Acceptance criteria

1. The mail is addressed to the user set in the inquiry's existing サポート責任者 field (`[assumed]`, Q1) — no new "escalation target" field.
2. The mail names the inquiry so the サポート責任者 can open it: subject and body as in Q10 (`[assumed]`: subject 「【問い合わせ管理】エスカレーション: <問い合わせ番号> <件名>」; body with 問い合わせ番号, 件名, 顧客名, 優先度, 対応担当, エスカレーション日時 and a link to the record).
3. One escalation sends exactly one escalation mail; the existing notification (REQ-006) is not replaced by it (`[assumed]`, Q11).
4. If the サポート責任者 field is empty, the behaviour follows Q2 (`[assumed]`: the escalation is refused with a message asking to set the サポート責任者; nothing is recorded).
5. *(Not automatically testable: mail delivery and its content cannot be checked through the Pleasanter API. Verify by a person on dev with a test mailbox, or by the mail log of the dev environment.)*

## Notes for P2

- Pleasanter process notifications with `Address "[Manager]"` exist in the schema (KB `schema.md`, Processes → `Notifications[]`); their delivery has no probe entry in the KB.
