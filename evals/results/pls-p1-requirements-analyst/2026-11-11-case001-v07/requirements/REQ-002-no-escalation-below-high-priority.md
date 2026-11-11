# REQ-002 — No escalation for inquiries that are not high priority

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` — the request limits escalation to 「優先度が「高」の問い合わせ」; scope to be confirmed (Q5)
- **Type (EARS):** unwanted behaviour

## Requirement

If an inquiry's 優先度 is not 「高」 (中, 低 or empty), then the system shall not offer the エスカレーション action on that inquiry.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 中, 低 or empty, no エスカレーション button is shown.
2. Executing the エスカレーション action through the API on an inquiry with 優先度 中 is refused; the record (including エスカレーション日時) is unchanged and no escalation mail is sent.
3. Same as 2 for 優先度 低 and for 優先度 empty.
4. `[assumed]` (Q5) An inquiry escalated while 「高」 whose 優先度 is later lowered keeps its エスカレーション日時; it is not "un-escalated".
5. *(Criterion 1 is checked on the edit screen by a person on dev; "no mail sent" in 2 is not automatically testable.)*
