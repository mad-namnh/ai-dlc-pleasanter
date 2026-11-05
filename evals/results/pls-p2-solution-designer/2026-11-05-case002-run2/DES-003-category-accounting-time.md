# DES-003 — カテゴリ split, read-only 経理チーム, 合計対応時間

- **Status:** awaiting G2 (not approved — I4). **Two G2 prerequisite probes (PRB-1, PRB-2) have not been run** (no environment reachable in this P2 session); see "Probes".
- **Requirements:** REQ-007, REQ-008, REQ-009 (カテゴリ) · REQ-010, REQ-011, REQ-012 (経理チーム) · REQ-013, REQ-014, REQ-015 (対応時間) — all G1 approved 2026-11-05 with Q8–Q23 as assumed.
- **Sites:** `inquiries` (問い合わせ管理), `responses` (対応履歴).
- **Change classification (ADR-0004):** **data-impacting** *and* **permission-impacting**.
  - data-impacting: choice 契約・請求 is removed from カテゴリ (ClassD) and AI: 推定カテゴリ (ClassF) while records hold it (D11, D12); REQ-008 rewrites record values; a new Summary does not recalculate existing parents (D16). → migration M-1 and M-2 below.
  - permission-impacting: new principal 経理チーム (read-only) on `inquiries`, reaching `responses` through its inherited permissions; process `escalate` gets process access control.
  - Note for P5: `pls classify` recognises Summaries and removed choices as data-impacting, but classifies `Processes[].Groups` as config-only (it only matches `permissions*`/`AccessControl` paths). The classification above is authoritative.

## Ladder (I5)

| Rung | Elements | Reason if ≥ 3 |
|---|---|---|
| 1 | ClassD / ClassF choices, column `inquiries.NumB` + editor/grid/filter placement, site permissions, no change to `responses.NumA` | — |
| 2 | Summary #2 (child→parent total), process access control on `escalate` | — |
| 3 | `ai1` server script (existing, DES-000) — only its allowed category list and instruction text change | The AI call itself is rung 3 for the reason in DES-000 (external AI via gateway). The list of allowed values lives inside the script's `CONF`; nothing in `pls-kb-pleasanter` lets the script read ClassF's choices from the site settings, so the list is changed in place. No new code path, no new script. |

Migrations M-1/M-2 are one-off P5 operations through the record API (runner), not configured mechanisms.

## Design

### A. カテゴリ (REQ-007, REQ-008, REQ-009)

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| A1 | `inquiries` `Columns[ClassD].ChoicesText` (カテゴリ) | **final:** `操作方法\n不具合\n契約\n請求\n機能要望\nその他` (Q8 order). **release step 1 (transitional, additive):** `操作方法\n不具合\n契約\n請求\n契約・請求\n機能要望\nその他` | REQ-007 | 1 |
| A2 | `inquiries` `Columns[ClassF].ChoicesText` (AI: 推定カテゴリ) | same as A1 in both steps (REQ-009 AC1: identical content and order) | REQ-009 | 1 |
| A3 | `ai1` `CONF.outputs[key=category]` | `allowed: ["操作方法","不具合","契約","請求","機能要望","その他"]`; `instruction: "カテゴリ（操作方法/不具合/契約/請求/機能要望/その他 のいずれかの文字列）"`. Existing guard `allowed.indexOf(...) < 0 → return` is kept (REQ-009 AC2). Change the **generator source (`spec.json` `ai`)** and regenerate — the file header says manual edits are overwritten; `spec.json` is not in this repository (open point O-6). | REQ-009 | 3 (existing) |
| A4 | Migration **M-1** | reclassify every inquiry with ClassD = 契約・請求 to 契約 or 請求 per the customer-confirmed list (Q9). Detail under "Migration". | REQ-008 | — |

Release sequencing (D11/D12): step 1 adds 契約 and 請求 next to 契約・請求 → M-1 writes only values that are valid choices → step 2 removes 契約・請求. At no time does a record hold a value that is not a choice, and nothing relies on the API accepting a value outside `ChoicesText` (not in the KB).

Past AI values: inquiries whose ClassF holds 契約・請求 keep it (Q12, REQ-009 AC4). After step 2 the value is kept but shown as an orphan option on the edit screen (D12). P-5: 0 such records in the original data; counted again per environment before step 2.

### B. 経理チーム read-only (REQ-010, REQ-011, REQ-012)

