# REQ-006 — AI一次対応 keeps working on escalated inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001/REQ-003 impact analysis: the existing feature 「AI問い合わせ一次対応」 (`config/inquiries/server-scripts/ai1.js`, DES-000) runs on every save of an inquiry, acts when 「AIで一次対応する」 is checked, and holds its own list of 状況 labels (受付, 対応中, 顧客回答待ち, 解決, クローズ（対応不要）). The escalation is a new save path and may add data the feature does not know.
- **Type (EARS):** event-driven

## Requirement

When 「AIで一次対応する」 is executed on an escalated inquiry, the system shall write the AI results to the inquiry as it does for an inquiry that was not escalated.

## Acceptance criteria

1. On an escalated inquiry, saving with 「AIで一次対応する」 checked fills AI: 推定カテゴリ, AI: 推奨優先度 and AI: 回答の下書き, stamps AI実行記録 and unchecks 「AIで一次対応する」 — the same result as on an inquiry that was not escalated.
2. That save does not change the recorded escalation date-time (REQ-003) and sends no escalation mail (REQ-004).
3. Executing エスカレーション on an inquiry where 「AIで一次対応する」 is unchecked does not call the AI: AI実行記録 is unchanged.
4. *(Not automatically testable: the text sent to the AI is not observable through the API. If the design adds a 状況 for escalated inquiries (Q7), a reviewer checks that the label list of the feature contains it; otherwise the AI receives the bare status number.)*

## Notes for P2

- `ai1.js` says it is generated from a `spec.json`; that file is not in this repository. Where the label list is maintained is a point for P2.
- Whether executing エスカレーション while 「AIで一次対応する」 is checked must also run the AI (the save takes up to about 10 seconds, KB fact 8) is not asked by the customer; existing behaviour is "every save with the check on runs the AI" and this requirement does not change it.
