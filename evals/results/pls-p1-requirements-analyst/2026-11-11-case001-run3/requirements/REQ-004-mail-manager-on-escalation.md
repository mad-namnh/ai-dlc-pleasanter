# REQ-004 — Mail the サポート責任者 on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「責任者にはメールで知らせてほしい」)
- **Type (EARS):** event-driven

## Requirement

When an inquiry is escalated, the system shall send a mail to the user set as サポート責任者 on that inquiry.

## Acceptance criteria

1. Escalating an inquiry triggers exactly one escalation mail addressed to that inquiry's サポート責任者 (not to a fixed address, not to the 対応担当). `[assumed]` — Q1.
2. The mail contains at least 問い合わせ番号, 件名, 顧客名, 優先度, 対応担当 and the escalation date-time. `[assumed]` — Q8.
3. The escalation mail is distinguishable from the existing status/priority mail (different subject). `[assumed]` — Q9.
4. *(Not automatically testable: actual mail delivery and content cannot be checked through the API or the edit screen; the KB has no verified entry on mail delivery. A person checks the received mail on dev — see Q8. The configuration of the notification can be checked automatically.)*
