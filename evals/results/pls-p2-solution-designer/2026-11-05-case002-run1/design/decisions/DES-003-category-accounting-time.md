# DES-003 — カテゴリ split, read-only access for 経理チーム, 合計対応時間

- **Status:** awaiting G2 (not approved — designer does not approve, I4)
- **Requirements:** REQ-007, REQ-008, REQ-009 (カテゴリ) · REQ-010, REQ-011, REQ-012 (経理チーム) · REQ-013, REQ-014, REQ-015 (対応時間) — all G1 approved 2026-11-05, REQ-013 as revised; assumptions Q8–Q23 as accepted at G1.
- **Sites:** `inquiries` (問い合わせ管理) and `responses` (対応履歴).
- **Change classification (ADR-0004):** **data-impacting** and **permission-impacting** (details in § Classification):
  - data-impacting — the カテゴリ choice 契約・請求 is removed while records hold it (D11, D12) and 7 records (P-5) are rewritten (migration M1); a new Summary is added on `responses`, which does not fill existing parents (D16, migration M2);
  - permission-impacting — a new read-only principal 経理チーム is added to the permissions of `inquiries` (inherited by `responses`).

## Ladder (I5)

Highest rung: **3**, only for the *existing* AI server script `ai1` (DES-000), which is changed in its data (choice list and instruction text), not in its logic. Everything new is rung 1 (choices, column, layout, permissions) or rung 2 (Summary = computed value across the link). Reason for touching rung 3: the AI first response already exists as a server script (external AI call through the gateway, DES-000); its allowed category list is hard-coded in it, so REQ-009 cannot be met without editing it. No new script, no extended SQL, no external integration.

## Design

### A. カテゴリ (REQ-007, REQ-008, REQ-009) — site `inquiries`

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| A1 | `Columns[ClassD].ChoicesText` (カテゴリ) | `操作方法\n不具合\n契約\n請求\n機能要望\nその他` (契約・請求 replaced in place by 契約, 請求 — order Q8) | REQ-007 | 1 |
| A2 | Data migration M1 | rewrite カテゴリ 契約・請求 → 契約 / 請求 on each affected inquiry, per the reclassification list agreed with the customer (Q9); see § Migration M1 | REQ-008 | data (API) |
| A3 | `Columns[ClassF].ChoicesText` (AI: 推定カテゴリ) | identical to A1: `操作方法\n不具合\n契約\n請求\n機能要望\nその他` | REQ-009 | 1 |
| A4 | Server script `ai1` — `CONF.outputs[key=category]` | `allowed` = `["操作方法","不具合","契約","請求","機能要望","その他"]`; `instruction` = `カテゴリ（操作方法/不具合/契約/請求/機能要望/その他 のいずれかの文字列）`. Change it in the generator's source `spec.json` and regenerate `ai1.js` (the header says hand edits are overwritten); the existing guard (`allowed.indexOf(v) < 0 → return`) is kept, so 契約・請求 from the AI is never written (REQ-009 AC2). Nothing else in `ai1` changes (status map, `related` block, timeout). | REQ-009 | 3 (existing script, DES-000) |
| A5 | Past AI values | ClassF values 契約・請求 are left as they are (Q12); they become orphan values (D12). P-5: ClassF is empty on all 100 original records, so in practice none exist | REQ-009 AC4 | — |

Nothing else in `inquiries` refers to カテゴリ (views, aggregation, notification, reminder, process) — see impact table. `FilterColumns`, `GridColumns`, `LinkColumns` already contain ClassD/ClassF; the new choices appear there without a change.

