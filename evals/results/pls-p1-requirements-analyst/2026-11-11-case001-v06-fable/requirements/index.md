# Requirements index

| ID | Title | Type | Derived from | Status |
|---|---|---|---|---|
| REQ-001 | Offer one-click escalation on high-priority inquiries | state-driven | — (`sources/2026-11-11-escalation-high-priority.md`) | awaiting G1 |
| REQ-002 | No escalation when the priority is not 「高」 | unwanted behaviour | — (same source) | awaiting G1 |
| REQ-003 | Record the date and time of the escalation | event-driven | — (same source) | awaiting G1 |
| REQ-004 | Mail to the サポート責任者 on escalation | event-driven | — (same source) | awaiting G1 |
| REQ-005 | An escalated inquiry stays in the view 未完了 | state-driven | REQ-001, REQ-003 (view 未完了 is the condition of notification #1 and reminder #1) | awaiting G1 |
| REQ-006 | AI一次対応 keeps working on escalated inquiries | event-driven | REQ-001, REQ-003 (server script `ai1` runs on every save and holds a 状況 label list) | awaiting G1 |

## Open questions for the customer (お客様への確認事項)

| # | Question (日本語) | Assumption |
|---|---|---|
| Q1 | エスカレーション先（メールの宛先）は、各問い合わせの既存項目「サポート責任者」に設定されている方でよいでしょうか。エスカレーション先を別の項目で指定する必要はありますか。 | `[assumed]` 既存の「サポート責任者」をエスカレーション先とし、新しい項目は追加しない。(REQ-004) |
| Q2 | エスカレーションを実行できるのは、その問い合わせの「対応担当」に設定されているご本人だけでしょうか。それとも、問い合わせを更新できるサポート担当者であれば誰でも実行できてよいでしょうか。 | `[assumed]` 問い合わせを更新できるサポート担当者であれば誰でも実行できる（本人かどうかの判定は追加しない）。(REQ-001) |
| Q3 | 「ワンクリック」は、編集画面の「エスカレーション」ボタンを1回押すだけで実行され、確認ダイアログや追加の入力（理由など）は不要、という理解でよいでしょうか。ボタン名は「エスカレーション」でよいでしょうか。 | `[assumed]` ボタン名は「エスカレーション」。確認ダイアログ・追加入力なしで即時に実行する。(REQ-001) |
| Q4 | 状況が「解決」「クローズ（対応不要）」の問い合わせでも、優先度が「高」であればエスカレーションできる必要がありますか。 | `[assumed]` エスカレーションできるのは「受付」「対応中」「顧客回答待ち」の問い合わせのみ。(REQ-001) |
| Q5 | 一度エスカレーションした問い合わせを、もう一度エスカレーションすることはありますか。ある場合、記録する日時は最初の日時と最新の日時のどちらでしょうか。 | `[assumed]` エスカレーションは1件につき1回のみ。実行後はボタンを表示せず、記録した日時は上書きしない。(REQ-001, REQ-003) |
| Q6 | エスカレーションした日時の項目名は「エスカレーション日時」（年月日・時分）でよいでしょうか。編集画面のほかに、一覧やフィルタにも表示しますか。また、手入力で修正できる必要はありますか。 | `[assumed]` 項目名は「エスカレーション日時」。編集画面にのみ表示し、画面からは修正できない。一覧・フィルタには追加しない。(REQ-003) |
| Q7 | エスカレーションしたとき、問い合わせの「状況」を変更しますか（例：新しい状況「エスカレーション済」を追加する）。 | `[assumed]` 「状況」は変更しない。エスカレーション済みかどうかは「エスカレーション日時」の有無で判断する。(REQ-003, REQ-005, REQ-006) |
| Q8 | 現在、未完了の問い合わせで「状況」または「優先度」が変更されると、サポート責任者に通知メール（件名「優先度「高」の問い合わせが未対応です」）が送られています。エスカレーション時のメールは、これとは別の専用メールとして1通送る、という理解でよいでしょうか。既存の通知はそのまま残してよいでしょうか。 | `[assumed]` エスカレーション専用のメールを1通送る。既存の通知は変更しない。1回のエスカレーションで責任者に届くメールは1通とする。(REQ-004) |
| Q9 | エスカレーションのメールの件名・本文に記載する内容をご指定ください（例：問い合わせ番号、件名、顧客名、対応期限、対応担当）。 | `[assumed]` 件名「【問い合わせ管理】エスカレーション：（問い合わせ番号）（件名）」。本文に問い合わせ番号・件名・顧客名・対応期限・対応担当を記載する。(REQ-004) |
| Q10 | 「サポート責任者」が未設定の問い合わせは、エスカレーションできないようにしますか。 | `[assumed]` 優先度「高」の問い合わせには「サポート責任者」が設定されている前提とし、未設定時のチェックは追加しない。(REQ-004) |

## Points P2 must verify before designing

The knowledge base (`pls-kb-pleasanter`) has no entry on these; no requirement promises them.

| Point | Affects |
|---|---|
| Whether the existing site notification #1 (watches 状況 and 優先度, condition = view 未完了) also sends a mail when an escalation saves the inquiry without changing those two fields — i.e. whether one escalation could produce two mails | REQ-004 criterion 3, Q8 |
| What a mail notice does when its recipient field (サポート責任者) is empty | REQ-004, Q10 |
| That a mail notice attached to an action is actually delivered on the dev environment (the KB knows the configuration shape, not the delivery) | REQ-004 criterion 5 |
| Whether an action can be limited to the user set as 対応担当 on the record (needed only if Q2 is answered "本人だけ") | REQ-001, Q2 |

## Notes for G1

- Nothing here is approved. All six requirements wait for the approver's decision at G1; the assumptions above apply only where the customer does not answer.
- Scope of the impact check: `config/inquiries/` (columns, statuses, views 1–3, notification #1, reminder #1, aggregation by 状況, server scripts `ai1` and `aiEnv`), `design/decisions/DES-000`, `design/slot-ledger.json`. `environments.json` also manages the site `responses` (対応履歴), but there is no `config/responses/` in the repository, so the impact on that site could not be checked. The request does not mention it.
- Not turned into requirements, because the customer did not ask for them and no existing element needs them: undoing an escalation, a view of escalated inquiries, an entry in 対応履歴, a refusal when サポート責任者 is empty (Q10).
