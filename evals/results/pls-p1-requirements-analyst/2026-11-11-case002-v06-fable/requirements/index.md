# Requirements index

**G1 approved** by Nam (project owner), 2026-11-05 — scope: REQ-001…004 with assumptions Q1–Q4 as marked.

| ID | Title | Type | Status |
|---|---|---|---|
| REQ-001 | Escalate an inquiry | event-driven | G1 approved |
| REQ-002 | When escalation is available | state-driven + unwanted | G1 approved |
| REQ-003 | Notify the support manager | event-driven | G1 approved |
| REQ-004 | Escalated inquiries stay in the open list | ubiquitous (derived) | G1 approved |
| REQ-005 | 優先度 offers 緊急 | ubiquitous | released (R-20261105-02) |
| REQ-006 | Escalation also available for 緊急 (depends on Q5) | state-driven (derived) | withdrawn at G1 |
| REQ-007 | カテゴリ offers 契約 and 請求 | ubiquitous | awaiting G1 |
| REQ-008 | Past 契約・請求 inquiries are held under the new categories (depends on Q9) | unwanted behaviour | awaiting G1 |
| REQ-009 | AI: 推定カテゴリ follows the category split | ubiquitous (derived) | awaiting G1 |
| REQ-010 | 経理チーム can view 請求 inquiries (scope depends on Q12) | ubiquitous | awaiting G1 |
| REQ-011 | 経理チーム cannot change inquiries or 対応履歴 | unwanted behaviour | awaiting G1 |
| REQ-012 | 経理チーム can view 対応履歴 | ubiquitous | awaiting G1 |
| REQ-013 | Handling time is recorded on 対応履歴 (existing 作業時間, Q17) | ubiquitous | awaiting G1 |
| REQ-014 | Total handling time per inquiry | ubiquitous | awaiting G1 |
| REQ-015 | The total covers 対応履歴 recorded before the release | ubiquitous (derived) | awaiting G1 |

## Open questions for the customer (お客様への確認事項)

Assumptions taken for the slice are marked **[assumed]**; G1 confirms or changes them.

| # | Question (日本語) | Assumption |
|---|---|---|
| Q1 | エスカレーションを実行できるのは対応担当のみですか？編集権限のある全員でよいですか？ | [assumed] anyone with edit rights |
| Q2 | エスカレーション後に状況を「エスカレーション中」に変えてよいですか？（一覧・集計に新しい状況が増えます） | [assumed] yes — status 150 |
| Q3 | 一度エスカレーションした問い合わせを、再度エスカレーションする必要はありますか？ | [assumed] no |
| Q4 | 通知メールの宛先はサポート責任者のみでよいですか？メールの到達確認はどの環境で行いますか？ | [assumed] サポート責任者 only; delivery verified in stg by the customer |

## Change request 2026-11-05 — priority 緊急 (drift accepted on stg)

Source: `sources/2026-11-05-stg-drift-urgent-priority.md`.

**G1** by Nam (tech lead / PM), 2026-11-05: REQ-005 approved; REQ-006 withdrawn. Decisions: Q5 = **no** (緊急 is not escalatable — decided, not assumed); Q6, Q7 and Q-adopt accepted as assumed. The customer question stays open for confirmation.

### Impact analysis (site `inquiries`, current `config/`)

| Element | Impact | Recorded as |
|---|---|---|
| 優先度 (ClassE) choices | 緊急 added before 高 | REQ-005 |
| Process エスカレーション, display condition 優先度 = 高 | 緊急 inquiries cannot be escalated | REQ-006 (Q5) |
| AI 推奨優先度 (ClassG) choices 高/中/低 and the AI script's allowed list | AI never recommends 緊急 | Q6 (no requirement — assumed unchanged) |
| Notification #1 (watches 優先度, subject 「優先度「高」…」) | A change to 緊急 also triggers it | not analysed further — mail deferred (TD-10) |
| Views 1–3, aggregation by 状況, filter/grid columns | 優先度 is shown/filtered as before; new choice appears automatically | none |
| Reminder 1 (対応期限) | does not depend on 優先度 | none |
| Permissions | unchanged | none |

### お客様への確認事項 (open questions)

| # | Question (日本語) | Assumption |
|---|---|---|
| Q5 | 優先度「緊急」の問い合わせも、エスカレーションの対象にしますか？（現在は「高」のみ） | [assumed] はい — 「高」と同じ条件で対象にする (REQ-006) |
| Q6 | AIの「推奨優先度」にも「緊急」を含めますか？ | [assumed] いいえ — AIの推奨は「高」「中」「低」のまま |
| Q7 | 「緊急」は「高」より優先度が高い、という理解でよいですか？ 既存の問い合わせを「緊急」に変更する予定はありますか？ | [assumed] はい、「高」より上。既存データの一括変更はしない |

Q-adopt (from the drift report, asked as written there): 「緊急」を正式な選択肢として採用してよいか — [assumed] はい (REQ-005; tech lead accepted the drift).

## Change request 2026-11-11 — category split, sharing with 経理チーム, handling time