### B. 経理チーム read-only (REQ-010, REQ-011, REQ-012) — permissions

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| B1 | Principal `accounting` | logical name in `environments.json` → `principals`: `"accounting": "Group,<id>"` per environment; the group 「経理」 is created by the customer (Q13). Never a raw ID in `config/` (L-PERM-01) | REQ-010…012 | 1 |
| B2 | `config/inquiries/permissions.json` (new file, opt-in ADR-0006) | `inherit` and **all existing entries exactly as exported** (prerequisite D-1), plus one entry `${principal:accounting},<READ-ONLY VALUE>`. The read-only value is **not in `pls-kb-pleasanter`** (only 511 = all rights is): it is taken from probe PR-A and added to the KB; P3 cannot complete B2 before that. | REQ-010, REQ-012 | 1 |
| B3 | `config/responses/permissions.json` | **unchanged** — `inherit: ${site:inquiries}`, no own entries. 経理 reaches 対応履歴 through inheritance from `inquiries` (to be confirmed by PR-A, see below) | REQ-011, REQ-012 | 1 |
| B4 | Record scope | **none** — 経理 sees all inquiries and all 対応履歴, read-only (Q14 accepted at G1). Billing inquiries are found with the existing カテゴリ filter (REQ-010 AC2; no new view, Q11) | REQ-010 AC2–3, REQ-011 AC3 | 1 |
| B5 | Process `escalate` | **no change planned.** Expected: 経理 has no update right, so the button is not offered and the API execution is refused. This is **not in the KB** (impact checklist refers to D19/D20, which are not present in `behaviours.md`) → PR-A decides. If PR-A shows the button to 経理 or lets it execute, the process needs access control (`Processes[escalate].Groups/Users/Depts` with `${principal:…}`), which requires the principals of everyone who *may* escalate (Q1 assumed "anyone with edit rights") → raised back to P1/G1 as a derived requirement, not absorbed here | REQ-012 AC4–5 | (2) |

#### Who can see and press what (permission-impacting, D19/D20 checklist item)

| Role | 問い合わせ管理 | 対応履歴 | Buttons it can press | Change |
|---|---|---|---|---|
| support staff (existing edit principals) | view/create/edit as today | as today (inherited) | 保存, 削除 (as today), エスカレーション within its display condition | none — entries copied unchanged (REQ-010 AC4) |
| サポート責任者 / admin (`User,1`) | as today | as today | as today | none |
| **経理チーム** (new) | list + edit screen, read-only; all categories | list + open, read-only (inherited) | **none expected**: no 保存/削除/作成, no エスカレーション (PR-A); attachments open/download yes, comments no (Q15, PR-A) | new entry B2 |

P4 test plan (TD-11): a 経理 test user in the 「経理」 group on dev (and the customer's check on stg) executes every REQ-010…012 criterion through the API **as that user** and checks the screen (REQ-012 AC5), on a record that is *inside* the `escalate` display condition (優先度 高, 状況 100) so the button check is meaningful.

### C. 対応時間 (REQ-013, REQ-014, REQ-015)

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| C1 | `responses.Columns[NumA]` 作業時間 (分) | **unchanged** — already on editor, grid and link columns; optional (REQ-013 revised, Q23) | REQ-013 | 1 (existing) |
| C2 | New column `inquiries.Columns[NumB]` | `LabelText` 合計対応時間, `Unit` 分, `EditorReadOnly: true` (REQ-014 AC6 — screen only, D17) | REQ-014 | 1 |
| C3 | `inquiries` layout | `EditorColumnHash.General`: NumB right after NumA (対応回数). `GridColumns`: NumB right after NumA. `FilterColumns`: add NumB (REQ-014 AC7) | REQ-014 | 1 |
| C4 | New Summary on `responses` | `Summaries[Id 2]`: `{Type: "Total", SourceColumn: "NumA", LinkColumn: "ClassA", SiteId: "${site:inquiries}", DestinationColumn: "NumB", DestinationReferenceType: "Results"}` — exactly the shape verified in D16: every child create/update/delete recomputes the full total for that parent, empty = 0 (AC1–4); no condition, so 予定 and 完了 are both summed (AC5, Q18). Final form after `pls canon` / dev export (D8) | REQ-014 | 2 |
| C5 | Existing Summary `responses.Summaries[Id 1]` (Count → `inquiries.NumA` 対応回数) | **kept byte-identical**, together with `Links[ClassA]` and `Columns[ClassA]` (link 問い合わせ). `updatesite` replaces everything (D4): P3 deploys the complete unpacked `responses` configuration + C4 only | REQ-015 | 1 (existing) |
| C6 | Data migration M2 | after the release, touch one 対応履歴 per inquiry so that NumB is filled for existing data (D16); see § Migration M2 | REQ-014 (past data, Q19 superseded) | data (API) |

### Slots (A2, ADR-0002)

- `inquiries.NumB` — first Num slot never allocated in the ledger (NumA is 対応回数). **P3 must confirm it is empty/unused in every environment's export** (dev 44565, stg 44573 and the customer's production site) with `pls slots` before deploying; if it is used anywhere, take the next never-allocated slot and update ledger + this design.
- `responses`: no new slot. Its existing slots (ClassA, ClassB, DateA, NumA, AttachmentsA) are recorded in the ledger from the P-1 export (they were missing — L-SLOT-01).

