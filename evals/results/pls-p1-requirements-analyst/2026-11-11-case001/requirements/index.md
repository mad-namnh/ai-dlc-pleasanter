# Requirements — index

Site: 問い合わせ (`inquiries`). Change request of 2026-11-11: escalation of high-priority inquiries (`sources/2026-11-11-escalation-high-priority.md`).

## Requirements

| ID | Title | EARS type | Derived | Status |
|---|---|---|---|---|
| [REQ-001](REQ-001-offer-escalation-for-high-priority.md) | Offer escalation on high-priority inquiries | state-driven | — | awaiting G1 |
| [REQ-002](REQ-002-no-escalation-below-high.md) | No escalation for inquiries that are not high priority | unwanted behaviour | — | awaiting G1 |
| [REQ-003](REQ-003-record-escalation-date-time.md) | Record the escalation date-time | event-driven | — | awaiting G1 |
| [REQ-004](REQ-004-mail-to-support-manager.md) | Notify the サポート責任者 by mail on escalation | event-driven | — | awaiting G1 |
| [REQ-005](REQ-005-open-view-keeps-escalated.md) | 未完了 view still lists escalated open inquiries | state-driven | from REQ-001/003 (view 2 enumerates statuses) | awaiting G1 |
| [REQ-006](REQ-006-existing-notification-unchanged.md) | Existing サポート責任者 notification keeps working | event-driven | from REQ-004 (notification #1, same recipient) | awaiting G1 |
| [REQ-007](REQ-007-ai-first-response-unchanged.md) | AI first response keeps working on escalated inquiries | event-driven | from REQ-001/003 (script `ai1`, status map) | awaiting G1 |

## Impact on the current configuration (checked 2026-11-11, `config/inquiries/`)

| Element | Touched by the request? | Result |
|---|---|---|
| Column サポート責任者 (`Manager`) | yes — it is the escalation target | Overlap: no new "target" field; Q1, Q2 |
| Column 対応担当 (`Owner`) | yes — the person who escalates | Q3 (who may act), Q7 (does it change) |
| Column 優先度 (`ClassE`, 高/中/低) | yes — condition of the action | REQ-001, REQ-002, Q4, Q9 |
| Escalation date-time | yes — new data | No existing column holds it (受付日, 対応期限, 更新日時, AI実行記録 checked) → new element; REQ-003, Q12 |
| Status (100/200/300/900/910) | only if escalation changes it | Q6; REQ-005 protects view 2 |
| View 1 標準 | no filter on status | not affected; new column in grid → Q12 |
| View 2 未完了 (Status ∈ 100/200/300) | enumerates statuses | REQ-005 |
| View 3 状況×チャネル, Aggregation #1 (by 状況) | enumerate statuses implicitly | affected only if a status is added (Q6); noted in REQ-005 for P2 |
| Notification #1 (mail to サポート責任者 on 状況/優先度 change, condition view 2) | same recipient as the new mail | REQ-006, Q11 |
| Reminder #1 (対応期限 within 3 days → 対応担当) | no | not affected unless 対応担当 changes on escalation (Q7) |
| Server script `ai1` (BeforeCreate/BeforeUpdate, status label map) | runs on every save | REQ-007 |
| Shared script `aiEnv` | no | not affected |
| Permissions | who may escalate | no `permissions.json` in `config/`; Q3 |

## お客様への確認事項 (questions for the customer)

| No. | 確認事項 | 回答がない場合の前提 `[assumed]` | 関連 |
|---|---|---|---|
| Q1 | エスカレーション先は、各問い合わせの既存の「サポート責任者」欄に設定されている人でよいですか？（新しい「エスカレーション先」欄は作らない想定です） | 既存の「サポート責任者」欄の人に通知する。新しい欄は作らない。 | REQ-004 |
| Q2 | 「サポート責任者」欄が空の問い合わせでエスカレーションしようとした場合、どうしますか？ | エスカレーションを受け付けず、「サポート責任者を設定してください」と表示する。日時は記録しない。 | REQ-004 |
| Q3 | エスカレーションを実行できるのは、その問い合わせの「対応担当」本人だけですか？ほかの担当者やサポート責任者本人が実行してもよいですか？ | 問い合わせを編集できる人なら誰でも実行できる（対応担当本人に限定しない）。 | REQ-001 |
| Q4 | 優先度が「中」「低」または未設定の問い合わせはエスカレーションできない、という理解でよいですか？ | 「高」のみ可能。「中」「低」・未設定では実行できない。 | REQ-002 |
| Q5 | 「解決」「クローズ（対応不要）」の問い合わせでもエスカレーションできる必要がありますか？ | できない。「受付」「対応中」「顧客回答待ち」のときだけ実行できる。 | REQ-001 |
| Q6 | エスカレーションしたときに「状況」を変えますか？（例：「エスカレーション中」という新しい状況を追加する） | 変えない。状況はそのまま、日時の記録とメールのみ。 | REQ-003, REQ-005, REQ-006, REQ-007 |
| Q7 | エスカレーション後、「対応担当」はサポート責任者に変わりますか？ | 変わらない。対応担当はそのまま。 | REQ-003 |
| Q8 | 同じ問い合わせを2回以上エスカレーションできますか？その場合、記録する日時は最初の日時と最新の日時のどちらですか？ | 何度でもでき、記録は最新の日時で上書きする（その都度メールを送る）。 | REQ-003 |
| Q9 | エスカレーションの取り消しは必要ですか？また、エスカレーション後に優先度が「高」以外に変わった場合、記録した日時はどうしますか？ | 取り消し機能は不要。日時はそのまま残す。 | REQ-002 |
| Q10 | 責任者へのメールの件名・本文に載せたい内容を教えてください。 | 件名「【問い合わせ管理】エスカレーション: <問い合わせ番号> <件名>」、本文に問い合わせ番号・件名・顧客名・優先度・対応担当・エスカレーション日時・レコードへのリンク。 | REQ-004 |
| Q11 | 現在、問い合わせの「状況」または「優先度」が変わると、サポート責任者に通知メール（件名「優先度「高」の問い合わせが未対応です」）が届く設定になっています。エスカレーションのメールはこの通知とは別に送り、既存の通知はそのまま残してよいですか？ | 別のメールとして送る。既存の通知は変更しない。 | REQ-004, REQ-006 |
| Q12 | エスカレーション日時はどこで見られるようにしますか？（編集画面のみ／一覧にも表示／一覧で絞り込み）また、手で修正できる必要はありますか？ | 編集画面に「エスカレーション日時」として読み取り専用で表示する。一覧の列や絞り込みには追加しない。 | REQ-003 |
| Q13 | 「ワンクリック」について：実行前に確認メッセージ（「エスカレーションしますか？」）を出しますか？ボタンの表示名は「エスカレーション」でよいですか？一覧画面から直接実行する必要はありますか？ | 確認メッセージなし、表示名「エスカレーション」、問い合わせの編集画面から実行する。 | REQ-001 |

## Questions for the project owner (not for the customer)

| No. | Question | Assumption used in this run |
|---|---|---|
| O1 | The project profile says Origin `new`, yet the site runs on dev and stg, `config/` was unpacked from the stg rollback of release R-20261105-01 of another project folder (`ops/log/2026-11-11-namnh.jsonl`), and this project has no `requirements/`, `gates/` or onboarding summary. Is this our own app continued here (change request through P1), or a takeover that needs `pls-x-onboarding` / `pls-x-spec-recovery` first? | Our own app (managed in `environments.json`, slots in `design/slot-ledger.json` zone `madlab`, DES-000): P1 run as a change request. If it is a takeover, these requirements wait for the onboarding summary. |
| O2 | Who asked (name, role)? The source records only "the customer". | Unknown; recorded as such. |
| O3 | Observation, outside this request: notification #1's subject says 「優先度「高」の問い合わせが未対応です」, but its condition is view 2 (status only), so it fires for every priority. Intended? | Left as it is; REQ-006 protects the current behaviour. |

## Points P2 must verify before designing

- REQ-001: only if Q3 is answered "only the record's own 対応担当" — per-record restriction by the `Owner` value is not in the KB (D20 covers group / user / dept lists only) → `[unverified]`.
- REQ-004 / REQ-006: delivery of process and site notification mails has no KB probe; mail criteria are manual.
