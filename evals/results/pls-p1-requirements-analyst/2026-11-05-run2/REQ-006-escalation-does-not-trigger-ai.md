# REQ-006 — Escalation does not run the AI first response by itself (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 impact analysis: the existing AI first-response feature (「AIで一次対応する」, DES-000) runs on every save of an inquiry and acts only when 「AIで一次対応する」 is checked. Escalation saves the inquiry, so it must not change this rule.
- **Type (EARS):** event-driven

## Requirement

When a user executes the 「エスカレーション」 action on an inquiry whose 「AIで一次対応する」 is not checked, the 問い合わせ管理 site shall leave the AI items (AI: 推定カテゴリ, AI: 推奨優先度, AI: 回答の下書き, AI実行記録) unchanged.

## Acceptance criteria

1. Inquiry with 「AIで一次対応する」 off and known values in the four AI items. Execute escalation via the API. `get` returns identical values for the four AI items, and no AI gateway call is logged for that record.
2. The escalation succeeds (HTTP 200) with no `ServerScriptExecutionFailed` error.
