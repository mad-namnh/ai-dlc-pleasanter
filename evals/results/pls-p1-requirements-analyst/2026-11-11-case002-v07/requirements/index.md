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
| REQ-008 | Past 契約・請求 inquiries carry the new categories (「できれば」 — scope at G1) | ubiquitous | awaiting G1 |
| REQ-009 | AI 推定カテゴリ follows the new categories | event-driven (derived from REQ-007) | awaiting G1 |
| REQ-010 | 経理チーム can view billing inquiries | ubiquitous | awaiting G1 |
| REQ-011 | 経理チーム can view 対応履歴 | ubiquitous | awaiting G1 |
| REQ-012 | 経理チーム cannot change inquiries or 対応履歴 | unwanted behaviour (incl. derived impact on process エスカレーション) | awaiting G1 |
| REQ-013 | Response time is recorded on each 対応履歴 record (existing 作業時間) | ubiquitous | awaiting G1 |
| REQ-014 | Total response time per inquiry | ubiquitous | awaiting G1 |

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

## Change request 2026-11-11 — categories, 経理 sharing, response time (customer mail)

Source: `sources/2026-11-11-improvement-request.md` (佐藤様, カスタマーサポート課, 2026-11-11). REQ-007…REQ-014 — **awaiting G1** (approver: Nam). Nothing below is approved.

Constraints stated by the customer (not requirements of the site; for P2/P5 planning): usable before the monthly closing on **2026-12-10**; avoid work that stops the app on **weekday daytime** (Q23, Q24). Note: the project's release target is `stg`; how the change reaches the environment the customer uses daily is not defined in this project (PO-3).

### Impact analysis (current `config/`, unpacked from the stg rollback exports of R-20261105-05)

Each element by what decides when it acts, not only by its recipient.

| Element | What decides when it acts | Impact | Recorded as |
|---|---|---|---|
| 問い合わせ カテゴリ (ClassD) choices | — | 契約・請求 replaced by 契約, 請求 | REQ-007 |
| Existing inquiries with カテゴリ 契約・請求 | — | value stays on the record when the choice is removed (KB D12) — orphan | REQ-008 (Q10, Q11) |
| AI: 推定カテゴリ (ClassF) choices + script 「AI問い合わせ一次対応」 (`ai1`) category instruction and allowed list | runs on save when 「AIで一次対応する」 is on (BeforeCreate/BeforeUpdate) | enumerates the old list; would keep proposing 契約・請求 | REQ-009 (derived); past values Q12 |
| Views 1 標準, 2 未完了, 3 状況×チャネル | filters: view 2 on 状況 only; view 3 crosstab チャネル × 状況 | none filters or groups by カテゴリ; new choices appear in the カテゴリ filter automatically | none |
| Aggregation 1 | group by 状況 | not by カテゴリ | none (no category aggregation exists today — Q20) |
| Notification #1 (to サポート責任者) | watches 状況, 優先度; BeforeCondition 0 (none), AfterCondition = view 2 未完了 (filter 状況 ∈ 100/150/200/300) | no dependency on カテゴリ, permissions or new columns; 経理 is not a recipient | none |
| Process エスカレーション | display condition 優先度 = 高 and 状況 ∈ 100/200/300; no access control | (a) no カテゴリ dependency; (b) a read-only 経理 user still sees the button when the condition matches and is refused on press (KB D19, D20) | REQ-012 AC3, Q16 |
| Process エスカレーション notification | none of its own (sent on execution) | sent only when the process runs; refused for 経理 | REQ-012 AC3 |
| Reminder 1 (対応期限が3日以内, to 対応担当) | column 対応期限; `Condition: 2` — field not in the KB; value equals view id 2 未完了 (filter on 状況 only) — **unverified** reading | no dependency on カテゴリ, 作業時間 or permissions | none |
| 対応履歴 作業時間 (NumA, 分) | — | existing column already records time per response | REQ-013 (overlap → Q18) |
| 対応履歴 Summary 1 (Count → 問い合わせ 対応回数) | every response create/update/delete | must keep working next to a new total | REQ-014 AC5 |
| New total column on 問い合わせ | — | list, filter, edit screen, export | REQ-014 (Q19, Q21, Q22); past totals need a migration (KB D16) |
| Permissions 問い合わせ / 対応履歴 | — | new read-only role 経理; no `permissions.json` in `config/`, no principal besides admin in `environments.json` | REQ-010, REQ-011, REQ-012 (Q13–Q17, PO-2) |
| `environments.json` `managed_sites` | — | only `inquiries`; REQ-011…014 change `responses` | PO-1 |
| Statuses | — | no new status in the request or in any open question | none |

### お客様への確認事項 (open questions)

