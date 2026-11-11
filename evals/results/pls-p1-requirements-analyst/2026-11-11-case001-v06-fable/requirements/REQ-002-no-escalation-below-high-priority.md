# REQ-002 — No escalation when the priority is not 「高」

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (the request limits escalation to 優先度「高」)
- **Type (EARS):** unwanted behaviour

## Requirement

If the 優先度 of an inquiry is not 「高」, then the system shall not offer the エスカレーション action on that inquiry.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 = 「中」, 「低」 or empty, the エスカレーション action is not shown.
2. Executing the action through the API on such an inquiry is refused (HTTP 400, KB D10) and the inquiry is unchanged: no escalation date-time recorded.
3. When the 優先度 of an inquiry is changed from 「高」 to another value before escalation, the action is no longer shown after the save.

## Notes for P2

- An inquiry whose 優先度 is lowered **after** it was escalated keeps its recorded escalation date-time (the request does not ask to undo an escalation).
