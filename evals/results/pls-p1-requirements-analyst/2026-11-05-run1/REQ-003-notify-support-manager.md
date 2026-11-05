# REQ-003 — Mail the サポート責任者 on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md`
- **Type (EARS):** event-driven

## Requirement

When a user executes 「エスカレーション」 on an inquiry, the 問い合わせ管理 site shall send a mail to the サポート責任者 set on that inquiry.

## Acceptance criteria

1. Configuration check (`getsite`): the escalation action carries a mail notification addressed to the inquiry's サポート責任者, and to no one else (Q6 `[assumed]`).
2. Configuration check: subject is 「【問い合わせ管理】エスカレーション: <問い合わせ番号> <件名>」 and the body contains 問い合わせ番号, 件名, 顧客名, 優先度, 対応期限, 対応担当, エスカレーション日時 and a link to the inquiry (Q6 `[assumed]`).
3. A normal save without escalation does not send the escalation mail (configuration check: the mail is attached to the escalation action only).
4. *(Not automatically testable: actual mail delivery and rendering in the recipient's mailbox. Verify manually on dev with a test mailbox; see Q6.)*

## Notes

- Exactly one mail per escalation — see REQ-009 for the interaction with the existing notification.
