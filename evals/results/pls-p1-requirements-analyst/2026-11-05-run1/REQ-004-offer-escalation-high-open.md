# REQ-004 — Offer escalation for open high-priority inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-05-high-priority-escalation.md`
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 優先度 is 「高」 and its 状況 is 受付, 対応中 or 顧客回答待ち, the 問い合わせ管理 site shall offer the 「エスカレーション」 action on the inquiry's edit screen.

## Acceptance criteria

1. For each of 受付 / 対応中 / 顧客回答待ち with 優先度 = 高: the 「エスカレーション」 button is shown on the edit screen (UI check) and API execution succeeds (HTTP 200).
2. The action is offered on the edit screen of a single inquiry only, not as a bulk action on the list `[assumed]`.

## Notes

- Allowed statuses are the `[assumed]` answer to Q3.
- Conditions are evaluated on the saved values: a user who changes 優先度 to 高 on screen must save before the button appears. This matches how process display conditions work through the API (D10); the on-screen behaviour before saving must be confirmed in P2.
