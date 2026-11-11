# Requirements index

Site: 問い合わせ (`config/inquiries/`). Earlier requirement documents of this app were not carried into this folder; IDs start at REQ-001.

## Requirements

| ID | Title | EARS type | Source | Status |
|---|---|---|---|---|
| REQ-001 | Record the escalation date-time | event-driven | `sources/2026-11-11-escalation-high-priority.md` | awaiting G1 |
| REQ-002 | Offer escalation on open high-priority inquiries | state-driven | `sources/2026-11-11-escalation-high-priority.md` | awaiting G1 |
| REQ-003 | No escalation when priority is not 高 | unwanted behaviour | `sources/2026-11-11-escalation-high-priority.md` | awaiting G1 |
| REQ-004 | Mail the サポート責任者 on escalation | event-driven | `sources/2026-11-11-escalation-high-priority.md` | awaiting G1 |
| REQ-005 | 未完了 view still lists escalated inquiries (derived) | ubiquitous | derived from REQ-001/002 | awaiting G1 |
| REQ-006 | Existing status/priority mail to サポート責任者 unchanged (derived) | event-driven | derived from REQ-004 | awaiting G1 |

## Impact on the current configuration (step 2 / step 4)

| Existing element | Touched by the request? | Outcome |
|---|---|---|
| Column サポート責任者 (Manager) | Yes — it already holds the person to escalate to | Used as the escalation target; overlap raised as Q1 |
| Column 対応担当 (Owner) | Yes — the actor | Who may escalate: Q2; whether escalation reassigns it: Q7 |
| Column 優先度 (高/中/低) | Yes — the condition | REQ-002, REQ-003 |
| A place for the escalation date-time | No existing column holds it (受付日, 対応期限, 更新日時, AI実行記録 all mean something else) | New element needed (REQ-001); grid/filter/edit layout: Q12 |
| Status choices 100/200/300/900/910 | Only if escalation changes 状況 (Q6) | REQ-005 protects the 未完了 view; if a new 状況 is chosen, P1 is re-run for its impact (see below) |
| View 2 未完了 (Status ∈ 100/200/300) | Indirectly | REQ-005 |
| View 3 状況×チャネル, aggregation by 状況 | Only if a new 状況 (Q6) | REQ-005 criterion 3 |
| Notification #1 (mail to [Manager] on 状況/優先度 change, condition view 2) | Overlaps with the requested mail | REQ-006 keeps it; relation to the new mail: Q9; existing subject vs. actual condition: Q10 |
| Reminder #1 (対応期限 within 3 days → mail to 対応担当) | Only if escalation reassigns 対応担当 (Q7) | Under the Q7 assumption it is unaffected; no requirement |
| Server script ai1 (AI first response; 状況 label map 100/200/300/900/910) | Runs on every save (BeforeCreate/BeforeUpdate) but acts only when AIで一次対応する is on; its 状況 map is affected only by a new 状況 (Q6) | No requirement under the Q6 assumption; if a new 状況 is chosen, ai1's label map must include it (derived requirement to add then) |
| Permissions | Who may escalate (Q2). KB D19: read-only users still see action buttons whose condition matches, but are refused | Addressed in P2 after Q2 |

If G1 answers Q6 with "a new 状況", re-run P1 impact for that status: view 2, view 3, the 状況 aggregation, notification #1's condition and the 状況 label map in ai1 all enumerate statuses (KB behaviours, "Adding a new status").

## お客様への確認事項 (open questions)

