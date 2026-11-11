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
| REQ-007 | カテゴリ offers 契約 and 請求 instead of 契約・請求 | ubiquitous | G1 approved |
| REQ-008 | Past 契約・請求 inquiries are counted under 契約 or 請求 | ubiquitous | G1 approved |
| REQ-009 | AI: 推定カテゴリ uses the new categories | ubiquitous (derived) | G1 approved |
| REQ-010 | 経理チーム can view billing inquiries | state-driven | G1 approved |
| REQ-011 | 経理チーム can view the 対応履歴 of billing inquiries | state-driven | G1 approved |
| REQ-012 | 経理チーム cannot change inquiries or 対応履歴 | unwanted behaviour | G1 approved |
| REQ-013 | 対応時間 can be recorded on each 対応履歴 (in existing 作業時間) | ubiquitous | G1 approved (revised) |
| REQ-014 | 合計対応時間 per inquiry | ubiquitous | G1 approved |
| REQ-015 | 対応回数 keeps working | ubiquitous (derived) | G1 approved |

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

## Change request 2026-11-05 — customer mail (佐藤様): カテゴリ見直し・経理チーム共有・対応時間

Source: `sources/2026-11-05-customer-mail-category-accounting-time.md` (mail from 佐藤様, みなと商事 カスタマーサポート課, received 2026-11-05).

**G1** by Nam (tech lead / PM), 2026-11-05: REQ-007…015 approved with **all assumptions Q8–Q22 accepted as written** (incl. Q14: 経理 may view all inquiries and 対応履歴, read-only). The questions stay open for the customer's confirmation; a different answer becomes a change request.

| Mail item | Requirements |
|---|---|
| 1. カテゴリの見直し | REQ-007, REQ-008, REQ-009 (derived) |
| 2. 経理チームへの共有 | REQ-010, REQ-011, REQ-012 |
| 3. 対応時間の記録 | REQ-013, REQ-014, REQ-015 (derived) |
| Deadline 12/10, no weekday daytime stop | constraints C1, C2 (not EARS requirements) |

### Constraints (from the mail — release planning, not system behaviour)

| # | Constraint | Question |
|---|---|---|
| C1 | Usable by **2026-12-10** (monthly closing). P1 date 2026-11-05 → about 5 weeks incl. G1–G4 and the customer's stg check. | Q22 (priority if not all fits) |
| C2 | Avoid work that stops the app on **weekdays during the day** (used daily). Applies to every stg/prod release and to the data change of REQ-008. | Q21 (allowed window) |

### Impact analysis (site `inquiries`, current `config/`; site `responses` not in git)

| Element | Impact | Recorded as |
|---|---|---|
| カテゴリ (ClassD) choices | 契約・請求 → 契約, 請求 | REQ-007 |
| Records holding カテゴリ 契約・請求 | value no longer a choice → orphan (D11, D12); customer wants past data in new categories | REQ-008 (Q9, Q10) |
| AI: 推定カテゴリ (ClassF) choices and `ai1` allowed list / instruction text (契約・請求) | AI would keep proposing a removed category | REQ-009 (derived); past AI values Q12 |
| Views 1–3, Aggregation (by 状況), crosstab 状況×チャネル | none filter or group by カテゴリ | none |
| `FilterColumns` / `GridColumns` / `LinkColumns` (ClassD) | new choices appear automatically | none |
| Notification #1, process `escalate` (incl. its mail), Reminder 1 | do not depend on カテゴリ or on permissions of new readers | none |
| REQ-001…005 (escalation, 緊急) | no conflict. 経理 has no edit right → cannot escalate; consistent with Q1 (escalation = users with edit rights) | REQ-012 AC4 |
| Permissions (`permissions.json`: inherit + admin) | new read-only principal 経理チーム on `inquiries` and `responses`; existing entries must stay | REQ-010 AC4, REQ-011, REQ-012 (Q13, Q14, Q15) |
| Site `responses` (対応履歴): link 問い合わせ番号, 状況 予定/完了, columns 対応日時/対応種別/件名/対応内容 (known only from `ai1`) | new column 対応時間; read access for 経理 | REQ-011, REQ-013 |
| 対応回数 (NumA, read-only) on `inquiries` | no writer in `inquiries` config → presumably maintained from `responses`; at risk when `responses` is updated (D4) | REQ-015 (derived) |
| New column 合計対応時間 on `inquiries` | grid, filter, editor layout, export, slot ledger | REQ-014 |
| `ai1` related-records block (reads `responses` by ClassA) | unaffected by an added column; affected if the link changes | REQ-015 AC3 |
| Crosstab view 3 (`CrosstabValue` NumA, Count) | counts records, not NumA values → unaffected | none |

