# Requirements index

## Requirements

| ID | Title | EARS type | Site | Source | Status |
|---|---|---|---|---|---|
| [REQ-001](REQ-001-escalate-sets-status.md) | Escalation changes 状況 to エスカレーション済 | event-driven | inquiries | 2026-11-05 escalation request | awaiting G1 |
| [REQ-002](REQ-002-record-escalation-datetime.md) | Record the escalation date-time | event-driven | inquiries | 2026-11-05 escalation request | awaiting G1 |
| [REQ-003](REQ-003-notify-support-manager.md) | Mail the サポート責任者 on escalation | event-driven | inquiries | 2026-11-05 escalation request | awaiting G1 |
| [REQ-004](REQ-004-offer-escalation-high-open.md) | Offer escalation for open high-priority inquiries | state-driven | inquiries | 2026-11-05 escalation request | awaiting G1 |
| [REQ-005](REQ-005-reject-escalation-out-of-scope.md) | No escalation outside high-priority open inquiries | unwanted behaviour | inquiries | 2026-11-05 escalation request | awaiting G1 |
| [REQ-006](REQ-006-require-support-manager.md) | Escalation requires a サポート責任者 (derived) | unwanted behaviour | inquiries | derived from REQ-003 | awaiting G1 |
| [REQ-007](REQ-007-open-view-includes-escalated.md) | 「未完了」 view keeps escalated inquiries (derived) | state-driven | inquiries | derived from REQ-001 | awaiting G1 |
| [REQ-008](REQ-008-deadline-reminder-includes-escalated.md) | 対応期限 reminder still covers escalated inquiries (derived) | state-driven | inquiries | derived from REQ-001 | awaiting G1 |
| [REQ-009](REQ-009-no-duplicate-manager-mail.md) | No duplicate mail to the サポート責任者 on escalation (derived) | unwanted behaviour | inquiries | derived from REQ-003/007 | awaiting G1 |
| [REQ-010](REQ-010-ai-reads-escalated-status.md) | AI一次対応 sees the escalated status by name (derived) | event-driven | inquiries | derived from REQ-001 | awaiting G1 |
| [REQ-011](REQ-011-show-escalation-datetime.md) | エスカレーション日時 is visible and read-only (derived) | ubiquitous | inquiries | derived from REQ-002 | awaiting G1 |
| [REQ-012](REQ-012-crosstab-counts-escalated.md) | Status aggregations count エスカレーション済 (derived) | ubiquitous | inquiries | derived from REQ-001 | awaiting G1 |

Source: [`sources/2026-11-05-high-priority-escalation.md`](sources/2026-11-05-high-priority-escalation.md) (customer support team lead, mail, 2026-11-05).

## Impact analysis — site `inquiries` (current configuration)

| Element | Current state | Impact | Recorded as |
|---|---|---|---|
| 状況 choices | 受付 / 対応中 / 顧客回答待ち / 解決 / クローズ（対応不要） | New status エスカレーション済 `[assumed]` (Q2) | REQ-001 |
| 優先度, 対応担当, サポート責任者 | 優先度 高/中/低 (optional); サポート責任者 optional | Escalation condition and mail recipient; empty サポート責任者 case | REQ-004, REQ-005, REQ-006 |
| New item エスカレーション日時 | — | Edit screen, list, filters, export | REQ-002, REQ-011 |
| View 「未完了」 | 状況 ∈ 受付/対応中/顧客回答待ち | Would hide escalated inquiries | REQ-007 |
| View 「状況×チャネル」, 状況 aggregation | Group by 状況 | New row | REQ-012 |
| View 「標準」 | No status filter | None | — |
| Notification 「優先度「高」の問い合わせが未対応です」 | To サポート責任者; watches 状況, 優先度; condition 「未完了」 | Duplicate mail on escalation | REQ-009, Q8, Q9 |
| Reminder 「対応期限が3日以内の問い合わせ」 | To 対応担当; condition 2 (apparently 「未完了」, unverified) | Escalated inquiries must stay covered | REQ-008 |
| Script 「AI問い合わせ一次対応」 (ai1) | Lists status names in its own table | New status would appear as a code | REQ-010 |
| Script 「共通設定（環境）」 (aiEnv) | Gateway URL only | None | — |
| Permissions | Not in the unpacked config | Who may escalate (Q1); restriction to 対応担当 unverified | REQ-001 note |
| 対応回数, 「AIで一次対応する」, 添付資料 | — | None | — |

## Items to verify in P2 (not in `pls-kb-pleasanter`)