Q14 accepted: 経理 may view **all** inquiries and 対応履歴 read-only. Therefore no record-level (per-category) restriction is designed and none is probed.

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| B1 | `inquiries` site permissions | add `${principal:keiri},<READ>` to the entries; every existing entry and `inherit` unchanged (REQ-010 AC4). `<READ>` = the value Pleasanter stores for the UI pattern 「読み取り」(read only) — **not in the KB** (only 511 = all rights is), taken from PRB-2. `config/inquiries/permissions.json` does not exist yet: P3 must first unpack it **from the live export** (opt-in, ADR-0006, D15) — never hand-write it — so the existing inheritance and entries are preserved. | REQ-010, REQ-012 | 1 |
| B2 | `responses` site permissions | **no change**: `inherit: ${site:inquiries}`, `entries: []`. 経理 reaches 対応履歴 through the inheritance from `inquiries` (that is how all current users reach it — `responses` has no own entries). Confirmed by PRB-2; fallback below. | REQ-011, REQ-012 | 1 |
| B3 | `environments.json` principals | add `keiri` (Group, Q13 — the customer creates the 経理 group in every environment) and every principal that today holds update rights on `inquiries` (from PRB-1), per environment. Raw IDs are never written into config (L-PERM-01). | REQ-010…012 | — |
| B4 | Process `escalate` access control (`Processes[escalate].Groups` / `.Users` / `.Depts`, property per tool `acl_to_refs`, 1.5.2 PR-4) | the `${principal:x}` of **every principal with update rights on `inquiries`** (from PRB-1), **not** `keiri`. Keeps Q1 ("anyone with edit rights") for today's users. | REQ-012 AC4, AC5 | 2 |

Why B4 (safe branch, step 3 of the skill): the KB does not state whether a read-only user sees process buttons, nor whether executing a process (`ProcessId` on update) is refused for a read-only user (D10 covers only the display condition). Relying on the read-only permission alone to hide/refuse エスカレーション is the *expected* branch, unverified. With B4, 経理 is excluded at the process level as well; if PRB-2 shows the permission alone already hides and refuses it, B4 stays as defence in depth. If B4's own effect is not as expected, the permission layer is still there. The cost is a maintenance coupling (a future editor principal must also be added to B4) → raised as derived requirement DR-1.

Fallback branches (taken only on probe results, not by P3 on its own):
- **PRB-1 shows `inquiries` inherits its permissions from a parent folder**: do not grant 経理 on the folder (would expose every site in it). Instead `inquiries` would need its own permissions (copy of the folder entries + 経理), which stops future folder changes from flowing → permission structure change → back to P2/G1 before P3.
- **PRB-2 shows inheritance does not give 経理 read access to `responses`**: add an explicit read entry on `responses`; that means breaking its inheritance and replicating every `inquiries` entry → revised design (DES-003 rev.) before P3.

What each role can see and press after the change (TD-11 tests in P4, one test user per role):

| Role | `inquiries` | `responses` | エスカレーション button |
|---|---|---|---|
| 経理チーム (new, `${principal:keiri}`) | list + edit screen of all inquiries incl. 状況, 合計対応時間; no create/update/delete (refused); no comment (Q15, to confirm in PRB-2); attachments open/download (Q15, PRB-2) | list + edit screen of all 対応履歴; no create/update/delete | not shown (B4 + read-only), `ProcessId` refused |
| Support staff / サポート責任者 (existing editors) | unchanged | unchanged | unchanged — shown under the display condition (優先度 高, 状況 100/200/300), executable; **P4 tests this with a support user** to prove B4's list is complete |
| admin (`${principal:admin}`) | unchanged | unchanged | unchanged (included in B4) |

### C. 対応時間 (REQ-013, REQ-014, REQ-015)

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| C1 | `responses` `Columns[NumA]` 作業時間 (分) | **no change** (REQ-013 revised, Q23). Editor, grid, optional input stay as they are. | REQ-013 | 1 |
| C2 | `inquiries` column **NumB** (new slot) | `LabelText: 合計対応時間`, `Unit: 分`, `EditorReadOnly: true` (REQ-014 AC6 — screen only, D17). Editor: after `NumA` (対応回数). `GridColumns`: after `NumA`. `FilterColumns`: append `NumB` (AC7). | REQ-014 | 1 |
| C3 | `responses` **Summary #2** | `{Id: 2, Type: Total, SourceColumn: NumA, LinkColumn: ClassA, SiteId: ${site:inquiries}, DestinationReferenceType: Results, DestinationColumn: NumB}` — no condition, so 予定 and 完了 both count (Q18); empty counts as 0 (D16). D16 (1.5.2): every child create/update/delete recomputes the full total for the parent (AC1–3). | REQ-014 | 2 |
| C4 | `responses` **Summary #1** (Count → `inquiries.NumA` 対応回数), `Columns[ClassA]` link, `Links[ClassA]` | **kept exactly as exported** (P-4). The full `responses` payload (D4) is built from the P-1 export in git, so #1 is in it. | REQ-015 | — |
| C5 | Migration **M-2** | touch one 対応履歴 per inquiry after the release so existing parents get NumB (D16). Detail under "Migration". | REQ-014 | — |

