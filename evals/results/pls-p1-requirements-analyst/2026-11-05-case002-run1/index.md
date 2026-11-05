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
| REQ-007 | カテゴリ offers 契約 and 請求 instead of 契約・請求 | ubiquitous | awaiting G1 |
| REQ-008 | Past 契約・請求 inquiries are reclassified as 契約 or 請求 (depends on Q9, Q10) | event-driven | awaiting G1 |
| REQ-009 | AI: 推定カテゴリ uses the new categories (depends on Q12) | event-driven (derived) | awaiting G1 |
| REQ-010 | 経理チーム can view 請求 inquiries | state-driven | awaiting G1 |
| REQ-011 | 経理チーム can view the 対応履歴 of 請求 inquiries | state-driven | awaiting G1 |
| REQ-012 | 経理チーム cannot change inquiries or 対応履歴 | unwanted behaviour | awaiting G1 |
| REQ-013 | エスカレーション is not offered to 経理チーム | unwanted behaviour (derived) | awaiting G1 |
| REQ-014 | Each inquiry shows the total 作業時間 of its 対応履歴 | ubiquitous | awaiting G1 |
| REQ-015 | Existing inquiries show their correct 合計作業時間 from release (depends on Q18) | state-driven (derived) | awaiting G1 |
| REQ-016 | 対応回数 keeps counting 対応履歴 | ubiquitous (derived) | awaiting G1 |

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

## Change request 2026-11-05 — category split, 経理 access, work time (customer mail, 佐藤様)

Source: `sources/2026-11-05-category-billing-worktime.md` (mail from 佐藤様, みなと商事 カスタマーサポート課, received 2026-11-05).
Requirements REQ-007 … REQ-016 — **awaiting G1**. Nothing here is approved.

### Mapping of the mail to requirements

| Mail item | Requirements | Main open questions |
|---|---|---|
| 1. カテゴリの見直し（契約・請求 → 契約／請求、過去分も集計） | REQ-007, REQ-008, REQ-009 (derived) | Q8–Q12, Q22 |
| 2. 経理チームへの共有（見るだけ、対応履歴も） | REQ-010, REQ-011, REQ-012, REQ-013 (derived) | Q13–Q15 |
| 3. 対応時間の記録（対応履歴に入力、問い合わせごとの合計） | REQ-014, REQ-015 (derived), REQ-016 (derived) | Q16–Q20, Q22 |
| Constraints: 12月10日の月次締めまでに利用可能／平日日中の停止を避ける | constraints C1, C2 (below) | Q21 |

Dependency: REQ-010/REQ-011 identify 請求 inquiries by the new カテゴリ 請求, so they need REQ-007 (and REQ-008 for past inquiries).

### Existing elements that already cover part of the request (overlaps → questions, no new element)

| Request | Existing element | Handling |
|---|---|---|
| 「対応履歴に対応時間を入れられるように」 | 対応履歴 already has **作業時間** (unit 分, NumA), shown in the grid and on the edit screen | No new column; REQ-014 uses 作業時間 — Q16 |
| 「問い合わせごとに合計」 | 問い合わせ管理 already aggregates 対応履歴 as **対応回数** (count) | Same mechanism extended with a total — REQ-014; protect the count — REQ-016 |
| 「見るだけ」 | Pleasanter read permission (value 1) — KB D19 | REQ-010…012 rely on it; no custom mechanism |

### Impact analysis (current `config/`)

| Element | Impact | Recorded as |
|---|---|---|
| `inquiries` カテゴリ (ClassD) choices | 契約・請求 replaced by 契約, 請求; stored values stay until migrated (D12) | REQ-007, REQ-008 |
| `inquiries` AI: 推定カテゴリ (ClassF) choices + AI script allowed list / instruction text | AI keeps proposing 契約・請求 | REQ-009 (Q12) |
| AI script input (カテゴリ value sent to the AI as text) | new values are sent as they are | none |
| `inquiries` views 1–3, aggregation (Status), notification #1 (watches 状況, 優先度), reminder 1 (対応期限) | none filters or monitors カテゴリ → unaffected by the split; category change during migration does not touch monitored columns (confirm — EP-8) | none |
| `inquiries` grid / filter / link columns (ClassD) | new choices appear automatically; 契約・請求 remains as an orphan value until migrated | REQ-007 AC 4 |
| `inquiries` process エスカレーション (no access control) | rendered for read-only users (D19) | REQ-013 (Q14) |
| Site permissions of `inquiries` and `responses` | new 経理 read-only role; current permissions not in git | REQ-010…012, EP-3, EP-4 |
| `inquiries` new column 合計作業時間 | editor layout, grid, filters, exports | REQ-014 (Q17) |
| `responses` aggregation (Count → 対応回数) | a second aggregation is added on the same link; first deploy of this site from git (full replacement, D4) | REQ-016, EP-1, EP-6 |
| Existing inquiries' totals | not recalculated by a new aggregation (D16) | REQ-015 (Q18) |
| `responses` 作業時間 (NumA) | unchanged (optional field) | Q19 (required? — not in scope unless decided) |
| `responses` views, crosstab 状況×対応種別 | unaffected | none |
| Escalation mail (REQ-003), reminder recipients | 経理 are neither サポート責任者 nor 対応担当 → receive nothing | none (Q15) |

