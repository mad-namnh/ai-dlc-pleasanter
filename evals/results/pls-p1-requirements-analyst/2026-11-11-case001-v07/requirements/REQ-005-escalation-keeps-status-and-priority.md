# REQ-005 — Escalation keeps 状況 and 優先度 (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 / REQ-003 / REQ-004 impact analysis: the 未完了 view, the existing notification #1, the reminder #1, the aggregation by 状況, the 状況×チャネル view and the AI script all decide on 状況 (and the notification also on 優先度); see `index.md`, "Impact analysis". `(derived)` — `[assumed]` (Q2)
- **Type (EARS):** event-driven

## Requirement

When the 対応担当 escalates an inquiry, the system shall leave the inquiry's 状況 and 優先度 unchanged.

## Acceptance criteria

1. After the エスカレーション action is executed (API), 状況 and 優先度 read through the API equal their values before the action.
2. An escalated inquiry in 受付, 対応中 or 顧客回答待ち is still listed in the 未完了 view (API read with the view's filter).
3. An escalated inquiry is still counted under its 状況 in the 状況×チャネル view.
4. *(Not automatically testable: the escalation itself does not trigger the existing notification 「優先度「高」の問い合わせが未対応です」, and the 対応期限 reminder still reaches the 対応担当 for an escalated inquiry — checked by a person on dev with a test mailbox; the notification and reminder conditions are unverified, see index.md "Points P2 must verify".)*

## Note

If the answer to Q2 is that escalation changes 状況 (e.g. a new status such as エスカレーション済), this requirement is replaced by derived requirements for every element listed in `index.md`, "Impact analysis — if a status is added".
