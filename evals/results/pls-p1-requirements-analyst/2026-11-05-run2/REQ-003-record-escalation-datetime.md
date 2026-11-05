# REQ-003 — Record the escalation date-time

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md` (「エスカレーションした日時を記録し」)
- **Type (EARS):** event-driven

## Requirement

When a user executes the 「エスカレーション」 action on an inquiry, the 問い合わせ管理 site shall record the current date and time in the inquiry's 「エスカレーション日時」 [assumed label, Q5] item.

## Acceptance criteria

1. Before: エスカレーション日時 is empty. Execute escalation (button or API) at time T. After: `get` returns エスカレーション日時 within T ± 1 minute, with date **and** time (minutes) precision.
2. The edit screen shows 「エスカレーション日時」 with the recorded value, formatted as date and time.
3. 「エスカレーション日時」 cannot be changed by hand on the edit screen [assumed, Q5].
4. The value is kept if 優先度 is later changed from 高 to another value [assumed, Q10].
5. 「エスカレーション日時」 is not added to the list (grid) or the filter panel [assumed, Q6].

## Notes

- New item → impact on grid, filters, editor layout and exports was checked; only the editor placement is required here. Grid/filter/export visibility is Q6.