## Rejected alternatives

- **Keep 契約・請求 next to 契約 and 請求** — violates REQ-007 AC2.
- **Migrate M1 before changing the choices** — writing a value that is not (yet) a choice through the API is not described in `pls-kb-pleasanter`; changing choices first and migrating in the same window only relies on D12 (removed choice keeps stored values) and D13/D18.
- **Customer re-categorises the 7 records by hand on screen** — workable for 7 records, but Q9 (accepted) specifies a list-based bulk update, and manual edits leave no backup/dry-run evidence. Kept as fallback only if the count turns out to be very small on the target and the customer prefers it.
- **Converting past AI: 推定カテゴリ values** — Q12: left unchanged.
- **Let `ai1` read the カテゴリ choices from the site settings at run time** — more script logic at rung 3 and no KB entry on reading SiteSettings from a server script; a static list kept equal to ClassD is enough (REQ-009 AC1 checks equality).
- **Restrict 経理 to 請求 records only** (record-level permission) — not required (Q14); not in the KB; would need its own probe and threatens C1.
- **Own permission entries on `responses` (stop inheritance)** — the site already inherits from `inquiries`; a second, separately maintained list doubles the drift surface. Only becomes necessary if PR-A shows that inheritance does not give 経理 read access.
- **Change the parent folder's permissions** (if `inquiries` itself inherits) — would grant 経理 access to every sibling site; not allowed without a new decision (see D-1).
- **A new 「請求」 view for 経理** — not requested (Q11/Q14 assumptions: existing filter); adding it would be gold-plating.
- **New 対応時間 column on `responses`** — rejected at G1 (REQ-013 revised; 作業時間 exists and is filled).
- **Server script summing 作業時間 into the inquiry (AfterCreate/AfterUpdate/AfterDelete)** — rung 3 without need: the standard Summary (D16) recomputes on create, update and delete, and is configuration the customer can read.
- **Formula column on `inquiries`** — the KB has no entry for a formula that reads child records; not relied upon.
- **Writing NumB values directly in M2 (bulkupsert of computed totals)** — would be overwritten by the Summary anyway and duplicates logic; touching a child (D16) uses Pleasanter's own computation.

## Impact analysis (`impact-checklist.md`, current `config/`)

| Existing element | Impact | Action |
|---|---|---|
| inquiries: records with カテゴリ 契約・請求 (7 on original data, P-5) | orphan values after A1 (D11, D12) | M1 (REQ-008) in the same window |
| inquiries: ClassF records with 契約・請求 | orphan values (D12) | none — Q12; 0 records on original data |
| inquiries: Views 1 標準, 2 未完了, 3 状況×チャネル (crosstab Count) | no filter/group on ClassD, ClassF, NumB; crosstab counts records | none |
| inquiries: Aggregation (GroupBy Status) | unaffected | none |
| inquiries: `FilterColumns` / `GridColumns` / `LinkColumns` | ClassD/ClassF show the new choices automatically; NumB added to grid and filters (C3) | C3 |
| inquiries: `EditorColumnHash.General` | NumB inserted after NumA | C3 |
| inquiries: Notification #1 (`[Manager]`, monitors Status, ClassE, condition view 2) | not affected by カテゴリ, NumB or new readers. M1 changes only ClassD; whether a bulk API update triggers it is observed in the M1 dry run (`AfterBulkUpdate` is false) | observe in dry run |
| inquiries: Reminder 1 (DateB, to `[Owner]`) | unaffected; 経理 is never Owner | none |
| inquiries: Process `escalate` (display condition, data change DateC, mail to `[Manager]`) | 経理 must not see/press it (REQ-012 AC4–5) — expected from missing update right, **unverified** | PR-A; access control only via derived requirement (B5) |
| inquiries: Server script `ai1` | category list/instruction (A4). `related` block reads `responses` by ClassA — link unchanged (REQ-015 AC3). Runs only on save with CheckA = on → 経理 (read-only) cannot trigger it; M1 must not carry CheckA = true (pre-check D-3) | A4 |
| inquiries: Server script `aiEnv` (shared) | unchanged | none |
| inquiries: Column NumA 対応回数 | still written by Summary #1 | C5 (REQ-015) |
| inquiries: permissions (not in git today) | new entry for 経理; existing entries must stay identical (REQ-010 AC4) | D-1, B2 |
| responses: permissions (inherit from inquiries) | 経理 gains read through inheritance | B3, PR-A |
| responses: Summary #1 (Count → NumA) | must survive the full-replacement update (D4) | C5 |
| responses: Summary #2 (new) | fills NumB on every child change; existing parents stay empty until touched (D16) | M2 |
| responses: Views 1–3, Aggregation, Links, Columns | unchanged (crosstab view 3 counts records) | none |
| responses: `managed_sites` | `environments.json` still lists only `inquiries`, while `index.md` (P-1) says `responses` was added | P3 prerequisite D-4 |
| D17 — NumB is read-only on screen only | API clients or Excel/CSV imports into `inquiries` could overwrite 合計対応時間 | tell the customer; after any import touching NumB, recompute with M2 procedure |
| Child save → parent recalculation also rewrites NumA (Count) | same values as before (REQ-015) | P4 before/after comparison (REQ-015 AC1–2) |
| Records' 更新日時/更新者 | change on the 7 M1 records and on one 対応履歴 per inquiry in M2 (D16) | tell the customer before the window |
| Derived requirements raised | none new at this point. Conditional: process access control for `escalate` if PR-A shows the button to 経理 (→ P1/G1 with Q1) | — |