| # | Question (日本語) | Assumption | REQ |
|---|---|---|---|
| Q8 | 「契約・請求」の位置に「契約」「請求」の順で並べてよいですか？（操作方法／不具合／契約／請求／機能要望／その他） | [assumed] はい | REQ-007 |
| Q9 | 「契約」と「請求」の分け方の基準を教えてください。（例：契約＝契約内容・更新・解約・プラン変更、請求＝請求書・支払い・料金・返金）AIのカテゴリ推定にも同じ基準を使います。 | [assumed] 例のとおり | REQ-007, REQ-009 |
| Q10 | 過去の「契約・請求」の問い合わせはおよそ何件ありますか？ 1件ずつ「契約」か「請求」かを判断するのはどなたですか？ | [assumed] お客様が問い合わせ番号ごとの振り分け一覧（契約／請求）をご用意いただき、MADLABがバックアップを取ったうえで一括更新する。一覧にない問い合わせは推測で振り分けず、リリース前にご報告する | REQ-008 |
| Q11 | 過去分の振り分けが12月10日に間に合わない場合、新しいカテゴリへの切り替えを先に行い、過去分は後から更新する形でよいですか？ | [assumed] はい — REQ-008 は REQ-007 の後でもよい | REQ-008 |
| Q12 | 過去の問い合わせの「AI: 推定カテゴリ」に残っている「契約・請求」はそのままでよいですか？（AIが当時推定した記録です） | [assumed] はい、そのまま残す | REQ-009 |
| Q13 | 経理チームの方はどなたですか？ Pleasanter上に「経理」のグループはありますか？（なければ作成とメンバー登録をどなたが行いますか） | [assumed] お客様が「経理」グループを用意し、メンバーを登録する | REQ-010…012 |
| Q14 | 経理チームの方に、「請求」以外のカテゴリの問い合わせ（顧客名・問い合わせ内容を含む）が見えてもよいですか？ 見えないようにする必要がある場合はお知らせください（実現方法を検証してからご回答します）。また、請求の問い合わせだけを並べた一覧は必要ですか？ | [assumed] 見えてもよい（問い合わせ全体を閲覧のみ可）。専用の一覧は不要（カテゴリで絞り込む） | REQ-010 |
| Q15 | 対応履歴も、請求の問い合わせの分だけに限定する必要はありますか？ | [assumed] いいえ、対応履歴全体を閲覧のみ可（Q14と同じ扱い） | REQ-011 |
| Q16 | 経理チームの方の画面に「エスカレーション」ボタンが表示されないようにしてよいですか？（現在の設定では、閲覧のみの方にもボタンは表示され、押すとエラーになります。非表示にするには、エスカレーションできる方（またはグループ）を指定する必要があります） | [assumed] はい、非表示にする。エスカレーションできるのはサポート課のメンバー（編集権限のある方）全員 | REQ-012 |
| Q17 | 経理チームの方が一覧をExcel/CSVに出力する必要はありますか？ | [assumed] いいえ（閲覧のみ） | REQ-012 |
| Q18 | 対応履歴には既に「作業時間（分）」の項目があります。これを「対応時間」として使ってよいですか？ 現在、この項目は入力されていますか？ | [assumed] はい、既存の「作業時間」を使い、新しい項目は追加しない | REQ-013 |
| Q19 | 問い合わせごとの合計時間は「分」で表示してよいですか？ 「時間」（例：1.5時間）での表示が必要ですか？ | [assumed] 分で表示 | REQ-014 |
| Q20 | 月次報告では、どの月で集計しますか？（問い合わせの受付日の月／対応履歴の対応日時の月）。月をまたぐ問い合わせはどう扱いますか？ | [assumed] 問い合わせごとの累計の合計時間のみを表示し、月次の数値は一覧・出力からお客様が集計する | REQ-014 |
| Q21 | リリース前に入力済みの対応履歴の作業時間も、合計に含めますか？ | [assumed] はい、リリース後に過去分も再計算する | REQ-014 |
| Q22 | 合計時間は問い合わせの一覧と編集画面に表示すればよいですか？（編集画面では変更不可、絞り込みには追加しない） | [assumed] はい | REQ-014 |
| Q23 | 作業してよい時間帯を教えてください（例：平日19時以降、土日）。切り替え作業中は入力を控えていただく必要があります（所要時間は設計後にお知らせします）。 | [assumed] 平日19時以降または土日に実施し、事前に日時をご連絡する | all (P5) |
| Q24 | 12月10日までに3点すべてが必要ですか？ 間に合わない場合に優先する項目はどれですか？ | [assumed] 3点とも12月10日より前に利用開始。優先順位はご回答待ち | all (P5) |

### Questions for the project owner (internal, not for the customer)

| # | Question | Default until answered |
|---|---|---|
| PO-1 | `environments.json` `managed_sites` lists only `inquiries`, but REQ-011…014 change `responses` (permissions, summary). Bring `responses` under management in P2? | yes — P2 proposes it |
| PO-2 | No `permissions.json` exists for either site and no principal besides admin is mapped. Can an operator export the current site permissions (and the 経理 group id per environment) before P2? | P2 waits for the export; no permission is designed blind |
| PO-3 | Release target is `stg` (Stage `demo`). The customer uses the app daily and asks for 2026-12-10; which environment is "production" for this request, and does `handover/customer-responsibilities.md` need to be filled first? | treat stg as the target; raise at G1 |
| PO-4 | Observation outside this request: notification #1's subject is 「優先度「高」の問い合わせが未対応です」 but its condition (view 2 未完了) does not filter on 優先度, so it is sent for any priority. Raise with the customer separately? | not part of this change |
