# REQ-007 — AI first response keeps working on escalated inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 / REQ-003 impact analysis: server script `ai1` (DES-000) runs on every create/update and holds its own label map of 状況 (100/200/300/900/910). An escalation saves the record, and a new status (Q6) or a new column would not be known to the script.
- **Type (EARS):** event-driven

## Requirement

When a user saves an escalated inquiry with AIで一次対応する turned on, the 問い合わせ site shall fill AI: 推定カテゴリ, AI: 推奨優先度, AI: 回答の下書き and AI実行記録 as it does for an inquiry that is not escalated.

## Acceptance criteria

1. Escalating an inquiry with AIで一次対応する off does not call the AI and does not change the AI fields or AI実行記録.
2. On an escalated inquiry, saving with AIで一次対応する on fills AI実行記録 and turns AIで一次対応する off again; the save succeeds (API HTTP 200).
3. *(Not automatically testable: whether the AI receives the 状況 as its Japanese label rather than a code — the prompt is not visible through the API. Check by reading the script in P2/P4 if a status is added.)*
4. *(AI output depends on the dev AI gateway; criterion 2 needs it reachable.)*
