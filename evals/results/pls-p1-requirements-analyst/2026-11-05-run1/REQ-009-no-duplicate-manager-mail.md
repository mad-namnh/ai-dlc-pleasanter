# REQ-009 — No duplicate mail to the サポート責任者 on escalation (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-003/REQ-007 impact analysis: existing notification 「優先度「高」の問い合わせが未対応です」 mails [サポート責任者] when 状況 or 優先度 changes and the record is in the 「未完了」 view; once 「未完了」 includes エスカレーション済, every escalation would trigger it too
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry is escalated, then the 問い合わせ管理 site shall not send the サポート責任者 the existing 「優先度「高」の問い合わせが未対応です」 mail for that status change.

## Acceptance criteria

1. `getsite`: the existing notification's condition / monitored items exclude the change to エスカレーション済 (configuration check).
2. The existing notification still fires for the cases it covers today (状況 or 優先度 changes within 受付/対応中/顧客回答待ち) — configuration check against the baseline.
3. *(Not automatically testable: that the サポート責任者 receives exactly one mail per escalation; verify manually on dev with a test mailbox.)*

## Notes

- `[assumed]` answer to Q8 (one mail per escalation). If the customer wants both mails, this requirement is withdrawn.
- Observation for Q9 (not changed by this request): the existing notification's subject says 優先度「高」, but its condition is the whole 「未完了」 view regardless of 優先度.