- Restricting a process to the record's 対応担当 (process access control "not yet exercised") — REQ-001 / Q1.
- Refusing a process when a user column (サポート責任者) is empty — REQ-006.
- Meaning of the reminder's `Condition: 2` (view Id?) — REQ-008.
- On-screen display of a process button before unsaved changes are saved — REQ-004.

## お客様への確認事項 (open questions)

Customer and project owner were not available on 2026-11-05. Until answered, the `[assumed]` answer is used and is subject to G1.

| No. | 確認事項 | 回答がない場合の前提 | Affects | Status |
|---|---|---|---|---|
| Q1 | エスカレーションを実行できるのは、その問い合わせの「対応担当」本人だけに限定しますか？それとも問い合わせを更新できる方なら誰でも実行できてよいですか？ | `[assumed]` 問い合わせを更新できる方なら誰でも実行可能とします。対応担当本人への限定は、Pleasanter での実現可否を検証のうえ改めてご相談します。 | REQ-001 | open |
| Q2 | エスカレーションしたとき、「状況」を新しい状況「エスカレーション済」に変更してよいですか？（名称・並び順のご希望があればお知らせください） | `[assumed]` 新しい状況「エスカレーション済」を追加し、「対応中」と「顧客回答待ち」の間に置きます。 | REQ-001, 007, 008, 010, 012 | open |
| Q3 | エスカレーションできる状況はどれですか？ | `[assumed]` 「受付」「対応中」「顧客回答待ち」のときのみ可能。「解決」「クローズ（対応不要）」では不可。 | REQ-004, 005 | open |
| Q4 | 同じ問い合わせを複数回エスカレーションすることはありますか？ | `[assumed]` 「エスカレーション済」の間は再実行不可。状況を別の状況に戻した後は再度可能で、エスカレーション日時は最新の日時で上書きします。 | REQ-002, 005 | open |
| Q5 | 「ワンクリック」とは、確認メッセージ（「エスカレーションしますか？」）なしで即時実行する意味でよいですか？ | `[assumed]` 確認メッセージは表示せず、ボタン1回で実行し、完了メッセージを表示します。 | REQ-001 | open |
| Q6 | 通知メールの宛先・件名・本文のご希望はありますか？（対応担当本人や他の方への CC は必要ですか？） | `[assumed]` 宛先はその問い合わせの「サポート責任者」のみ。件名「【問い合わせ管理】エスカレーション: 問い合わせ番号 件名」、本文に問い合わせ番号・件名・顧客名・優先度・対応期限・対応担当・エスカレーション日時・問い合わせへのリンクを記載します。 | REQ-003 | open |
| Q7 | 「サポート責任者」が未設定の問い合わせでエスカレーションしようとした場合、どうしますか？ | `[assumed]` エスカレーションは行わず、「サポート責任者を設定してからエスカレーションしてください。」と表示します。 | REQ-006 | open |
| Q8 | 現在、状況が変わると既存の通知「優先度「高」の問い合わせが未対応です」がサポート責任者に送られます。エスカレーション時にこの通知も届くとメールが2通になりますが、どちらか1通でよいですか？ | `[assumed]` エスカレーション時はエスカレーション通知の1通のみとし、既存通知は送りません。 | REQ-009 | open |
| Q9 | 既存の通知「優先度「高」の問い合わせが未対応です」は、現在は優先度に関係なく未完了の問い合わせすべてで送られる設定です。意図どおりでしょうか？（今回の依頼の範囲外のため、回答があるまで変更しません） | `[assumed]` 現状のまま変更しません。 | REQ-009 (observation) | open |
| Q10 | エスカレーション時に理由やコメントの入力は必要ですか？ | `[assumed]` 不要です（ワンクリックのため）。 | REQ-001 | open |
| Q11 | エスカレーション後に優先度が「中」「低」に変更された場合、エスカレーションを取り消しますか？ | `[assumed]` 取り消しません。状況「エスカレーション済」とエスカレーション日時はそのまま残します。 | REQ-005 | open |
| Q12 | エスカレーション時に「対応担当」をサポート責任者に変更しますか？ | `[assumed]` 変更しません。対応担当はそのままで、対応期限のリマインダーも引き続き対応担当に届きます。 | REQ-001, 008 | open |
| Q13 | 「エスカレーション日時」を一覧の列・絞り込み条件・CSV出力にも含めますか？（項目名のご希望があればお知らせください） | `[assumed]` 項目名「エスカレーション日時」とし、編集画面（読み取り専用）・一覧の列・絞り込み・CSV出力に含めます。 | REQ-011 | open |

## Gate

All requirements above are **awaiting G1**. Nothing has been approved by MADLAB P1 (I4).
