# REQ-004 — Notify the サポート責任者 by mail on escalation

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md` (「責任者にはメールで知らせてほしい」)
- **Type (EARS):** event-driven

## Requirement

When a user executes the 「エスカレーション」 action on an inquiry, the 問い合わせ管理 site shall send a notification mail to the user set as that inquiry's サポート責任者.

## Acceptance criteria

1. The site configuration (getsite) contains exactly one mail notification tied to the escalation, addressed to the inquiry's サポート責任者, with subject and body as agreed in Q7 (assumed: subject 「【問い合わせ管理】優先度「高」の問い合わせがエスカレーションされました」; body contains 問い合わせ番号, 件名, 顧客名, 対応担当, エスカレーション日時 and the link to the record) [assumed, Q7].
2. Recipients are the サポート責任者 only (no copy to the 対応担当) [assumed, Q7].
3. Escalating one inquiry produces one escalation mail; the existing notification 「優先度「高」の問い合わせが未対応です」 is not additionally triggered (see REQ-005).
4. If the inquiry has no サポート責任者, the escalation is still executed and recorded, and no mail is sent [assumed, Q8].
5. *(Not automatically testable: actual mail delivery and content as received depend on the mail server. Verify on dev with a test mailbox, or by checking the mail log/queue; see Q7.)*
