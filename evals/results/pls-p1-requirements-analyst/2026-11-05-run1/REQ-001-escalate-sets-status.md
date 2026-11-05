# REQ-001 — Escalation changes 状況 to エスカレーション済

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md`
- **Type (EARS):** event-driven

## Requirement

When a user executes 「エスカレーション」 on an inquiry, the 問い合わせ管理 site shall change the inquiry's 状況 to 「エスカレーション済」.

## Acceptance criteria

1. Record with 優先度 = 高, 状況 = 対応中, サポート責任者 set: executing the escalation action through the API (record update with the action's process) returns HTTP 200, and a subsequent `get` returns 状況 = エスカレーション済.
2. Same result when the starting 状況 is 受付 and when it is 顧客回答待ち.
3. After execution, 対応担当, サポート責任者, 優先度, 対応期限 and 問い合わせ内容 are unchanged (compare `get` before/after).
4. On the edit screen the action is a single button labelled 「エスカレーション」; one click executes it without further input and shows a completion message (UI check; no confirmation dialog per Q5 `[assumed]`).

## Notes

- New status 「エスカレーション済」 is an `[assumed]` answer to Q2; its label and position are customer-facing and must be confirmed. The internal status value is a P2 decision.
- Who may execute: Q1 `[assumed]` any user who can update the inquiry. Restricting it to the record's 対応担当 relies on process access control, which `pls-kb-pleasanter` lists as "not yet exercised" — P2 must probe it on dev before promising it.
- After escalation, users may still change 状況 manually to any other status (no new restriction) `[assumed]`; the 対応担当 is not changed (Q12 `[assumed]`).
