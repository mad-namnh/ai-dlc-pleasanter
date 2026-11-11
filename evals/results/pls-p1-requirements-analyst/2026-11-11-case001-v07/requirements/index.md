# Requirements index

Earlier requirement documents of this app were not carried into this folder; numbering starts at REQ-001 here.

| ID | Title | EARS type | Source | Status |
|---|---|---|---|---|
| REQ-001 | One-click escalation of a high-priority inquiry | state-driven | `sources/2026-11-11-escalation-high-priority.md` | awaiting G1 |
| REQ-002 | No escalation for inquiries that are not high priority | unwanted behaviour | same | awaiting G1 |
| REQ-003 | Record the escalation date and time | event-driven | same | awaiting G1 |
| REQ-004 | Mail to the サポート責任者 on escalation | event-driven | same | awaiting G1 |
| REQ-005 | Escalation keeps 状況 and 優先度 (derived) | event-driven | derived from REQ-001/003/004 impact | awaiting G1 |

## Current configuration read (site 問い合わせ, `config/inquiries/`)

Elements the request touches, each with **what decides when it acts**:

| Element | What it does | What decides when it acts |
|---|---|---|
| Column 優先度 (`ClassE`, 高/中/低) | escalation scope | — |
| Column 対応担当 (`Owner`), サポート責任者 (`Manager`) | who escalates / who is told | — |
| Status (100 受付, 200 対応中, 300 顧客回答待ち, 900 解決, 910 クローズ（対応不要）) | life cycle | — |
| View 2 未完了 | open inquiries | `ColumnFilterHash` Status ∈ 100/200/300 |
| View 3 状況×チャネル | crosstab count | groups by Status (Y) × チャネル (X) |
| View 1 標準 | default list | no filter |
| Notification #1 (mail to `[Manager]`, subject 「優先度「高」の問い合わせが未対応です」, prefix 【問い合わせ管理】) | tells the サポート責任者 | watches columns Status and 優先度 (`MonitorChangesColumns`); `AfterCondition` = view 2 → takes over view 2's Status filter (100/200/300); `BeforeCondition` 0. It does **not** itself filter on 優先度 = 高 despite its subject. |
| Reminder #1 (mail to `[Owner]`, 「対応期限が3日以内の問い合わせ」) | warns the 対応担当 of the due date | column 対応期限 (`DateB`), range 3 days, excludes overdue; `Condition: 2` — **unverified**: the field is not in the KB; its value equals the Id of view 2 未完了, so it probably limits the reminder to Status 100/200/300 |
| Aggregation #1 | count by 状況 on the grid | groups by Status |
| Server script `ai1` (BeforeCreate / BeforeUpdate) | AI first response when 「AIで一次対応する」 is on | runs on every save but acts only when `CheckA` is true; its prompt maps Status values to labels with a fixed list 100/200/300/900/910 |
| Server script `aiEnv` (shared) | environment setting | — |

No existing column holds an escalation date-time, and no existing feature performs an escalation (overlap check: REQ-003 notes). The existing notification #1 overlaps with the requested mail (same recipient, about high-priority unresolved inquiries): raised as Q7.

## Impact analysis

**With the assumed answer to Q2 (escalation does not change 状況):** escalation writes only the new エスカレーション日時 and sends a mail. Views 1–3, aggregation #1 and reminder #1 are unaffected as long as 状況 and 優先度 stay unchanged (REQ-005). `ai1` runs on the escalation save but does nothing unless 「AIで一次対応する」 is on. Notification #1 watches only Status and 優先度, so the escalation save should not trigger it — unverified (see below).

**Impact analysis — if a status is added (Q2 answered "yes", e.g. エスカレーション済):**
- View 2 未完了 filters Status 100/200/300 → escalated inquiries would disappear from the open list unless the new status is added to the filter.
- Notification #1 has view 2 as `AfterCondition` and watches Status → the escalation (a status change) would trigger it, and later changes on escalated inquiries would no longer notify the サポート責任者 if the new status is outside view 2.
- Reminder #1 (`Condition: 2`, probably view 2) → the 対応担当 would stop receiving due-date reminders for escalated inquiries.
- Aggregation #1 and view 3 (by 状況) → a new group / row appears.
- Server script `ai1` enumerates statuses in its label map → the AI prompt would show the raw value instead of the label for the new status.
- Each of these becomes a derived requirement once Q2 is answered.

## お客様への確認事項 (open questions)

