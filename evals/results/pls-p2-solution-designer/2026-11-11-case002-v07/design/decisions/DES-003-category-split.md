# DES-003 — カテゴリ 契約・請求 split into 契約 and 請求 (incl. past data and AI)

- **Status:** awaiting G2 (draft by the agent, 2026-11-11; dry run — no environment reachable, `pls lint`/`pls xref` not run, see Open points)
- **Requirements:** REQ-007, REQ-008, REQ-009 (G1 approved, Nam, 2026-11-05; assumptions Q8–Q12 accepted as written)
- **Change classification (ADR-0004):** **data-impacting** —
  - REQ-008 changes the stored カテゴリ (`ClassD`) of every inquiry holding 契約・請求 (7 of 100 in the original data, P-5; to be re-counted on each environment right before the migration).
  - REQ-007 removes the choice 契約・請求 from `ClassD`; REQ-009 removes it from `ClassF`. Removing a choice that records use is data-impacting (D11, D12). For `ClassD` the migration empties it first; for `ClassF` past AI values stay on the records as orphan values by decision (Q12).
  - The AI script change itself is config-only.

## Ladder (I5)

- Rung 1 for the choice lists (E1, E2, E3).
- Rung 3 for E4: **existing** server script `ai1` (reason recorded in DES-000: external AI call). This design changes only its data (allowed list, instruction text). No new script and no new logic.
- The migration (M1) is a one-off data operation through the record API, not part of the configuration.

## Design

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| E1 | カテゴリ choices, transitional (release step 1) | `Columns[ClassD].ChoicesText` = `操作方法\n不具合\n契約\n請求\n契約・請求\n機能要望\nその他` — new choices added, old one kept until M1 has run | REQ-007, REQ-008 | 1 |
| E2 | カテゴリ choices, final (release step 3) | `Columns[ClassD].ChoicesText` = `操作方法\n不具合\n契約\n請求\n機能要望\nその他` (order: Q8) | REQ-007 | 1 |
| E3 | AI: 推定カテゴリ choices | `Columns[ClassF].ChoicesText` = same six lines as E2, same order (REQ-009 AC1). Set to the final list in step 1 already: no record gets a new 契約・請求 AI value after step 1 | REQ-009 | 1 |
| E4 | `inquiries` server script `ai1` (title 「AI問い合わせ一次対応」, `server-scripts/_index.json` Id 1) | `CONF.outputs[key=category].allowed` = `["操作方法","不具合","契約","請求","機能要望","その他"]`; `instruction` = 「カテゴリ（操作方法/不具合/契約/請求/機能要望/その他 のいずれかの文字列）」. The existing guard (`allowed.indexOf(...) < 0 → return`) is kept, so a returned 契約・請求 is not written (REQ-009 AC2). Change the generator source (spec.json), then regenerate — see Open points | REQ-009 | **3** (existing) |
| M1 | Migration of past 契約・請求 inquiries | see *Migration* below | REQ-008 | — |

Rung-3 reason for E4: the AI first response calls the AI gateway; rungs 1–2 cannot call an external service (DES-000). This change adds no logic; it only aligns the script's allowed list with the choice list.

### Release sequence (proposed, P5 decides the release split)

A removed choice that records still hold becomes an orphan (D12). Whether the record API accepts a カテゴリ value that is **not** in the choice list is **not in `pls-kb-pleasanter`**, so the design does not rely on it: the new choices exist before M1 writes them, and the old one is removed only after M1.

1. Deploy `inquiries` with E1, E3, E4 (and the elements of DES-004/DES-005 that change `inquiries`).
2. M1 (backup, migrate, verify counts).
3. Deploy `inquiries` with E2.

Steps 1–3 run inside the window allowed by C2 (Q21 assumed: weekdays after 19:00 or weekends/holidays), when nobody edits the site (D4a). Steps 1 and 3 can be two releases; between them the list shows 契約・請求 next to 契約/請求 for a short time only.

## Rejected alternatives

- **Remove 契約・請求 and migrate afterwards in one step** — relies on the API accepting a value outside the choice list (not in the KB) and leaves the 7 records showing an orphan option until migrated (D12).
- **Rename 契約・請求 to 契約 and add 請求** — silently classifies every past billing inquiry as 契約; contradicts REQ-008 AC3 (each record per the agreed list, Q9).
- **Keep 契約・請求 as a seventh choice** — contradicts REQ-007 AC2.
- **Server script that classifies past records with the AI** — rung 3 not needed; Q9 assumes a list reviewed by the customer, and AI output is not deterministic.
- **Convert the past AI values (`ClassF` = 契約・請求)** — out of scope by decision (Q12 [assumed] keep them).

