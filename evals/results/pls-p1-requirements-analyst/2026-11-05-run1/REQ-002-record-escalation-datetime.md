# REQ-002 — Record the escalation date-time

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md`
- **Type (EARS):** event-driven

## Requirement

When a user executes 「エスカレーション」 on an inquiry, the 問い合わせ管理 site shall record the current date and time in the inquiry's 「エスカレーション日時」.

## Acceptance criteria

1. After executing the action through the API, `get` returns エスカレーション日時 equal to the execution time (date and time to the minute, tolerance ±1 minute, server time zone).
2. A normal save of an inquiry (no escalation) leaves エスカレーション日時 empty / unchanged.
3. If the same inquiry is escalated again later (possible only after its 状況 was changed away from エスカレーション済, see REQ-005 and Q4), エスカレーション日時 holds the latest execution time `[assumed]`.
4. A rejected escalation (REQ-005, REQ-006) does not change エスカレーション日時.

## Notes

- 「エスカレーション日時」 is a new item; label `[assumed]` (Q13). Display/read-only behaviour is REQ-011.