## Classification

| Group | Class | Reason |
|---|---|---|
| A — カテゴリ | **data-impacting** | a choice used by records is removed (D11; `pls classify` flags any choice removal) and record values are rewritten (M1). ClassF choice removal is flagged too but needs no migration (Q12, 0 records) |
| A4 — `ai1` | config-only | script data change, no record touched |
| B — 経理 | **permission-impacting** | new principal entry on `inquiries`, inherited by `responses`; no existing entry changes |
| C — 対応時間 | **data-impacting** | new Summary does not recalculate existing parents (D16) → M2; new column NumB in a never-used slot |
| **Overall** | **data-impacting (+ permission-impacting)** | migrations M1 and M2 needed; migration folders (`migration.json` with site/keys/rollback, `backup/`, `dry-run.md`) are required by `pls release-plan --migration` |

## Migration M1 — カテゴリ 契約・請求 → 契約 / 請求 (REQ-008)

1. **List (before the window):** MADLAB exports the inquiries with カテゴリ 契約・請求 (問い合わせ番号, 件名, 内容) and proposes 契約/請求 per record; the customer confirms or corrects every line, including the undecidable ones (Q9). The confirmed list is the input `migration.json` (`site: inquiries`, `keys: ["ClassA"]`, data `[{ClassA, ClassD}]`, `rollback`).
2. **Pre-checks on the target (D-3), at window start:** count of 契約・請求 = list length (records not in the list → stop, ask the customer; do not guess); every ClassA in the list is unique across the whole site (D18 — otherwise 400 and nothing is updated); CheckA is not on for any of them (otherwise `ai1` would call the AI on update).
3. **Backup:** `backupRecords` of all affected records, full columns (API updates create no versions, D14).
4. **Dry run on a copy (dev)** with the same records: `bulkupsert` with `Keys: ["ClassA"]` and only `ClassA` + `ClassD` (D13, D18 — other columns kept). Record in `dry-run.md`: other fields unchanged, ClassH (AI実行記録) unchanged, Notification #1 not sent, `UpdatedTime` changed.
5. **Window (C2/Q21: weekday after 19:00 or 土日祝, announced beforehand):** deploy `inquiries` (A1, A3, A4, plus C/B parts if in the same release) → run M1 → verify REQ-008 AC1–4 (count 契約・請求 = 0; sum check; sample vs list).
6. **Rollback:** `bulkupsert` the backup values (ClassD = 契約・請求) and redeploy the previous `inquiries` configuration. Once users have created new records with 契約 or 請求, a rollback would orphan them (D11) → rollback only within the window; afterwards it needs its own decision.

## Migration M2 — fill 合計対応時間 for existing inquiries (REQ-014)

1. **After** the `responses` deploy with Summary #2 (and `inquiries` with NumB), from a backup of `responses` records (`backupRecords`): for each distinct ClassA (parent inquiry), choose one 対応履歴 and `update` it with its current 作業時間 unchanged — D16: this recomputes the parent's full total (and the Count into NumA, which must stay equal).
2. **Dry run on dev** with copied data; record before/after NumA and NumB for every parent in `dry-run.md`.
3. **Verify:** for every inquiry, NumB = Σ 作業時間 of its 対応履歴 (computed from the backup); NumA unchanged (REQ-015 AC1). Inquiries without 対応履歴 keep NumB empty (REQ-014 AC4 allows empty).
4. Side effect: the touched 対応履歴 get a new 更新日時/更新者 (D16) — announce to the customer.
5. **Rollback:** remove Summary #2 and NumB from the layout (redeploy previous configuration of both sites). NumB keeps its values (D12) and the slot is **burnt** (never reused, ledger stays `allocated`).

