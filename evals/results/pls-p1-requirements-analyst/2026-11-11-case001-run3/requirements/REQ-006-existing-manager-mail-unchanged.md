# REQ-006 — Existing status/priority mail to サポート責任者 unchanged (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-004 impact analysis: the site already mails the サポート責任者 (notification #1, subject 「優先度「高」の問い合わせが未対応です」) when 状況 or 優先度 of an inquiry in 未完了 changes. The new escalation mail overlaps with it (same recipient, same subject matter); a design that reuses or edits it would change when the existing mail is sent.
- **Type (EARS):** event-driven

## Requirement

When the 状況 or 優先度 of an inquiry that is in the 未完了 view changes, the system shall send the existing mail to the inquiry's サポート責任者 as it does today, whether or not the inquiry has been escalated.

## Acceptance criteria

1. The existing notification keeps its recipient (サポート責任者), monitored items (状況, 優先度), condition (未完了 view) and subject after the change (configuration comparison against the current `config/inquiries/site.json`).
2. Escalating an inquiry without changing 状況 or 優先度 does not send the existing mail (only the escalation mail of REQ-004). `[assumed]` — Q6, Q9.
3. *(Not automatically testable: delivery of the mail itself; checked by a person on dev.)*
