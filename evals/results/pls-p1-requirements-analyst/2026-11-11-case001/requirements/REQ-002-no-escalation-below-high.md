# REQ-002 — No escalation for inquiries that are not high priority

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (the request limits escalation to 「優先度が「高」の問い合わせ」; confirmed as an `[assumed]` reading in Q4)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry's 優先度 is 中, 低 or empty, then the 問い合わせ site shall refuse to escalate the inquiry.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 = 中, 低 or empty, the エスカレーション action is not shown.
2. Executing the escalation through the API on such an inquiry is refused (non-2xx); the escalation date-time stays unchanged and no escalation mail is sent.
3. When an inquiry's 優先度 is changed from 中 to 高 and saved, the action is offered (REQ-001) on the next display of the edit screen.
4. What happens to an existing escalation record when 優先度 is lowered after escalation follows Q9 (`[assumed]`: the recorded date-time is kept).

## Notes

- `[assumed]` (Q4): the request names only 高; offering escalation for 中/低 is read as out of scope. If the customer answers that 中/低 may also be escalated, this requirement is withdrawn at G1.