### Engineering prerequisites / unverified Pleasanter behaviour (for P2, not customer questions)

| # | Point |
|---|---|
| P-1 | `responses` (対応履歴) is **not a managed site**: no `config/responses/`, not in `managed_sites`. Before P2: export dev and stg, unpack, run drift, add to `managed_sites`, create its slot ledger. Without this, any `updatesite` on it would delete its current settings (D4). |
| P-2 | Child-to-parent sum (Summaries/集計) incl. recalculation on update and delete — **not in `pls-kb-pleasanter`**; probe on dev (REQ-014). |
| P-3 | Read-only permission value, error returned on a refused write, and record-level (per category) restriction — **not in `pls-kb-pleasanter`**; probe on dev (REQ-010…012, Q14). |
| P-4 | How 対応回数 is maintained today — unknown; establish from the `responses` export (REQ-015). |
| P-5 | Number of records with カテゴリ 契約・請求 on stg/prod — unknown (no environment reachable in P1); needed to size REQ-008 against C1. |

### お客様への確認事項 (open questions)

| # | Question (日本語) | Assumption |
|---|---|---|
| Q8 | 新しいカテゴリの並び順は「操作方法・不具合・契約・請求・機能要望・その他」（「契約・請求」があった位置に「契約」「請求」の順）でよろしいですか？ | [assumed] はい (REQ-007) |
| Q9 | 過去の「契約・請求」の問い合わせは、どなたがどの基準で「契約」「請求」に振り分けますか？ | [assumed] MADLABが件名・内容から振り分け案の一覧を作成し、お客様が確認・修正した一覧のとおりに一括で更新する。判断できないものもお客様が決める (REQ-008) |
| Q10 | 過去分の振り分け（「できれば」とのこと）は、12月10日の締めまでに必要ですか？ | [assumed] 必要 — 11月分の締めから新しいカテゴリで集計する (REQ-008) |
| Q11 | カテゴリ別の集計は現在どのように行っていますか（一覧の絞り込み、Excel出力など）？ 集計用の新しい画面は必要ですか？ | [assumed] 既存の一覧の絞り込み・出力で集計する。新しい集計画面は追加しない (REQ-008, REQ-010) |
| Q12 | AIの「推定カテゴリ」も「契約」「請求」を分けて推定してよいですか？ また、過去の問い合わせに残っているAIの推定値「契約・請求」はそのままでよいですか？ | [assumed] はい（分けて推定する）／過去のAI推定値は変換せずそのまま残す (REQ-009) |
| Q13 | 経理チームの方はPleasanter上でどのグループ（または組織）に登録されていますか？ 対象となる方の範囲を教えてください。 | [assumed] お客様がPleasanterに「経理」グループを用意し、権限はグループ単位で付与する (REQ-010…012) |
| Q14 | 経理チームの方に、請求以外の問い合わせ・対応履歴が見えても問題ありませんか？ | [assumed] 問題ない（すべて閲覧のみ可）。請求のみに限定する場合はPleasanterでの動作確認が必要で、期限に影響する可能性があります (REQ-010, REQ-011) |
| Q15 | 経理チームの方は、コメントの書き込みや添付資料の閲覧・ダウンロードを行いますか？ | [assumed] コメントは書き込まない（見るだけ）。添付資料は閲覧・ダウンロード可 (REQ-012) |
| Q16 | 対応時間はどの単位で入力しますか（分／時間、15分単位など）？ | [assumed] 分単位の整数（0以上） (REQ-013) |
| Q17 | 対応時間は必須入力にしますか？ | [assumed] 任意入力。未入力は0分として合計する (REQ-013, REQ-014) |
| Q18 | 状況が「予定」の対応履歴に入力された対応時間も、合計に含めますか？ | [assumed] 含める（状況に関係なく入力済みの対応時間をすべて合計） (REQ-014) |
| Q19 | すでに登録済みの対応履歴（11月分など）にも対応時間を入力する必要がありますか？ 12月10日の締めでは11月分の報告に対応時間を使いますか？ | [assumed] 過去分はさかのぼって入力しない（必要なら現場で手入力）。合計対応時間は公開後に入力された分から使える (REQ-013, REQ-014) |
| Q20 | 月次報告では、合計対応時間をどの単位でまとめますか（月別・カテゴリ別など）？ 画面上での月別集計は必要ですか？ | [assumed] 問い合わせごとの合計を一覧・出力で確認し、月別のまとめはお客様側で行う。新しい集計画面は追加しない (REQ-014) |
| Q21 | 設定変更の作業は、どの時間帯なら実施してよいですか（平日何時以降、土日祝など）？ | [assumed] 平日19:00以降または土日祝に実施し、作業日時は事前にご連絡する (C2) |
| Q23 | 対応履歴にはすでに「作業時間（分）」があり、これまでの対応履歴すべてに入力されています。ご依頼の「対応時間」はこの作業時間のことでよろしいですか？ | [assumed] はい — 合計対応時間は作業時間の合計 (REQ-013, REQ-014) |
| Q22 | 3つのご依頼はすべて12月10日までに必要ですか？ 間に合わない場合の優先順位を教えてください。 | [assumed] すべて12月10日まで。間に合わない場合は 1.カテゴリ → 3.対応時間 → 2.経理共有 の順 (C1) |

