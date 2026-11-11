# REQ-006 — Existing サポート責任者 notification keeps working (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-004 impact analysis: notification #1 already mails `[Manager]` (サポート責任者) when 状況 or 優先度 changes on an inquiry in view 2 「未完了」 (subject 「【問い合わせ管理】優先度「高」の問い合わせが未対応です」). The new escalation mail goes to the same person; the change must not remove or alter this notification (overlap raised as Q11).
- **Type (EARS):** event-driven

## Requirement

When the 状況 or 優先度 of an inquiry that is in 受付, 対応中 or 顧客回答待ち after the save changes, the 問い合わせ site shall mail the inquiry's サポート責任者 as it does today, whether or not the inquiry is escalated.

## Acceptance criteria

1. The site settings after the change still hold notification #1 with the same address (`[Manager]`), monitored columns (状況, 優先度), condition (view 「未完了」), prefix and subject — compared with `config/inquiries/site.json` of 2026-11-11.
2. On an escalated inquiry in 対応中, changing 状況 to 顧客回答待ち triggers notification #1.
3. If the escalation itself changes 状況 (Q6), the サポート責任者 receives the escalation mail (REQ-004) and the notification #1 mail; whether that double mail is acceptable is Q11 (`[assumed]`: escalation does not change 状況, so only the escalation mail is sent).
4. *(Not automatically testable: mail delivery. Criterion 1 is checked on the configuration; criteria 2–3 by a person on dev with a test mailbox.)*