Source: `sources/2026-11-11-category-accounting-worktime.md` (customer mail, 佐藤 — カスタマーサポート課, received 2026-11-11).

**G1: not decided.** REQ-007…REQ-015 are `awaiting G1`. Nothing below is approved; every `[assumed]` is a default that G1 confirms or changes. No answer from the customer or the approver was available when this was written (2026-11-11).

### Impact analysis (sites `inquiries` and `responses`, current `config/`)

| Element | Impact | Recorded as |
|---|---|---|
| 問い合わせ: カテゴリ choices (操作方法 / 不具合 / 契約・請求 / 機能要望 / その他) | 契約・請求 replaced by 契約 and 請求 | REQ-007, Q8 |
| 問い合わせ: existing records with カテゴリ = 契約・請求 | keep the old value unless migrated; a removed choice stays on the record as an orphan (KB D11, D12) | REQ-008, Q9 |
| 問い合わせ: AI: 推定カテゴリ choices, and the category list in the AI first-response script (instruction + allowed values) | would keep proposing 契約・請求, which カテゴリ no longer offers | REQ-009 (derived), Q11 |
| 問い合わせ: list filter カテゴリ / AI: 推定カテゴリ | new choices appear automatically | none |
| 問い合わせ: views 標準, 未完了, 状況×チャネル; aggregation by 状況 | none of them filters or groups by カテゴリ; no category aggregation is configured today | Q10 (no requirement) |
| 問い合わせ: process エスカレーション (condition 優先度 = 高, 状況 100/200/300) | independent of カテゴリ; a read-only user still sees the button (KB D19) | REQ-011 criterion 3, Q15 |
| 問い合わせ: notification #1, reminder 対応期限 | recipients are サポート責任者 / 対応担当; do not depend on カテゴリ; 経理チーム receives nothing | none |
| Permissions of both sites | not in `config/` (no `permissions.json`); `environments.json` already names principals `accounting` and `support` on dev and stg | REQ-010, REQ-011, REQ-012; Q12, Q13 |
| 対応履歴: 作業時間 (number, unit 分, on the edit screen and in the list) | **already exists** — the requested 対応時間 field | REQ-013 (against the existing field), Q17 |
| 問い合わせ: 対応回数 (count of 対応履歴 records) | counts records, not time; stays as is | REQ-014 criterion 6 |
| 問い合わせ: a total of 作業時間 per inquiry | does not exist; new displayed value → edit screen, list, filter, export | REQ-014, Q19 |
| Existing inquiries with 対応履歴 | a new total is not calculated for them by itself (KB D16) | REQ-015 (derived), Q20 |
| 対応履歴: views 標準, 未完了, 状況×対応種別; AI script's reading of 対応履歴 | unaffected (the script reads 対応日時, 対応種別, 件名, 対応内容) | none |

### Constraints stated by the customer (not system behaviour — for P2 and the release plan)

| # | Constraint (customer's words) | Meaning taken | Question |
|---|---|---|---|
| C-1 | 「月次の締めが12月10日なので、それまでに使えるようになると大変ありがたいです」 | usable by the users before 2026-12-10 | Q23 |
| C-2 | 「平日の日中に止まる作業はできれば避けてください」 | no release step or data migration that stops or disturbs use on weekdays during business hours. REQ-008 and REQ-015 include data migrations; a release must also run while nobody edits the site settings (KB D4a) | Q22 |

### お客様への確認事項 (open questions)

None of these is answered. Numbers continue from Q7.

