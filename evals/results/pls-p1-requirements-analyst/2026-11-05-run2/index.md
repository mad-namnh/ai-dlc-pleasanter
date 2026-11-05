# Requirements index

## Requirements

| ID | Title | EARS type | Source | Status |
|---|---|---|---|---|
| [REQ-001](REQ-001-offer-escalation-for-high-priority.md) | Offer one-click escalation for high-priority inquiries | state-driven | [2026-11-05 escalation](sources/2026-11-05-high-priority-escalation.md) | awaiting G1 |
| [REQ-002](REQ-002-refuse-escalation-when-not-high.md) | Refuse escalation for inquiries that are not high priority | unwanted behaviour | [2026-11-05 escalation](sources/2026-11-05-high-priority-escalation.md) | awaiting G1 |
| [REQ-003](REQ-003-record-escalation-datetime.md) | Record the escalation date-time | event-driven | [2026-11-05 escalation](sources/2026-11-05-high-priority-escalation.md) | awaiting G1 |
| [REQ-004](REQ-004-notify-manager-by-mail.md) | Notify the サポート責任者 by mail on escalation | event-driven | [2026-11-05 escalation](sources/2026-11-05-high-priority-escalation.md) | awaiting G1 |
| [REQ-005](REQ-005-escalation-keeps-status-and-assignees.md) | Escalation keeps status, priority and assignees unchanged | event-driven (derived) | impact analysis of REQ-001/003/004 | awaiting G1 |
| [REQ-006](REQ-006-escalation-does-not-trigger-ai.md) | Escalation does not run the AI first response by itself | event-driven (derived) | impact analysis of REQ-001 (DES-000) | awaiting G1 |

## Impact analysis — site `inquiries` (2026-11-05 escalation request)

| Existing element | Touched? | Result |
|---|---|---|
| 状況 (受付/対応中/顧客回答待ち/解決/クローズ（対応不要）) | Only if a new status is wanted (Q4) | Assumed no change → REQ-005 |
| 優先度 (高/中/低) | Read as the condition | REQ-001, REQ-002 |
| 対応担当 / サポート責任者 | 責任者 is the mail recipient; neither changes (Q4) | REQ-004, REQ-005 |
| View 未完了 (filter 状況 100/200/300) | Would hide escalated inquiries if 状況 changed | REQ-005 |
| View 状況×チャネル, aggregation by 状況 | Counts by 状況 | REQ-005 |
| Notification 「優先度「高」の問い合わせが未対応です」 (to サポート責任者, monitors 状況/優先度, condition = 未完了 view) | Would send a duplicate mail if escalation changed 状況/優先度 | REQ-004 AC3, REQ-005 |
| Reminder 「対応期限が3日以内の問い合わせ」 (to 対応担当) | Must still reach the 対応担当 | REQ-005 |
| Server script `ai1` (BeforeCreate/BeforeUpdate) / `aiEnv` | Runs on the save made by escalation | REQ-006 |
| New item エスカレーション日時 | Editor; grid/filter/export visibility open | REQ-003, Q5, Q6 |
| Permissions | Who may escalate is open; process access control not verified in KB | Q1 |

Observation (not in scope, for information): the existing notification's subject says 「優先度「高」…」 but its condition is only the 未完了 view (no 優先度 filter). Not changed by this request; raise separately if relevant.

## お客様への確認事項 (open questions)

Unanswered questions are handled with the `[assumed]` default until G1.

| # | 確認事項 | [assumed] 回答がない場合の前提 | Affects |
|---|---|---|---|
| Q1 | エスカレーションを実行できるのは、その問い合わせの対応担当ご本人だけに限定しますか？それとも問い合わせを編集できる方なら誰でも実行できてよいですか？ | [assumed] 問い合わせを編集できる方なら誰でも実行できる（対応担当本人への限定はしない）。 | REQ-001 |
| Q2 | 「解決」「クローズ（対応不要）」の問い合わせでもエスカレーションできる必要はありますか？ | [assumed] 状況が「受付」「対応中」「顧客回答待ち」のときだけ実行できる。 | REQ-001, REQ-002 |
| Q3 | 同じ問い合わせを2回以上エスカレーションすることはありますか？ある場合、日時は最新で上書きしますか、それとも最初の日時を残しますか？ | [assumed] エスカレーションは1回のみ。実行済みの問い合わせではボタンを表示しない。 | REQ-001, REQ-002 |
| Q4 | エスカレーション時に、状況（例：新しい状況「エスカレーション済」）や対応担当を変更しますか？ | [assumed] 状況・優先度・対応担当・サポート責任者は変更しない。日時の記録とメール通知のみ。 | REQ-005 |
| Q5 | 記録する項目の名前は「エスカレーション日時」でよいですか？また、画面から手で修正できないようにしてよいですか？ | [assumed] 項目名「エスカレーション日時」、日付と時刻（分まで）、画面からは編集不可。 | REQ-003 |
| Q6 | 「エスカレーション日時」を一覧画面の列やフィルタ（絞り込み）、エクスポートにも表示しますか？ | [assumed] 編集画面にのみ表示し、一覧の列・フィルタには追加しない。 | REQ-003 |
| Q7 | 通知メールの件名・本文の内容と、宛先（サポート責任者のみか、対応担当にも写しを送るか）をご指定ください。 | [assumed] 宛先はサポート責任者のみ。件名「【問い合わせ管理】優先度「高」の問い合わせがエスカレーションされました」、本文に問い合わせ番号・件名・顧客名・対応担当・エスカレーション日時・問い合わせへのリンクを記載。 | REQ-004 |
| Q8 | サポート責任者が未設定の問い合わせでエスカレーションした場合、どうしますか？（実行を止める／実行してメールは送らない） | [assumed] エスカレーションは実行して日時を記録し、メールは送信しない（新たな入力チェックは追加しない）。 | REQ-004 |
| Q9 | 「ワンクリック」は、確認ダイアログなしでボタンを押した時点で実行される、という意味でよいですか？ | [assumed] 確認ダイアログなし。実行後に完了メッセージを表示する。 | REQ-001 |
| Q10 | エスカレーション後に優先度が「高」以外に変更された場合、記録した日時はそのまま残しますか？ | [assumed] 残す（消去しない）。 | REQ-003 |
| Q11 | ボタンの名前は「エスカレーション」でよいですか？ | [assumed] 「エスカレーション」。 | REQ-001 |

## G1 hand-over

- Self-check done: one `shall` per requirement; every requirement has acceptance criteria (mail delivery/absence and reminder delivery flagged as not automatically testable); impact on statuses, views, notifications, reminder, scripts and permissions checked; derived requirements (REQ-005, REQ-006) only protect existing behaviour; extra behaviour (repeat limit, closed-status limit, read-only item, missing 責任者 handling, grid visibility) is raised as questions; every `[assumed]` points to a question above.
- KB gap for P2: restricting the action to the 対応担当 (Q1) would rely on process `AccessControl`, not yet verified in `pls-kb-pleasanter` — probe on dev before designing it.
- Nothing is approved; awaiting G1 decision by the project owner.