### Constraints (from the mail — not EARS requirements; they bind the release plan, P5)

| # | Constraint | Source | Open point |
|---|---|---|---|
| C1 | The changes are usable in production before the monthly close on **2026-12-10 (Thu)** — i.e. released by 2026-12-09 at the latest. | 「月次の締めが12月10日なので、それまでに使えるようになると大変ありがたいです」 | Q21; deadline is a wish (「ありがたい」), not a hard commitment, until confirmed |
| C2 | No deployment or migration that interrupts the sites during weekday daytime. | 「平日の日中に止まる作業はできれば避けてください」 | Q21; whether a deploy (`updatesite`) or migration interrupts users is not in the KB — EP-9 |

### Engineering prerequisites (to settle before / during P2; no live system was reachable during P1)

| # | Prerequisite | Why | Blocks |
|---|---|---|---|
| EP-1 | Bring `responses` under management: add it to `managed_sites`, export it from every environment, record its slots in `design/slot-ledger.json` (lint currently reports 5 × L-SLOT-01 for `responses`), run a drift check git ↔ live. | The git copy of `responses` has never been deployed by `pls`; a full-replacement deploy (D4) of a stale copy would overwrite live settings. | REQ-011, REQ-012, REQ-014–016 |
| EP-2 | Add the **production** environment to `environments.json` (site IDs, principals, values). Only dev and stg are defined. | The customer uses the app daily — the target of C1 is production. | release (all) |
| EP-3 | Export the current site permissions and inheritance of `inquiries` and `responses` in every environment (`getsite` → `InheritPermission`, `Permissions` — D15) and decide whether to put them in git (`permissions.json`, ADR-0006). Establish whether `responses` inherits from `inquiries`. | Permissions are not in git; REQ-010–012 change them. | REQ-010–013 |
| EP-4 | Obtain the principal IDs (per environment) of the 経理 group and of the support staff group, and add them to `environments.json` `principals`. | Permissions and process access control use environment-specific IDs (L-PERM-01). | REQ-010–013 |
| EP-5 | **Only if Q13 = 「請求のみ」:** find and probe on dev a way to restrict a read-only role to records of one カテゴリ (and to the 対応履歴 of those records). Not in `pls-kb-pleasanter`; no requirement may rely on it until probed and recorded in the KB. | Site permissions are site-wide (D19); record-level restriction is unverified. | scope of REQ-010/011 |
| EP-6 | Probe on dev: two aggregations (Count and Total) from `responses` to `inquiries` on the same link column — both recomputed on child create/update/delete. | D16 verified a single Total only. | REQ-014, REQ-016 |
| EP-7 | Data checks on production (read-only export): number of inquiries with カテゴリ 契約・請求; uniqueness of 問い合わせ番号 (D18); fill rate of 作業時間 in 対応履歴; number of inquiries with 対応履歴 (size of the REQ-015 touch). Back up affected records before any migration (D14). | Sizes the migrations and the release window; non-unique keys stop `bulkupsert` (D18). | REQ-008, REQ-015 |
| EP-8 | Probe on dev: a migration update of カテゴリ (and a touch of 対応履歴) does not send notification #1 or the escalation mail and does not run the AI script. | Notification #1 monitors 状況/優先度 only, but behaviour on API/bulk updates is not in the KB. | REQ-008 AC 5, REQ-015 |
| EP-9 | Measure on dev/stg whether `updatesite` and the migrations interrupt or slow users (and for how long). | C2; not in the KB. | release plan |

### お客様への確認事項 (open questions)

Assumptions are marked **[assumed]**; G1 confirms or changes them. Q1 (who may escalate) is affected by REQ-013 — see Q14.