## Impact analysis (`impact-checklist.md`, current `config/inquiries/`)

| Existing element | Impact | Action |
|---|---|---|
| Records with `ClassD` = 契約・請求 | orphan value after E2 (D11, D12) | M1 before E2 (REQ-008) |
| Records with `ClassF` = 契約・請求 (AI values) | orphan option shown on their edit screen after E3 (D12); value kept | accepted by Q12; count them on each environment before step 1 (P-5: 0 in the original data); tell the customer that such values show as an old option |
| `ai1` `CONF.outputs[category]` allowed list and instruction | would keep proposing a removed category | E4 (REQ-009) |
| `ai1` `CONF.inputs` (ClassD sent to the AI as カテゴリ) | value text only; new values readable | none |
| Views 1 標準, 2 未完了, 3 状況×チャネル; Aggregation 1 (by Status) | none filters or groups by `ClassD`/`ClassF` | none |
| `FilterColumns`, `GridColumns`, `LinkColumns` (ClassD), `FilterColumns` (ClassF) | the new choices appear automatically | none |
| Notification #1 (`MonitorChangesColumns` Status, ClassE) | M1 changes only `ClassD` → no mail | none; verify in P4 that M1 sends no mail |
| Process `escalate` (display condition ClassE, Status) | independent of カテゴリ | none |
| Reminder 1 (DateB) | independent of カテゴリ | none |
| `ai1` BeforeUpdate during M1 | runs only when `CheckA` is true; M1 sends only `ClassD`, `CheckA` stays as stored (false after any AI run) | check in the backup that no target record has `CheckA` = true; if one has, stop and ask |
| Slot ledger | no new column | none |
| Permissions | unchanged by this DES (see DES-004) | none |

`pls xref --site inquiries` was **not run** in this dry run (no shell available). Manual reading of `ai1.js`: it names `ClassD` (input), `ClassF` (output) and the 契約・請求 text twice (instruction, allowed); `aiEnv.js` names no column. P3 must run `pls xref --site inquiries` and compare.

## Migration (M1, REQ-008)

Run by the person (CLAUDE.md rule 3) on each environment of the release, in the C2 window, after step 1:

1. **Count** inquiries with `ClassD` = 契約・請求 and record the counts of all six categories (REQ-008 AC2 baseline).
2. **Reclassification list** (Q9 [assumed]): MADLAB proposes 契約 or 請求 per inquiry from 件名/問い合わせ内容; the customer confirms or corrects; undecided rows are decided by the customer. Key = `ClassA` (問い合わせ番号). The confirmed list is customer data: kept under `.pls/` (gitignored), never committed.
3. **Backup** the target records (all columns) before any write — API updates create no versions (D14).
4. **Key check:** every `ClassA` in the list exists **exactly once** in the backup and currently holds 契約・請求; otherwise stop (D18: a duplicate key makes `bulkupsert` fail; D13: an unmatched key would **create** a new record).
5. **Write:** `bulkupsert` with `Keys: ["ClassA"]`, `Data` = `ClassA` + `ClassD` only (D18: other columns kept — REQ-008 AC4).
6. **Verify:** count of 契約・請求 = 0; 契約 + 請求 = baseline; other categories unchanged; sample compared with the list; 状況/優先度/対応担当/エスカレーション日時 unchanged (REQ-008 AC1–AC4).
7. Tell the customer that 更新日時/更新者 of the migrated inquiries change.

Dry run on a copy: run steps 1–6 on dev against a seeded copy of the records (test data with the same shape), before stg.

**Rollback:** before step 3 of the release sequence — `bulkupsert` the backup values (`ClassA`, `ClassD` = 契約・請求) and redeploy the previous `inquiries` configuration. After step 3 — first redeploy E1 (old choice back), then restore from the backup. Rollback of E3 does not restore anything (no AI value is changed).

## Open points

- **spec.json missing:** `ai1.js` says it is generated from `spec.json` and overwritten on re-registration; no `spec.json` is in this project. Where is the source? (project owner) Until known, P3 edits `ai1.js` in git and records the generator gap.
- Whether the record API accepts a カテゴリ value outside the choice list — not needed by this design; not probed.
- Environment holding the real records: P-5 counts come from the original sites (42410/42411), not from dev/stg (test records only), and `environments.json` declares only dev and stg. On which environment does M1 run for real, and who runs it? (project owner)
- Release split (one release with two `inquiries` deploys, or two releases) — P5.
- Customer questions Q8–Q12, Q21, Q22 stay open (asked in `requirements/index.md`).