| # | 質問 | 想定（回答がない場合の前提） | Affects |
|---|---|---|---|
| Q1 | エスカレーションを実行できるのは、その問い合わせの「対応担当」に設定されている本人だけですか？それとも問い合わせを編集できる担当者なら誰でも（サポート責任者自身も含めて）実行できますか？ | `[assumed]` 問い合わせを編集できる利用者は誰でも実行できる（閲覧のみの利用者は実行不可）。 | REQ-001 |
| Q2 | エスカレーションしたときに「状況」を変えますか？（例：新しい状況「エスカレーション済」を追加する） | `[assumed]` 状況は変えない（エスカレーション日時の記録とメール送信のみ）。 | REQ-005, impact analysis |
| Q3 | 「解決」「クローズ（対応不要）」の問い合わせでもエスカレーションできる必要がありますか？ | `[assumed]` できない。受付・対応中・顧客回答待ちの問い合わせのみ。 | REQ-001 |
| Q4 | 同じ問い合わせを2回以上エスカレーションすることはありますか？ある場合、日時は最初のものを残しますか、最新のものに更新しますか？ | `[assumed]` 1件につき1回のみ。エスカレーション後はボタンを表示しない。 | REQ-001, REQ-003 |
| Q5 | 優先度が「中」「低」の問い合わせはエスカレーションできない、という理解でよいですか？また、エスカレーション後に優先度が下がった場合、記録した日時はそのまま残してよいですか？ | `[assumed]` 「高」のみ実行可。優先度が後で変わっても日時は残す。 | REQ-002 |
| Q6 | 「サポート責任者」が未設定の問い合わせでエスカレーションした場合、どうしますか？ | `[assumed]` 問い合わせに設定された「サポート責任者」にメールする。未設定の場合はエスカレーションを受け付けず、画面にメッセージを表示する（G1で承認された場合のみ要件化）。 | REQ-004 |
| Q7 | 現在、優先度または状況が変わったときに、サポート責任者へ「優先度「高」の問い合わせが未対応です」というメールが送られています。エスカレーションのメールは、この既存の通知とは別に送りますか？既存の通知は今のままでよいですか？ | `[assumed]` エスカレーション専用のメールを別に送る。既存の通知は変更しない。 | REQ-004, REQ-005 |
| Q8 | エスカレーションのメールの件名と本文には何を載せますか？ | `[assumed]` 件名「【問い合わせ管理】エスカレーション: 問い合わせ番号 件名」、本文に問い合わせ番号・件名・顧客名・優先度・対応担当・対応期限・エスカレーション日時。 | REQ-004 |
| Q9 | 記録する項目の名前は「エスカレーション日時」でよいですか？編集画面のほか、一覧の列や絞り込みにも表示しますか？ | `[assumed]` 項目名「エスカレーション日時」。編集画面にのみ表示（一覧・絞り込みへの追加は回答があれば対応）。 | REQ-003 |
| Q10 | 「エスカレーション日時」を利用者が手で修正できる必要はありますか？ | `[assumed]` 手での修正は不可（画面上は読み取り専用）。 | REQ-003 |
| Q11 | エスカレーションの際に、理由やコメントの入力、または「実行しますか？」の確認は必要ですか？ | `[assumed]` 入力も確認もなし（ボタン1回で完了）。 | REQ-001 |
| Q12 | エスカレーションを受けたサポート責任者側で、受領や対応完了などの操作・記録は必要ですか？ | `[assumed]` 不要（今回の範囲外）。 | scope |

## Points P2 must verify before designing (not covered by the KB)

| Point | Why it matters | REQ |
|---|---|---|
| Meaning of reminder field `Condition` (value 2 = view 2 Id?) | Decides whether escalated inquiries keep their due-date reminder | REQ-005, Q2 |
| Notification #1: does `MonitorChangesColumns` limit sending to saves where Status / 優先度 changed? Meaning of `Expression: 1` | Decides whether the escalation save triggers the existing mail (duplicate) | REQ-004, REQ-005, Q7 |
| Restricting an action to the record's own 対応担当 (`Owner` of that record) | KB D20 covers only group / user / dept lists | REQ-001, Q1 |
| Refusing (or hiding) the action when エスカレーション日時 is already set or サポート責任者 is empty | View filter behaviour on empty date / user columns is not in the KB (D9 covers checkboxes, D23 numbers) | REQ-001, Q4, Q6 |

## Notes for the project owner

- The project profile says Origin `new`; the request states that this project built the app (DES-000), so this is a change request through P1, not a takeover.
- Observation outside this request: in `environments.json`, `stg.values.AI_GATEWAY_URL` is the same URL as dev (contains `-dev-`). Not part of this change; worth checking.