Slot (A2, ADR-0002): **NumB** is the first Num slot the `inquiries` ledger has never allocated. It must be confirmed **unused and empty in every environment's export** (dev, stg and the production site) with `pls slots` before P3 deploys — D12: a slot that once held data shows that data again when redefined.

## Rejected alternatives

- **Change ClassD in one step (remove 契約・請求 and add 契約/請求 together), migrate afterwards** — records hold an orphan value between deploy and migration (D12) and users see an orphan option; rollback after the migration would itself remove a used choice (D11). The two-step sequence avoids both.
- **Migrate before adding 契約/請求 to the choices** — relies on the API accepting a value outside `ChoicesText`; not in `pls-kb-pleasanter`.
- **Rename 契約・請求 to 契約 and add 請求** — misclassifies the billing inquiries silently and contradicts Q9 (customer decides each record).
- **Convert past AI values (ClassF 契約・請求)** — Q12 assumed "keep"; not required.
- **Make `ai1` read the allowed list from ClassF's choices at run time** — needs site-settings access from a server script, not in the KB; adds code (rung 3 growth) for a list that changes rarely.
- **Restrict 経理 to カテゴリ = 請求 (record-level permission)** — Q14 accepted "all, read-only"; record-level permissions are not in the KB (P-3). Becomes a change request if the customer answers Q14 differently.
- **A new view 「請求」 for 経理** — not required (Q11/Q14: list filter on カテゴリ).
- **Rely on the read-only permission alone to hide/refuse エスカレーション** — behaviour not in the KB (no entry on process buttons for read-only users; D10 covers only the display condition); that is the unverified expected branch → B4 added.
- **Restrict `escalate` by a display condition instead of access control** — display conditions filter on record values (D10), not on who the user is.
- **New 対応時間 column on `responses`** — duplicate of 作業時間 (G1 revision of REQ-013, Q23).
- **Server script on `responses` that sums 作業時間 and writes the parent (rung 3)** — Summary Total does it with configuration and D16 verifies recalculation on create/update/delete; a script would add a cross-site write, D3 handling and a 10 s budget.
- **Formula column on `inquiries`** — the KB has no entry on formulas reading other records; Summary is the verified mechanism (D16).
- **Hand-entered 合計対応時間** — contradicts REQ-014 AC2/AC3/AC6.

## Impact analysis (`impact-checklist.md`, current `config/inquiries/` and `config/responses/`)

| Existing element | Impact | Action |
|---|---|---|
| `inquiries` records with ClassD 契約・請求 (7 in the original data, P-5) | choice removal → orphan (D11/D12) | M-1 before step 2 (REQ-008) |
| `inquiries` records with ClassF 契約・請求 (0 in the original data) | kept as orphan value after step 2 (D12) | intended (Q12); counted before step 2 and reported to the customer |
| `inquiries` Views 1 標準, 2 未完了, 3 状況×チャネル; Aggregation 1 (Status) | no filter/group on ClassD, NumB or permissions | none |
| `inquiries` `FilterColumns`/`GridColumns`/`LinkColumns` (ClassD, ClassF) | new choices appear automatically | none |
| `inquiries` Notification #1 (`MonitorChangesColumns` Status, ClassE; to `[Manager]`) | M-1 changes only ClassD; summary writes only NumA/NumB; 経理 is not a recipient | none (mail deferred, TD-10) |
| `inquiries` Reminder 1 (DateB, to `[Owner]`) | independent | none |
| Process `escalate` (display condition, data change, mail) | gains access control B4; display condition unchanged | B4 lists every current editor; DR-1 raised; P4 tests a support user and a 経理 user |
| `ai1` category list/instruction | would propose removed 契約・請求 | A3 (REQ-009) |
| `ai1` `inputs` (ClassD) | after M-1 no record sends 契約・請求 | none |
| `ai1` `related` block (reads `responses` by ClassA as the saving user) | link unchanged; added Summary does not change records it reads; 経理 never saves → never runs it | none (REQ-015 AC3 tested in P4) |
| `ai1` BeforeUpdate during M-1 | runs only when CheckA = true; M-1 sends ClassD only | none; M-1 dry run checks no AI stamp (ClassH) changes |
| `inquiries.NumA` 対応回数 ← `responses` Summary #1 | must survive the full-replacement update of `responses` (D4) | C4; REQ-015 AC1 before/after comparison |
| `responses` Views 1–3, crosstab 状況×対応種別 (Count) | no change | none |
| `responses` `Columns[NumA]` 作業時間 | becomes Summary #2 source; not changed | none |
| `responses` permissions (`inherit ${site:inquiries}`, no entries) | 経理 inherits read from `inquiries` | B2; PRB-2 confirms; fallback above |
| `inquiries` site permissions (not in git) | new read entry; existing entries must stay identical | B1 from live export; PRB-1 baseline; REQ-010 AC4 |
| `NoDisplayIfReadOnly: false` (both sites) | not relied on | none |
| Imports / API writes to `inquiries` NumB | can overwrite the total (D17) | open point O-4 |
| Slot ledger | `responses` slots were not in the ledger (lint L-SLOT-01) | recorded now from the P-1 export; NumB allocated |
| Release order | `responses` Summary #2 references `inquiries` NumB | `pls release-plan` orders `inquiries` first (`${site:inquiries}` reference) |