### P2 prerequisites — results (2026-11-05, read-only)

| # | Result |
|---|---|
| P-1 | Site `responses` exported from dev 44566 / stg 44574 (SHA-256 verified), unpacked to `config/responses/`, added to `managed_sites`, slots recorded in the ledger. Live stg = git: 0 differences. |
| P-4 | 対応回数 (`inquiries.NumA`) is maintained by **Summary #1 on `responses`** (Type Count, link ClassA → inquiries NumA). Changing `responses` must keep this Summary (REQ-015). |
| P-5 | Original demo data (42410/42411, counted only): 100 inquiries, **7 with カテゴリ 契約・請求**; AI 推定カテゴリ empty on all. dev/stg copies hold test records only. |
| **New** | `responses` **already has 作業時間 (NumA, unit 分)** on the editor and the list, filled on **all 100** 対応履歴 (6,320 min). REQ-013 as approved would add a second time column. **Raised back to G1** — not absorbed in P2. |

**G1 decision (Nam, 2026-11-05): REQ-013 revised as proposed; Q23 added ([assumed] yes).** Proposed text:
- **REQ-013 (revised)** — "The 対応履歴 site shall let the support staff record the 対応時間 of each 対応履歴 record **in the existing 作業時間 (分)**." Acceptance: unchanged entry of 作業時間; no new column.
- **Q23** 対応履歴にはすでに「作業時間（分）」があり、これまでの対応履歴すべてに入力されています。ご依頼の「対応時間」はこの作業時間のことでよろしいですか？ — [assumed] はい。合計対応時間は作業時間の合計とする (REQ-013, REQ-014).
- Q16/Q17/Q19 become largely moot (unit = 分, already filled, past data exists → 11月分の合計も出せる).

### Raised from P2 (2026-11-11) — awaiting G1, not part of the approved scope

| # | Item | From |
|---|---|---|
| DR-1 | **Derived requirement (proposed REQ-016):** The エスカレーション button of 問い合わせ管理 shall be shown to, and executable by, only the members of the support group and admin; members of the 経理チーム shall not see it. Reason: a read-only role still sees process buttons (D19), so REQ-012 AC5 needs process access control, which also limits the existing editors who are not in that group (changes Q1 "anyone with edit rights"). If rejected: REQ-012 AC5 must be changed to "button may show; pressing is refused". | DES-004 |

お客様への確認事項 (new):

| # | Question (日本語) | Assumption |
|---|---|---|
| Q24 | 経理チームの方には「エスカレーション」ボタンを表示しないようにするため、ボタンを押せる人をグループで指定します。エスカレーションを行うサポート担当の方が所属するグループはありますか？ ない場合、「サポート担当」グループを作成してよいですか？ | none — needs G1 with DR-1 |
| Q25 | 合計対応時間を過去の問い合わせにも表示するため、公開時に各問い合わせの対応履歴を1件ずつ再保存します（内容は変わりません）。その対応履歴の「更新日時」「更新者」が作業日時・作業者に変わりますが、問題ありませんか？ | [proposed] 問題ない (DES-005 M2) |

