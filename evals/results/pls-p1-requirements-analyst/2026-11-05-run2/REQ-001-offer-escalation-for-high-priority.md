# REQ-001 — Offer one-click escalation for high-priority inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md` (「優先度が「高」の問い合わせは、対応担当がワンクリックでサポート責任者にエスカレーションできるようにしたい」)
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 優先度 is 「高」 and its 状況 is 受付, 対応中 or 顧客回答待ち [assumed, Q2] and it has not yet been escalated [assumed, Q3], the 問い合わせ管理 site shall offer a one-click 「エスカレーション」 [assumed label, Q11] action on the inquiry's edit screen.

## Acceptance criteria

1. Open an inquiry with 優先度 = 高, 状況 = 対応中, no エスカレーション日時: the edit screen shows the 「エスカレーション」 button.
2. Clicking the button once completes the escalation without any further input or confirmation dialog [assumed, Q9]; a success message is shown [assumed, Q9].
3. Repeat criterion 1 for 状況 = 受付 and 状況 = 顧客回答待ち: the button is shown.
4. Executing the escalation through the record update API (`ProcessId`) on such an inquiry returns success (HTTP 200).
5. The action is available to any user who can edit the inquiry; no additional restriction to the record's 対応担当 is applied [assumed, Q1].

## Notes

- "One click" is taken literally (Q9). Who may click is Q1; restricting it to the 対応担当 would rely on process access control, which is **not yet verified** in `pls-kb-pleasanter` (schema.md: `AccessControl` "not yet exercised") and would need a dev probe in P2.
- The unwanted counterpart (not 高 → refused) is REQ-002.