### Derived requirements raised (not absorbed)

- **DR-1 → P1/G1:** 「エスカレーションを実行できるのは、問い合わせ管理の編集権限を持つ利用者（サポート担当・サポート責任者・管理者）に限る。今後編集権限を付与する利用者・グループは、エスカレーションの実行者にも追加する」 — makes the B4 access list an explicit requirement (refines Q1) and states the maintenance rule. Until G1 decides, B4 = exactly today's editors, which keeps REQ-001/Q1 behaviour unchanged.
- **DR-2 → P1/G1 (only if PRB-2 shows read-only users can comment):** 経理 must not comment (Q15) → would need an additional restriction.

## Migration (data-impacting)

Both run in the release window agreed under C2/Q21 (weekday after 19:00 or weekend/holiday), first on dev with fixture records, then stg, then production. Every change of a record also changes its 更新日時/更新者 — **tell the customer** (M-1: the reclassified inquiries; M-2: one 対応履歴 per inquiry plus the inquiry itself through the summary).

### M-1 — カテゴリ reclassification (REQ-008)

1. **Before the window:** count ClassD = 契約・請求 and ClassF = 契約・請求 per environment (API `get` with filter). MADLAB drafts the list (ClassA 問い合わせ番号, 件名, current カテゴリ, proposed 契約/請求) from 件名/内容; the customer confirms or corrects it and decides unclear ones (Q9). The confirmed list is the input.
2. **Backup** (D14 — API updates create no versions): full records of all inquiries with ClassD = 契約・請求 (runner `backupRecords`).
3. **Key check** (D18): ClassA must be unique among all inquiries in the backup/export (`ValidateRequired` only, uniqueness not enforced). If not unique, stop and agree another key before running.
4. **Release step 1** (all additive config of DES-003: A1/A2 transitional, A3, B1, B3, B4, C2, C3).
5. **Re-count** 契約・請求; any record not on the list (created after the list was made) → stop, ask the customer, do not guess.
6. **Run:** `bulkupsert` on `inquiries`, `Keys: ["ClassA"]`, `Data` = `{ClassA, ClassD}` only (D13, D18 — other columns kept).
7. **Verify** (REQ-008 AC1–4): count 契約・請求 = 0; count(契約) + count(請求) = count before; other categories unchanged; per record only ClassD differs from the backup.
8. **Release step 2:** A1/A2 final (契約・請求 removed).
- **Dry run:** on dev with fixture inquiries holding 契約・請求 (including one with CheckA off and an AI stamp), same script and list format.
- **Rollback:** before step 2 — `bulkupsert` ClassD back from the backup (契約・請求 is still a choice), then redeploy the previous release. After step 2 — redeploy step 1 first (re-adds the choice, additive), then restore from the backup.

### M-2 — 合計対応時間 for existing inquiries (REQ-014, D16)