| # | Question (日本語) | Assumption |
|---|---|---|
| Q8 | カテゴリを「契約」と「請求」に分けたあと、「契約・請求」は選択肢から外してよいですか？ 並び順は「操作方法／不具合／契約／請求／機能要望／その他」でよいですか？ | [assumed] はい — 新規の問い合わせでは「契約・請求」を選べないようにし、元の位置に「契約」「請求」の順で置く (REQ-007) |
| Q9 | 過去の「契約・請求」の問い合わせを「契約」「請求」のどちらにするかは、どなたが、どのように決めますか？（内容から自動では判定できません。例：問い合わせ番号と新カテゴリの一覧をご提供いただく）また、対象は解決・クローズ済みを含む全件でよいですか？ | [assumed] お客様（カスタマーサポート課）から問い合わせ番号ごとの振り分け一覧をいただき、そのとおりに更新する。対象は全件。一覧にない問い合わせは「契約・請求」のまま残し、推測での振り分けはしない (REQ-008) |
| Q10 | カテゴリ別の集計は、現在どの画面・方法で行っていますか？（一覧の絞り込み、クロス集計、CSV出力など）新しい集計画面が必要ですか？ | [assumed] 新しい画面は作らない — 既存の一覧の絞り込み・集計機能で「契約」「請求」を選べれば足りる |
| Q11 | AIの「推定カテゴリ」も「契約」「請求」に分けてよいですか？ 過去の問い合わせに保存済みの推定カテゴリ（「契約・請求」）はそのままでよいですか？ | [assumed] はい、カテゴリと同じ選択肢にする。保存済みの推定カテゴリは変更しない (REQ-009) |
| Q12 | **（重要）** 経理チームの方に「請求」以外の問い合わせ（操作方法・不具合など）も見えてしまって問題ありませんか？ それとも「請求」の問い合わせだけに限定する必要がありますか？ | [assumed] 問題なし — 経理チームは問い合わせ全体を閲覧でき、「請求」で絞り込んで確認する (REQ-010, REQ-012)。**閲覧範囲を広げる前提のため、G1で必ず判断すること。**「請求のみに限定」の場合は実現方法が未検証で、P2での検証が必要（お約束はまだできません） |
| Q13 | 「経理チーム」は具体的にどなた（どのグループ）ですか？ メンバーの追加・削除はお客様の管理者が行う、という理解でよいですか？ | [assumed] Pleasanter上の既存の経理グループ（`environments.json` の `accounting`）を使い、メンバー管理はお客様の管理者が行う |
| Q14 | 経理チームに見せたくない項目はありますか？（顧客名、問い合わせ内容、AIの回答の下書き、添付資料、コメント、対応履歴の対応内容・作業時間など。添付資料はダウンロードも可能になります） | [assumed] なし — すべての項目を閲覧可能とする (REQ-010, REQ-012) |
| Q15 | 経理チームの画面に「エスカレーション」ボタンが表示されても（押しても実行は拒否されます）問題ありませんか？ 非表示にする必要がありますか？ また、経理チームはコメントの書き込みも不可でよいですか？ | [assumed] 実行が拒否されれば足りる（非表示は要件にしない）。コメントも不可 (REQ-011) |
| Q16 | 経理チームは問い合わせ・対応履歴のCSV出力（エクスポート）が必要ですか？ | [assumed] 不要 — 画面での閲覧のみ |
| Q17 | 対応履歴にはすでに「作業時間」（単位：分）の項目があります。これを「対応時間」として使ってよいですか？ 項目名を「対応時間」に変える、または単位を変える必要はありますか？ | [assumed] 既存の「作業時間」（分）をそのまま対応時間として使い、新しい項目は追加しない。名称・単位は変更しない (REQ-013) |
| Q18 | 「作業時間」の入力は必須にしますか？ 合計には状況が「予定」の対応履歴も含めますか？ | [assumed] 必須にしない。合計は状況にかかわらずすべての対応履歴を含める (REQ-013, REQ-014) |
| Q19 | 問い合わせごとの合計時間は、項目名「合計対応時間」（単位：分）として、問い合わせの編集画面と一覧に表示し、手入力は不可、でよいですか？ | [assumed] はい (REQ-014) |
| Q20 | 過去の対応履歴には「作業時間」が入力されていますか？ 未入力のものを後から入力する予定はありますか？ | [assumed] 過去分は現在の値のまま合計に含める。未入力は0として扱い、こちらで補完はしない (REQ-015) |
| Q21 | 月次の報告では、問い合わせごとの合計時間のほかに、月ごと・担当者ごと・カテゴリごとの合計などが必要ですか？ | [assumed] 不要 — 問い合わせごとの合計を一覧・既存の出力機能で利用する。新しい集計画面・帳票は作らない |
| Q22 | リリースやデータ更新の作業は、平日の夜間（何時以降）または土日のどちらがよいですか？ その間、設定変更や入力を控えていただくことは可能ですか？ | [assumed] 平日の業務時間外（夜間）または土日に実施し、作業中はお客様に利用を控えていただく (C-2) |
| Q23 | 12月10日までに3件すべてが必要ですか？ 間に合わない場合の優先順位を教えてください。（「できれば」とある過去カテゴリの付け替え、「助かる」とある経理チームの対応履歴閲覧を含めますか？） | [assumed] 3件すべて（REQ-007〜REQ-015）を12月10日までの対象とする。優先順位は 3（対応時間）→ 1（カテゴリ）→ 2（経理共有） (C-1) |

### Points for P2 (not customer questions)

| # | Point | Affects |
|---|---|---|
| P2-1 | Restricting read access per record by a column value (経理チーム sees カテゴリ = 請求 only), and limiting 対応履歴 to the history of such inquiries: **no knowledge-base entry**. Needed only if Q12 is answered "請求 only". Probe on dev before designing; until then it is not promised. | REQ-010, REQ-012 |
| P2-2 | Hiding single fields from a group (if Q14 names any): no knowledge-base entry. Probe before designing. | REQ-010, REQ-012 |
| P2-3 | How an orphan choice value (契約・請求 after its removal) behaves in list filters and aggregations: KB D12 covers the edit screen only. | REQ-008 criterion 3 |
| P2-4 | Current permissions of both sites and whether 対応履歴 inherits from 問い合わせ are not in `config/`. Read them (dev export) before designing. | REQ-010…012 |
| P2-5 | KB entries used (D11–D14, D16–D20, D22, D27) are verified on 1.5.2; check the target environment's version (`pls version`). | all |
| P2-6 | The total of REQ-014 for existing inquiries needs a migration (D16), as does REQ-008; both are data-impacting and fall under C-2. | REQ-008, REQ-015 |
