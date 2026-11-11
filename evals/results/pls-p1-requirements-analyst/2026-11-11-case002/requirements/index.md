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
| REQ-008 | Past 契約・請求 inquiries are counted under 契約 or 請求 | ubiquitous | awaiting G1 |
| REQ-009 | AI: 推定カテゴリ proposes only categories that カテゴリ offers | event-driven (derived) | awaiting G1 |
| REQ-010 | 経理チーム can view 請求 inquiries | ubiquitous | awaiting G1 |
| REQ-011 | 経理チーム can view the 対応履歴 of those inquiries | ubiquitous | awaiting G1 |
| REQ-012 | 経理チーム cannot change inquiries or 対応履歴 | unwanted behaviour | awaiting G1 |
| REQ-013 | Record the time of each response in the existing 作業時間 | ubiquitous | awaiting G1 |
| REQ-014 | Each inquiry shows the total 作業時間 of its 対応履歴 | event-driven | awaiting G1 |

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

## Change request 2026-11-11 — category split, 経理 read access, response time (customer mail)

Source: `sources/2026-11-11-improvement-request.md` (佐藤, カスタマーサポート課, received 2026-11-11). **G1 not yet decided** — REQ-007…014 await G1.

### Constraints stated by the customer (input for P2/P5, not EARS requirements)

| # | Constraint | Note |
|---|---|---|
| C1 | Usable by **2026-12-10** (monthly closing) | Scope / order decided at G1 (Q25) |
| C2 | Avoid work that stops the app on **weekdays during the day** | Release window to be agreed (Q24); releases must also run while nobody edits the sites (KB D4a) |

### Impact analysis (current `config/inquiries/`, `config/responses/`)

| Element | Impact | Recorded as |
|---|---|---|
| カテゴリ (ClassD) choices | 契約・請求 replaced by 契約, 請求; stored 契約・請求 values stay (D12) — data-impacting (D11) | REQ-007, REQ-008 (Q8–Q11) |
| AI: 推定カテゴリ (ClassF) choices and `ai1` allowed list / instruction (lists 契約・請求) | AI would keep proposing a category カテゴリ no longer offers | REQ-009 (derived, Q12) |
| Views 1–3, aggregation (by 状況), notification #1, reminder 1 | do not filter on カテゴリ; カテゴリ filter/grid shows the new choices automatically | none |
| Escalation process (no access control) | read-only 経理 users still see the button on matching inquiries; pressing it is refused (D19) | REQ-012 AC 6 (Q16) |
| Site permissions of 問い合わせ and 対応履歴 | new read-only group 経理; current permissions not in `config/` | REQ-010…012 (Q13–Q15, PO4) |
| 対応履歴 作業時間 (NumA, 分) | already holds the time per response — no new column | REQ-013 (Q17) |
| 問い合わせ: new total column; summary on 対応履歴 | new column (slot ledger, editor, grid); existing parents not recalculated (D16) — data-impacting | REQ-014 (Q18–Q23) |
| 対応回数 (Count summary) | must keep working next to the new summary | REQ-014 AC 8 |
| `ai1` related-history columns | do not include 作業時間 | none |

### お客様への確認事項 (open questions)

