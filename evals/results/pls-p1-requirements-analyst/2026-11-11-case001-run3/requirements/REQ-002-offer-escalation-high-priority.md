# REQ-002 — Offer escalation on open high-priority inquiries

- **Status:** awaiting G1
- **Source:** `sources/2026-11-11-escalation-high-priority.md` (「優先度が「高」の問い合わせは、対応担当がワンクリックで…エスカレーションできるようにしたい」); the 状況 restriction is `[assumed]` — Q3, "not yet escalated" is `[assumed]` — Q5
- **Type (EARS):** state-driven

## Requirement

While an inquiry's 優先度 is 高, its 状況 is 受付, 対応中 or 顧客回答待ち, and it has not been escalated yet, the system shall offer the エスカレーション action as a single click on the inquiry's edit screen.

## Acceptance criteria

1. An inquiry with 優先度 = 高, 状況 = 受付 (and again with 対応中, 顧客回答待ち), not yet escalated: the edit screen shows the エスカレーション action, and executing it through the API succeeds.
2. An inquiry with 優先度 = 高 and 状況 = 解決 or クローズ（対応不要）: the action is not shown, and executing it through the API is refused (no escalation date-time recorded). `[assumed]` — Q3.
3. An inquiry that has already been escalated: the action is not shown, and executing it again through the API is refused; the first escalation date-time is kept. `[assumed]` — Q5.
4. An inquiry with 優先度 = 高 whose サポート責任者 is empty: behaviour per Q11. `[assumed]` the action is not offered.
5. *(Who sees the action — only the record's 対応担当 or every support user — depends on Q2; no criterion is written for it until Q2 is answered.)*
