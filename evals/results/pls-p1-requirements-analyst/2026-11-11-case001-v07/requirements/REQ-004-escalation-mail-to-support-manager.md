# REQ-004 — Mail to the サポート責任者 on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「責任者にはメールで知らせてほしい。」)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 escalates an inquiry, the system shall send a mail about the escalation to the サポート責任者 set on that inquiry `[assumed]` (Q6).

## Acceptance criteria

1. The configuration sends a mail on the エスカレーション action, addressed to the inquiry's サポート責任者 (checked by configuration review and lint).
2. The mail contains at least 問い合わせ番号, 件名, 顧客名, 対応担当 and エスカレーション日時 `[assumed]` (Q8).
3. *(Not automatically testable: mail delivery and its content are checked by a person on dev with a test mailbox after executing the action.)*
4. `[assumed]` (Q7) This mail is separate from the existing notification 「優先度「高」の問い合わせが未対応です」; that notification keeps its current recipients, subject and condition.
5. *(Behaviour when the inquiry has no サポート責任者 is open — Q6; no criterion until answered.)*
