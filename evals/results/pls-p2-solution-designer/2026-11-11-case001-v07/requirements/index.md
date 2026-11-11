# Requirements index

**G1 approved** by Nam (project owner), 2026-11-05 — scope: REQ-001…004 with assumptions Q1–Q4 as marked.

| ID | Title | Type | Status |
|---|---|---|---|
| REQ-001 | Escalate an inquiry | event-driven | G1 approved |
| REQ-002 | When escalation is available | state-driven + unwanted | G1 approved |
| REQ-003 | Notify the support manager | event-driven | G1 approved |
| REQ-004 | Escalated inquiries stay in the open list | ubiquitous (derived) | G1 approved |
| REQ-005 | Existing 「未対応です」 notification and escalated inquiries | unwanted (derived in P2, DES-001) | proposed — awaiting G1 |
| REQ-006 | AI first response shows the new status by its label | ubiquitous (derived in P2, DES-001) | proposed — awaiting G1 |

## Open questions for the customer (お客様への確認事項)

Assumptions are marked **[assumed]**; G1 confirms or changes them.

| # | Question (日本語) | Assumption |
|---|---|---|
| Q1 | エスカレーションを実行できるのは対応担当のみですか？編集権限のある全員でよいですか？ | [assumed] anyone with edit rights |
| Q2 | エスカレーション後に状況を「エスカレーション中」に変えてよいですか？（一覧・集計に新しい状況が増えます） | [assumed] yes — status 150 |
| Q3 | 一度エスカレーションした問い合わせを、再度エスカレーションする必要はありますか？ | [assumed] no |
| Q4 | 通知メールの宛先はサポート責任者のみでよいですか？メールの到達確認はどの環境で行いますか？ | [assumed] サポート責任者 only; delivery verified in stg by the customer |

### Raised in P2 (DES-001) — not yet answered

| # | Question (日本語) | Design assumption |
|---|---|---|
| Q5 | サポート責任者が未設定の問い合わせでも、エスカレーションできてよいですか？（その場合メールは誰にも届きません） | button shown regardless of サポート責任者 |
| Q6 | エスカレーション後に状況を手で「対応中」などに戻した場合、再度エスカレーションできてよいですか？（エスカレーション日時は上書きされます） | allowed (condition on 状況 only) |
| Q7 | 対応期限のリマインダー（担当者宛て）は、エスカレーション中の問い合わせにも送ってよいですか？ | yes (reminder follows 未完了) |
| Q8 | 既存の通知「優先度「高」の問い合わせが未対応です」は、エスカレーション中の問い合わせには送らない、でよいですか？（REQ-005） | option A: not sent |
| Q9 | REQ-001 は「対応担当が実行」、Q1 の前提は「編集権限のある全員」です。どちらが正しいですか？ | anyone with edit rights (Q1) |