| # | Question (日本語) | Assumption | Affects |
|---|---|---|---|
| Q8 | 新しいカテゴリは「操作方法／不具合／契約／請求／機能要望／その他」の順でよいですか？また、今後新しく登録する問い合わせでは「契約・請求」を選べないようにしてよいですか？ | [assumed] はい — この順序。「契約・請求」は新規には選べない（既存データは振り分けまで「契約・請求」のまま表示） | REQ-007 |
| Q9 | 過去の「契約・請求」の問い合わせを「契約」「請求」に振り分ける方法についてご相談です。システムで内容から自動判定することはできないため、問い合わせ番号ごとに「契約」か「請求」かを記入した一覧（Excel等）をご用意いただくことは可能でしょうか？（AIによる推定結果を下書きとしてお出しし、確認いただく方法もご提案できます） | [assumed] お客様が一覧を作成し、MADLABが一括で反映する。一覧にない問い合わせは「契約・請求」のまま残し、現場で個別に変更する | REQ-008 |
| Q10 | 過去分の振り分けは、どの期間の問い合わせが対象ですか？また、12月10日の締めまでに必要ですか（11月分の報告から新しいカテゴリで集計しますか）？ | [assumed] 全期間の「契約・請求」が対象。12月10日の締めまでに反映（一覧を11月末までにいただける前提） | REQ-008, C1 |
| Q11 | 月次の集計は、現在どの方法で行っていますか（一覧画面の絞り込み、Excel/CSV出力、クロス集計など）？カテゴリ別のクロス集計画面が新たに必要ですか？ | [assumed] 既存の一覧の絞り込み・出力で集計する。新しい集計画面は追加しない | REQ-007/008 (scope) |
| Q12 | AIの「推定カテゴリ」も新しいカテゴリ（「契約」「請求」）で推定するように変更してよいですか？過去のAI推定結果（「契約・請求」）はそのまま残してよいですか？ | [assumed] はい — AIも新カテゴリで推定。過去のAI推定結果は変更しない | REQ-009 |
| Q13 | 経理チームの方が見られる範囲について確認させてください。「請求」以外のカテゴリの問い合わせ・対応履歴も（見るだけで）見えてしまってよいですか？それとも「請求」のものだけに限定する必要がありますか？ | [assumed] 「請求」以外も閲覧可（変更は不可）。経理の方は一覧でカテゴリ「請求」に絞り込んで確認する。限定が必要な場合は実現方法を検証のうえ別途ご提案（12月10日に間に合わない可能性あり） | REQ-010, REQ-011, EP-5 |
| Q14 | 経理チームの方はPleasanterのユーザーとして登録済みですか？「経理」のグループ（または組織）はありますか？あわせて、エスカレーションボタンを経理の方に表示しないために、エスカレーションを実行できる方（カスタマーサポート課のメンバー）をグループで指定したいのですが、該当するグループはありますか？ | [assumed] お客様が本番・検証環境に「経理」グループとサポート課のグループを用意し、メンバーを登録する。エスカレーションはサポート課グループのメンバーのみ実行可（Q1の「編集権限のある全員」はサポート課メンバー全員と読み替え） | REQ-010–013, EP-4 |
| Q15 | 経理チームの方に、Excel/CSV出力、添付資料のダウンロード、コメントの書き込み、メール通知は必要ですか？ | [assumed] 出力は不要、添付資料は閲覧（ダウンロード）可、コメント不可、メール通知なし | REQ-010–012 |
| Q16 | 対応履歴には既に「作業時間（分）」の項目があります。これを「対応時間」として使い、問い合わせごとの合計はこの値を合計する、という理解でよいですか？ | [assumed] はい — 既存の「作業時間」に入力し、新しい項目は追加しない | REQ-014 |
| Q17 | 問い合わせごとの合計は「分」単位の表示でよいですか（「時間」単位が必要ですか）？項目名は「合計作業時間」でよいですか？一覧画面にも表示しますか？ | [assumed] 分単位、項目名「合計作業時間」、編集画面と一覧画面の両方に表示 | REQ-014 |
| Q18 | 過去の対応履歴にも作業時間は入力されていますか？過去の問い合わせについても合計を表示する必要がありますか？ | [assumed] はい — 既存のすべての問い合わせについて合計を表示する（未入力の作業時間は0分として計算） | REQ-015 |
| Q19 | 今後、対応履歴の「作業時間」を必須入力にしますか？（未入力だと合計が実際より少なくなります） | [assumed] いいえ — 必須にはしない（現状どおり） | none unless decided (would be a new requirement) |
| Q20 | 月次報告では、「その月に受け付けた問い合わせ」の合計時間を使いますか、それとも「その月に行った対応」の時間を使いますか？ | [assumed] 問い合わせごとの累計（全期間）を表示し、月の区切りは受付日でお客様が絞り込む | REQ-014 (scope) |
| Q21 | 作業を避けるべき「平日の日中」は何時から何時でしょうか？リリース作業は平日夜間または休日に行ってよいですか？また「12月10日までに使える」とは、12月9日までに本番で使える状態になっていればよい、という理解でよいですか？ | [assumed] 平日 9:00–18:00 を避け、平日18時以降または休日に作業。12月9日（水）までに本番へ反映 | C1, C2 |
| Q22 | 過去データの振り分け・合計計算のため、対象の問い合わせと対応履歴の「更新日時」「更新者」が作業日時・作業用アカウントに変わります（内容は変わりません）。問題ありませんか？ | [assumed] 問題なし | REQ-008, REQ-015 |
