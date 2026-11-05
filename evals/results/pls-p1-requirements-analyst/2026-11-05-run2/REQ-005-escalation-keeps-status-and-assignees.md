# REQ-005 — Escalation keeps status, priority and assignees unchanged (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001/REQ-003/REQ-004 impact analysis: the 未完了 view and the 状況×チャネル view filter/group by 状況; the site aggregation groups by 状況; the existing mail notification 「優先度「高」の問い合わせが未対応です」 (to サポート責任者) fires on changes of 状況 or 優先度 while the inquiry is in the 未完了 view; the 対応期限 reminder goes to the 対応担当. Changing any of these items during escalation would hide inquiries, shift counts, send a duplicate mail or redirect reminders.
- **Type (EARS):** event-driven

## Requirement

When a user executes the 「エスカレーション」 action on an inquiry, the 問い合わせ管理 site shall leave the inquiry's 状況, 優先度, 対応担当 and サポート責任者 unchanged [assumed, Q4].

## Acceptance criteria

1. Inquiry with 状況 = 対応中, 優先度 = 高, 対応担当 = U1, サポート責任者 = U2. After escalation (API), `get` returns the same 状況, 優先度, 対応担当 and サポート責任者.
2. The escalated inquiry is still listed in the 未完了 view (filter on 状況 受付/対応中/顧客回答待ち), checked via the API with that view's filter.
3. The 状況 aggregation and the 状況×チャネル view count the inquiry under the same 状況 as before escalation.
4. The existing notification 「優先度「高」の問い合わせが未対応です」 is not triggered by the escalation (no change to its monitored items 状況/優先度). *(Mail absence is not automatically testable; criterion 1 proves the precondition.)*
5. The escalated inquiry is still included in the 対応期限 reminder to its 対応担当 when its 対応期限 is within 3 days. *(Reminder delivery is not automatically testable; criterion 1 proves the precondition.)*

## Notes

- If Q4 is answered "yes, add a status such as エスカレーション済 / reassign to the 責任者", this requirement is replaced by status-impact requirements for the 未完了 view, the aggregation, the crosstab view, the existing notification condition and the AI script's status map.