## Probes and discovery (not run — no environment reachable; to be run on **dev** only)

| Id | Contents (the combination the design relies on) | Result that changes the design |
|---|---|---|
| **D-1** read-only discovery | `getsite` on `inquiries` and `responses` in dev, stg and the customer site: `InheritPermission`, `Permissions`; unpack to `config/inquiries/permissions.json` with every principal mapped in `environments.json` | `inquiries` inherits from a parent folder → adding 経理 there would also open sibling sites → stop, design decision (stop inheritance on `inquiries` and copy entries, or customer accepts folder-level grant) back to G2. Unmapped principals → map them before P3 (L-PERM-01) |
| **PR-A** permissions | dev: group 「経理」 with one test user; entry on `inquiries` (44565) with the read-only preset as set by the UI; `responses` (44566) still inheriting. Records: inquiry カテゴリ 請求, **優先度 高, 状況 100 (inside the `escalate` display condition)**, with an attachment and two 対応履歴; one inquiry of another category. As the test user: list/open both sites; API `get`, `update`, `create`, `delete` on both sites; `update` with `ProcessId` of `escalate`; add a comment; download the attachment; screen check for 保存/削除/エスカレーション. Record the stored permission value and the HTTP status of refusals, add to the KB. Restore dev afterwards | (a) 対応履歴 not readable via inheritance → own entries on `responses` (B3 changes; permission design back to G2). (b) エスカレーション shown or executable → process access control needed → derived requirement to P1/G1 (B5). (c) comment possible / attachment not downloadable → conflicts with Q15 → raise to customer/G1. (d) no single read-only preset → define the bit value explicitly and add to KB |
| **PR-B** two Summaries on one child site | dev `responses` with Summary #1 (Count → NumA) **kept** and Summary #2 (Total NumA → NumB) added; existing children present. Create two children (30, 45), change one to 60, delete one; check NumA and NumB after each step; check a pre-existing parent stays empty until one child is touched; export and unpack the site to get the canonical form of Summary #2 (D8) | NumA (Count) altered or no longer updated → C4 cannot coexist with Summary #1 → stop, back to G2 (REQ-015 has priority). NumB not recomputed on delete → REQ-014 AC3 fails → new decision (only then consider rung 3 with a written reason) |
| **D-2** slot check | `pls slots` on exports of every environment for `inquiries` | NumB used somewhere → next never-allocated Num slot |
| **D-3** migration pre-check | on the target before the window: count 契約・請求, ClassA uniqueness, CheckA on affected records | count ≠ list → customer decides the rest; duplicates → key change or split batch; CheckA on → exclude/clear first |
| **D-4** managed site | `environments.json` `managed_sites` must include `responses` (P-1 says it does, the file does not) | without it the release tooling does not handle `responses` → fix in P3 before planning |

## Release sequencing (proposal for P5)

All work in the C2 window. Groups are independent and can ship separately in the C1 priority order (Q22): **R1 カテゴリ** (A + M1) → **R2 対応時間** (C + M2; `responses` and `inquiries` in one multi-site release, referenced site first) → **R3 経理** (B, after D-1 and PR-A). One combined release is also possible if all prerequisites are ready.

## Open points

- PR-A, PR-B, D-1…D-4 must be run (and the KB updated) before P3 completes the affected elements; B2 cannot be written without the read-only value.
- Location of the `ai1` generator source `spec.json` (not in this repository) — P3 must change it, not only `ai1.js`.
- Principal 「経理」 group id per environment (Q13) — needed in `environments.json` before pack.
- Production/customer site is not in `environments.json` (only dev/stg); the 7-record count is from the original data 42410/42411 and must be recounted on the real target (D-3).
- Export of NumB (REQ-014 AC7) uses the standard list export; the KB has no entry on which columns the export includes — P4 checks it.
- Customer questions Q8–Q23 remain open for confirmation; a different answer is a change request.
- Customer to be told: 更新日時/更新者 changes from M1/M2; NumB can be overwritten by imports/API (D17).
