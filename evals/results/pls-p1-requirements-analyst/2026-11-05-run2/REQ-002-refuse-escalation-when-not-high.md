# REQ-002 — Refuse escalation for inquiries that are not high priority

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md` (scope stated by the customer: only 優先度「高」 inquiries are escalated)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry's 優先度 is not 「高」 (中, 低 or empty), then the 問い合わせ管理 site shall refuse the 「エスカレーション」 action for that inquiry.

## Acceptance criteria

1. Open an inquiry with 優先度 = 中: the edit screen does not show the 「エスカレーション」 button. Same for 優先度 = 低 and 優先度 empty.
2. Executing the escalation through the record update API (`ProcessId`) on an inquiry with 優先度 = 中 returns HTTP 400 (`要求が不正です。`) and the record is unchanged (エスカレーション日時 stays empty, no mail is queued). *(Relies on KB fact D10: display condition enforced on API execution, verified on 1.5.2.)*
3. Same refusal applies, per the assumed defaults, when 状況 is 解決 or クローズ（対応不要） [assumed, Q2] and when the inquiry has already been escalated [assumed, Q3].