| # | Question (日本語) | Assumption |
|---|---|---|
| Q8 | カテゴリの並び順は「操作方法・不具合・契約・請求・機能要望・その他」（「契約・請求」の位置に「契約」「請求」を入れる）でよろしいですか？ | [assumed] はい |
| Q9 | 今後新しく登録する問い合わせでは「契約・請求」を選べないようにしてよろしいですか？（過去の問い合わせの値は、振り分けるまでそのまま残ります） | [assumed] はい — 選択肢から外す |
| Q10 | 過去の「契約・請求」の問い合わせは何件ほどありますか？ 1件ずつ「契約」「請求」のどちらにするかは、どなたが判断されますか？（例：問い合わせ番号と新しいカテゴリの一覧をいただき、当社で一括更新する） | [assumed] お客様が問い合わせ番号ごとの一覧を作成し、当社が一括更新する。一覧にないものは「契約・請求」のまま残す |
| Q11 | 過去分の振り分けが12月10日に間に合わない場合、新しいカテゴリの追加だけを先に使えるようにしてよろしいですか？ | [assumed] はい — 過去分は後から更新 |
| Q12 | AIの「推定カテゴリ」も「契約」「請求」に分けてよろしいですか？ 過去の問い合わせに入っているAIの推定結果（「契約・請求」）はそのまま残してよろしいですか？ | [assumed] はい／はい（過去のAI結果は変更しない） |
| Q13 | 経理チームの方が見られる問い合わせは「請求」だけに限定する必要がありますか？ それとも、他のカテゴリの問い合わせも見えてよく、カテゴリで絞り込んで確認する形でよろしいですか？ | [assumed] 全件見えてよい（カテゴリ「請求」で絞り込んで確認）。限定が必要な場合は実現方法を検証してからご回答します |
| Q14 | 経理チームの方はどなたですか？（Pleasanter上のユーザー／グループ名、人数） | [assumed] お客様が Pleasanter に「経理」グループを用意し、メンバーを登録する |
| Q15 | 経理チームの方は、一覧のエクスポート（CSV出力）やコメントの書き込みが必要ですか？ | [assumed] どちらも不要（閲覧のみ） |
| Q16 | 経理チームの方の画面にも「エスカレーション」ボタンが表示されます（押しても権限エラーで実行されません）。これでよろしいですか？ 非表示にする場合、エスカレーションできる方を限定する設定が必要になります。 | [assumed] 表示されたままでよい（エスカレーションの設定は変更しない） |
| Q17 | 「対応時間」は、対応履歴にすでにある項目「作業時間（分）」に入力する、という理解でよろしいですか？ 項目名を「対応時間」に変更しますか？ | [assumed] 既存の「作業時間（分）」を使い、項目名は変えない |
| Q18 | 問い合わせごとの合計時間は「分」で表示してよろしいですか？（「時間」単位が必要ですか？） | [assumed] 分 |
| Q19 | 合計には、状況が「予定」の対応履歴も含めますか？ | [assumed] はい — すべての対応履歴を合計（未入力は0分） |
| Q20 | 月次の報告では、問い合わせごとの合計時間があれば十分ですか？ 月ごと（対応日時の月）の合計も必要ですか？ | [assumed] 問い合わせごとの合計のみ。月ごとの集計は一覧の絞り込み・出力で行う |
| Q21 | 対応履歴を登録するとき、作業時間の入力を必須にしますか？ | [assumed] 必須にしない |
| Q22 | 合計時間は問い合わせの編集画面と一覧の両方に表示し、手で書き換えられない項目にしてよろしいですか？ | [assumed] はい |
| Q23 | すでに登録されている対応履歴の作業時間も、合計に含めてよろしいですか？（リリース後に当社で再計算します） | [assumed] はい |
| Q24 | 「平日の日中」は何時から何時ですか？ 改修の反映（数分〜、その間の編集は避けていただく必要があります）は、平日の夜間や休日に行ってよろしいですか？ | [assumed] 平日 9:00–18:00 を避け、平日夜間に実施 |
| Q25 | 12月10日までに3点すべてが難しい場合、どれを優先しますか？ | [assumed] 3点すべてを12月10日までに。過去分のカテゴリ振り分け（REQ-008）のみ後日でも可 |

### Questions for the project owner (before G1)

| # | Question | Why |
|---|---|---|
| PO1 | Which environment does the customer's 現場 use every day? `environments.json` has only dev and stg; the release target is `stg`. | The mail says the app is in daily use; live-data migrations (REQ-008, REQ-014) and the release window depend on it |
| PO2 | `managed_sites` lists only `inquiries`, but REQ-011, REQ-012 and REQ-014 change the 対応履歴 site (`config/responses/` exists). Add it? | Changes to 対応履歴 cannot be released otherwise |
| PO3 | `config/inquiries/server-scripts/ai1.js` holds the literal site id `"44574"` (stg 対応履歴) instead of `${site:responses}` as DES-000 states (KB D3). | Existing defect: on dev the AI would read stg data. Not part of this request — triage separately? |
| PO4 | No `permissions.json` / `design/roles.json`: what are the current site permissions, and does 対応履歴 inherit them? | Needed to design 経理 read access (REQ-010…012) |
| PO5 | Q1–Q7 (2026-11-05) are still unconfirmed by the customer. Send them together with Q8–Q25? | One mail to the customer |
