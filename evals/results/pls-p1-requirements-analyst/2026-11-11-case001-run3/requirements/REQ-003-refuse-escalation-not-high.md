# REQ-003 — No escalation when priority is not 高

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「優先度が「高」の問い合わせは」— read as a restriction to 高, `[assumed]` — Q4)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry's 優先度 is 中, 低 or empty, then the system shall refuse the エスカレーション action on that inquiry.

## Acceptance criteria

1. Inquiries with 優先度 = 中, 低 and empty (状況 = 対応中): the edit screen does not show the エスカレーション action.
2. Executing エスカレーション on such an inquiry through the API is refused; no escalation date-time is recorded and no mail is sent.
3. An inquiry escalated while 優先度 = 高 keeps its escalation date-time if 優先度 is later lowered. `[assumed]` — Q4.
