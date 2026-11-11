# REQ-001 — Offer one-click escalation on high-priority inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md`
- **Type (EARS):** state-driven

## Requirement

While the 優先度 of an inquiry is 「高」, the system shall offer the 対応担当 an エスカレーション action on that inquiry that is executed with one click.

## Acceptance criteria

1. On the edit screen of an inquiry with 優先度 = 「高」 and 状況 = 受付, 対応中 or 顧客回答待ち, a user of the support staff sees the エスカレーション action. `[assumed]` Q4 (open inquiries only), `[assumed]` Q2 (any support staff member who can update the inquiry, not only the person set as 対応担当).
2. One click on the action executes the escalation: no further input and no confirmation dialog. `[assumed]` Q3.
3. The same action can be executed through the API on such an inquiry and the call succeeds.
4. After an inquiry has been escalated, the action is not offered on it again. `[assumed]` Q5.

## Notes for P2

- The action name shown to users is 「エスカレーション」 `[assumed]` Q3.
- KB D19/D20: a user with read-only permission still sees an action button whose display condition matches, and is refused when pressing it. Whether the button must be hidden from such users depends on Q2.
- No existing element of `config/inquiries/site.json` offers such an action (the site has no action buttons today).
