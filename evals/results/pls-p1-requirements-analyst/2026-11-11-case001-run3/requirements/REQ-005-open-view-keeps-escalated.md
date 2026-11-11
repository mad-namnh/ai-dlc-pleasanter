# REQ-005 — 未完了 view still lists escalated inquiries (derived)

- **Status:** awaiting G1
- **Source:** derived from REQ-001 / REQ-002 impact analysis: the existing view 未完了 lists inquiries by 状況 (受付, 対応中, 顧客回答待ち). If escalation changes or adds a 状況 (Q6), an escalated inquiry that is still open would drop out of the view the support team uses daily, and out of the condition of the existing mail to サポート責任者 (notification #1 uses this view).
- **Type (EARS):** ubiquitous

## Requirement

The 未完了 view shall list every inquiry that is not 解決 or クローズ（対応不要）, including escalated inquiries.

## Acceptance criteria

1. An inquiry escalated while 状況 = 対応中 appears in the 未完了 view after the escalation.
2. After it is set to 解決 or クローズ（対応不要）, it no longer appears in the 未完了 view.
3. If G1 adds a new 状況 for escalation (Q6), an inquiry in that 状況 appears in 未完了, and the 状況×チャネル view and the 状況 aggregation show it as its own row.
