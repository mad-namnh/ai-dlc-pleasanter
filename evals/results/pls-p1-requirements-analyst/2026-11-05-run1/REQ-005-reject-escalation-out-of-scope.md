# REQ-005 — No escalation outside high-priority open inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md` (the request limits escalation to 優先度「高」; repeat/closed cases derived from Q3, Q4)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry's 優先度 is not 「高」, or its 状況 is エスカレーション済, 解決 or クローズ（対応不要）, then the 問い合わせ管理 site shall refuse the 「エスカレーション」 action.

## Acceptance criteria

1. 優先度 = 中, 低 and empty (with 状況 = 対応中): the button is not shown, and API execution returns HTTP 400 (`要求が不正です。`).
2. 優先度 = 高 with 状況 = エスカレーション済, 解決, クローズ（対応不要）: the button is not shown, and API execution returns HTTP 400.
3. In every refused case the record is unchanged (状況, エスカレーション日時) and no escalation mail is configured to fire (the mail belongs to the refused action).

## Notes

- Negative API tests rely on D10 (display condition enforced on API execution, verified on 1.5.2).
- If 優先度 is lowered after escalation, the inquiry stays エスカレーション済 and keeps its エスカレーション日時 `[assumed]` (Q11).
