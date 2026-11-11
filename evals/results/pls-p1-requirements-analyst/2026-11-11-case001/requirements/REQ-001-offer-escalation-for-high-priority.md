# REQ-001 — Offer escalation on high-priority inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「優先度が「高」の問い合わせは、対応担当がワンクリックで…エスカレーションできるようにしたい。」)
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 優先度 is 高, the 問い合わせ site shall let the 対応担当 escalate the inquiry to the サポート責任者 with a single action on the inquiry.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 = 高, a user acting as 対応担当 sees one action labelled エスカレーション (label `[assumed]`, Q13) and can execute it with one click; no other input is needed (no confirmation dialog `[assumed]`, Q13).
2. Executing the action through the API on an inquiry with 優先度 = 高 succeeds (HTTP 200) and the escalation is recorded as REQ-003 states.
3. Who besides the record's 対応担当 may execute it follows Q3 (`[assumed]`: every user who may edit the inquiry; no restriction to the record's 対応担当).
4. Whether the action is offered on inquiries in 解決 / クローズ（対応不要） follows Q5 (`[assumed]`: offered only while 状況 is 受付, 対応中 or 顧客回答待ち).

## Notes for P2

- The single action is the customer's "ワンクリック". How it is built (process button, etc.) is P2's choice; KB D10/D21 apply to any process (display condition is a server-side guard; always give it a `View`).
- Restricting the action to *the record's own* 対応担当 (per-record, by the `Owner` value) is not covered by the KB: D20 covers process access control by group / user / dept ID lists only. If Q3 is answered "only the record's 対応担当", that point is `[unverified]` and P2 must verify it before designing.
- Edit-screen display of an action to read-only users: D19/D20.