1. **Backup** all 対応履歴 records (D14) and the NumA/NumB of all inquiries; compute the expected NumB per inquiry offline = Σ 作業時間 per ClassA (empty = 0).
2. After the release containing C3, for each inquiry with ≥ 1 対応履歴: API `update` of **one** child (the latest by 対応日時) by record id, sending NumA = its current value (D16: an unchanged value still recalculates). Not `bulkupsert`: ClassA is not unique on `responses` (D18).
3. **Verify:** NumB = expected for every inquiry; NumA (対応回数) unchanged from the backup (REQ-015 AC1).
- **Dry run:** dev with fixture data (inquiry with 30 + 45 min, inquiry without children, a 予定 child with empty 作業時間).
- **Rollback:** redeploy the previous release (removes C3 and the NumB column definition). NumB values stay stored but hidden (D12) → NumB stays allocated in the ledger and is never reused for another purpose.

## Probes (none run — no environment reachable in this P2 session)

| ID | When | Contains (must reproduce the combination) | Result that changes the design |
|---|---|---|---|
| **PRB-1** | **G2 prerequisite** (read-only discovery: `getsite` on `inquiries` in dev, stg and production) | `InheritPermission` and `Permissions` of `inquiries`; principals with update rights (Type, Id, Value); existence of the 経理 group (`/api/groups/get`, Q13) | `inquiries` inherits from a parent folder → fallback branch (own permissions) and G1; the editor list defines B4 and the AC10.4 baseline; missing 経理 group blocks P3 |
| **PRB-2** | **G2 prerequisite**; if it cannot run before G2, the design already takes the safe branch (B4, fail-closed inheritance) and PRB-2 is the confirmation, run on dev before P3 build | On **dev**: a test group with the UI pattern 「読み取り」 on `inquiries`; `responses` inheriting from `inquiries` as today; `escalate` with B4 access control listing the editor principals but not the test group, display condition as live; a test inquiry with カテゴリ 請求, 優先度 高, 状況 100 (inside the display condition), with ≥ 1 対応履歴 and an attachment; a test user only in the test group, and a support test user. Record: stored permission value; `get` on both sites; `create`/`update`/`delete` on both sites (HTTP status, record unchanged); エスカレーション button shown?; `update` with `ProcessId` (status); comment box; attachment download; support user sees and executes エスカレーション. Restore dev afterwards; add the results to `pls-kb-pleasanter` with version and what the probe contained. | 経理 cannot read `responses` → explicit `responses` permission (fallback); read-only user can write or comment → further restriction + DR-2; access control does not hide/refuse → B4 kept only as UI aid or removed, REQ-012 AC5 re-checked; support user loses the button → B4 list incomplete |
| **PRB-3** | Before G2 if possible, otherwise as the first P3 dev deploy, **before anything reaches stg** | On **dev**: `responses` with existing Summary #1 (Count → NumA) **and** new Summary #2 (Total → NumB); inquiries with existing children before #2 is added; one child touched with an unchanged value; then AC1–5 of REQ-014 (30+45, change to 60, delete, no children, 予定 child) and the 対応回数 values before/after | #2 disturbs #1 or Total behaves differently from D16 in this combination → new design (rung 3 alternative) via P2/G2 again; D16 confirmed → no change |

Not probes, but checks before deploy: NumB empty and unused in every environment (`pls slots`); 契約・請求 counts (M-1 step 1/5); ClassA uniqueness (M-1 step 3).

## Open points

- **O-1** PRB-1 and PRB-2 are G2 prerequisites and were not run. G2 should either wait for them or explicitly accept the safe branch with the probes as confirmations.
- **O-2** `requirements/index.md` (P-1) says `responses` was added to `managed_sites` and its slots to the ledger, but `environments.json` still lists only `inquiries` and the ledger had no `responses` section. Slots are recorded now (from `config/responses/site.json`); **`managed_sites` must be corrected before P3** (not a P2 output).
- **O-3** `environments.json` has only dev and stg. The production site (original 42410/42411 per P-5?) needs its environment entry, principals and a slot check before the production release.
- **O-4** D17: NumB is read-only on screen only. An Excel import or API client that sends 合計対応時間 overwrites it until the next child change. Tell the customer; after any import to `inquiries`, re-run M-2 for the affected inquiries.
- **O-5** Moving a 対応履歴 to another inquiry (changing its ClassA): D16 does not say whether the *old* parent is recalculated. Not in the acceptance criteria; P4 records the behaviour on dev (informational).
- **O-6** `ai1` is generated from `spec.json` (`ai` section), which is not in this repository — P3 must change the source spec and regenerate, otherwise the next regeneration reverts A3.
- **O-7** C1 deadline 12/10: if not everything fits, priority per Q22 is A → C → B. A and C do not depend on B, except that B4 changes `escalate` in the same `inquiries` payload.
- **O-8** Customer confirmations still open: Q8–Q23 (all accepted as assumed at G1), DR-1 (and DR-2 if triggered).