| # | 質問 | [assumed] 回答がない場合の前提 | 関係する要件 |
|---|---|---|---|
| Q1 | エスカレーション先の「サポート責任者」は、各問い合わせに既に入力されている「サポート責任者」欄の方でよいですか？（新しい欄は作らない想定です） | `[assumed]` はい。既存の「サポート責任者」欄の方へエスカレーション・メール送信する。 | REQ-001, REQ-004 |
| Q2 | エスカレーションできるのは、その問い合わせの「対応担当」に設定されている本人だけですか？それとも問い合わせを編集できるサポート担当者なら誰でもよいですか？ | `[assumed]` 問い合わせを編集できるサポート担当者なら誰でもエスカレーションできる。 | REQ-001, REQ-002 |
| Q3 | 「解決」「クローズ（対応不要）」の問い合わせもエスカレーションできる必要はありますか？ | `[assumed]` いいえ。「受付」「対応中」「顧客回答待ち」のときだけエスカレーションできる。 | REQ-002 |
| Q4 | 優先度が「中」「低」（または未設定）の問い合わせは、エスカレーションできないようにしてよいですか？また、エスカレーション後に優先度が下げられた場合、記録した日時はそのまま残してよいですか？ | `[assumed]` はい、「高」のときだけ可能。日時はそのまま残す。 | REQ-003 |
| Q5 | 同じ問い合わせを2回以上エスカレーションすることはありますか？ある場合、記録する日時は最初と最新のどちらですか？ | `[assumed]` 1回のみ。エスカレーション後はボタンを表示せず、最初の日時を残す。 | REQ-001, REQ-002 |
| Q6 | エスカレーションしたとき、問い合わせの「状況」を変更しますか？（例：「エスカレーション済」のような状況を追加する） | `[assumed]` 変更しない。状況はそのまま、エスカレーション日時だけ記録する。 | REQ-001, REQ-005, REQ-006 |
| Q7 | エスカレーション後、「対応担当」をサポート責任者に変更しますか？それとも対応担当はそのまま対応を続けますか？ | `[assumed]` 変更しない（対応期限のリマインダーも引き続き対応担当に届く）。 | REQ-001 |
| Q8 | 責任者へのメールの件名と本文に含めたい項目を教えてください。 | `[assumed]` 件名「【問い合わせ管理】エスカレーション：[問い合わせ番号] [件名]」、本文に問い合わせ番号・件名・顧客名・優先度・対応担当・エスカレーション日時を記載する。メールの実際の受信は、開発環境で担当者が目視確認する。 | REQ-004 |
| Q9 | 現在も、未完了の問い合わせの「状況」または「優先度」が変わるとサポート責任者にメールが送られています。エスカレーションのメールはこれとは別に送る形でよいですか？ | `[assumed]` はい。既存のメールはそのまま残し、エスカレーション用のメールを別の件名で送る。 | REQ-004, REQ-006 |
| Q10 | 既存のメールは件名が「優先度「高」の問い合わせが未対応です」ですが、実際には優先度に関係なく（未完了の問い合わせの状況・優先度が変わると）送られています。現状のままでよいですか？ | `[assumed]` 現状のまま（今回の変更範囲外）。 | REQ-006 |
| Q11 | 「サポート責任者」が未入力の問い合わせで、エスカレーションしようとした場合はどうしますか？ | `[assumed]` エスカレーションボタンを表示しない（サポート責任者を入力してから実行する）。 | REQ-002 |
| Q12 | 「エスカレーション日時」は一覧画面にも表示・絞り込みが必要ですか？また、手で修正できる必要はありますか？ | `[assumed]` 編集画面と一覧に表示し、絞り込みにも追加する。手での修正は不可（読み取り専用）。 | REQ-001 |
| Q13 | エスカレーションを取り消す操作は必要ですか？ | `[assumed]` 不要。 | REQ-002 |

## Points P2 must verify before designing

| Point | Why | Requirements |
|---|---|---|
| Mail delivery from the escalation action to the user in サポート責任者 | The KB has a schema entry for process notifications (`Address "[Manager]"`), but no verified entry on delivery; delivery is not testable through the API | REQ-004, REQ-006 |
| Restricting an action to the user set in a record's 対応担当 (only if Q2 is answered 「本人のみ」) | KB D20 covers process access control by group/user/dept lists only; it says nothing about "the user in this record's column" | REQ-002 |
| Read-only protection of the escalation date-time | KB D17: `EditorReadOnly` is screen-only; the API can still write | REQ-001 |
| Refusal outside the condition through the API | KB D10/D21 verify this for a process display condition; P2 must keep the condition in the process `View` | REQ-002, REQ-003 |

## Gate

G1 not yet held. Approver (profile): Nam. Nothing here is approved.
