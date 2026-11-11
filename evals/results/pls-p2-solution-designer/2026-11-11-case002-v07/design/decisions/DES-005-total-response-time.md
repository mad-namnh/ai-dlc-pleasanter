# DES-005 — 合計対応時間 per inquiry from 作業時間; 対応回数 kept

- **Status:** awaiting G2 (draft by the agent, 2026-11-11; dry run — see Open points)
- **Requirements:** REQ-013 (revised: existing 作業時間), REQ-014, REQ-015 (G1 approved, Nam, 2026-11-05; Q17, Q18, Q20, Q23 accepted as assumed)
- **Change classification (ADR-0004):** **data-impacting** — a new Summary does not recalculate existing parents (D16); past 作業時間 exists on all 対応履歴, so the totals of existing inquiries need a migration that touches one 対応履歴 per inquiry (changes its 更新日時/更新者). Otherwise config-only: one new column on `inquiries`, one new Summary on `responses`; nothing removed.

## Ladder (I5)

Rung 1 (column, Summary). No script, no formula.

## Design

| # | Element | Setting (P3) | REQ | Rung |
|---|---|---|---|---|
| E1 | 作業時間 on `responses` | **no change**: `Columns[NumA]` (作業時間, unit 分) stays on the editor and the grid; optional as today | REQ-013 | 1 |
| E2 | New column 合計対応時間 on `inquiries` | `Columns[NumB]`: `LabelText` 合計対応時間, `Unit` 分, `EditorReadOnly` true | REQ-014 | 1 |
| E3 | Layout of NumB | `EditorColumnHash.General`: after `NumA` (required for the Summary to write it, D22); `GridColumns`: after `NumA`; `FilterColumns`: append `NumB` | REQ-014 AC6, AC7 | 1 |
| E4 | Summary #2 on `responses` (child) | `{Id: 2, Type: "Total", SourceColumn: "NumA", LinkColumn: "ClassA", SiteId: "${site:inquiries}", DestinationReferenceType: "Results", DestinationColumn: "NumB"}`; no `SourceCondition` → 予定 and 完了 both counted (Q18) | REQ-014 | 1 |
| E5 | Summary #1 on `responses` (対応回数, Count → `inquiries.NumA`) | **kept unchanged** in the full payload (D4) | REQ-015 | 1 |
| M2 | Touch migration | see *Migration* | REQ-014 | — |

### Behaviour relied on (KB)

- D16: every child create/update/delete recomputes the **full** total for that parent; empty counts as 0 → REQ-014 AC1–AC3, AC4 (records without 作業時間). Prerequisite P-2 of P1 is answered by D16; no new probe.
- D16: adding a Summary does not recalculate existing parents; touching one child recalculates its parent → M2.
- D22: the destination column must be in `EditorColumnHash`.
- D17: `EditorReadOnly` is screen-only; API clients or imports can still write NumB → any import into `inquiries` must be followed by a touch (M2 procedure). REQ-014 AC6 is a screen criterion, met.
- D23: an inquiry never linked keeps NumB **empty** (API shows 0) → REQ-014 AC4 accepts 0 or empty.

Not verified in the KB, carried as confirmation in P3/P4 (does not change the design): two Summaries on the same child site writing to two columns of the same parent (Count + Total). Expected to work; if not, back to G2. Probe PR-4 on dev: a copy of `responses` with Summaries #1 and #2, one inquiry with two children 30/45 → NumA 2, NumB 75; update 45→60 → 90; delete one → NumA 1, NumB 30 or 60.

## Slot allocation

`inquiries.NumB` — the first Num slot the ledger has never allocated (`NumA` = 対応回数). Recorded in `design/slot-ledger.json` (`req` REQ-014, `design` DES-005). **Must be confirmed empty in every environment's export before P3** (dev, stg, and the environment holding the real records): not defined in `Columns`, and no record holds a NumB value (D12: a removed column keeps its values). No slot on `responses` (REQ-013 revised).

## Rejected alternatives

- **New 対応時間 column on `responses`** — duplicates 作業時間 (G1 revision of REQ-013, Q23).
- **Server script on `responses` that sums the children into the parent** — rung 3 not needed; Summary does it (D16).
- **Formula / calculated column on `inquiries`** — a formula reads the record's own columns, not linked children.
- **Count with `SourceCondition` = 完了 only** — contradicts Q18 [assumed] (予定 included).
- **No migration (totals from the release on only)** — REQ-014 note: past 作業時間 exists and is needed for the 12/10 closing (C1); without M2 past inquiries show empty until a child changes.

## Impact analysis

| Existing element | Impact | Action |
|---|---|---|
| `responses` Summary #1 (対応回数) | lost if the deploy payload omits it (D4) | E5; drift check of `responses` before the deploy; REQ-015 AC1/AC2 before/after |
| `inquiries.NumA` (対応回数, read-only) | M2 recomputes it to the same value | REQ-015 AC1 sample before/after |
| `inquiries` crosstab view 3 (`CrosstabValue` NumA, Count) | unaffected (counts records) | none |
| `inquiries` grid, filter, editor layout | new column NumB | E3 |
| `inquiries` export | NumB must appear in the export (REQ-014 AC7); default export columns are not in the KB | P4 checks the exported file |
| `ai1` related block (reads `responses` by `ClassA`: DateA, ClassB, Title, Body) | link unchanged; no new column read | none (REQ-015 AC3 checked on dev) |
| `ai1` iterating columns | it uses explicit input lists only; NumB not sent to the AI | none |
| `responses` views 1–3, aggregation | unchanged | none |
| `responses` permissions (inherit) | 経理 reads NumA like the other columns (REQ-011 note) | none |
| Release order | NumB must exist in `inquiries` (`EditorColumnHash`) before the Summary on `responses` writes it | deploy `inquiries` before `responses` (same as `${site:inquiries}` reference order) |
| Notifications / reminders on `inquiries` | none monitor NumA/NumB | none |

`pls xref --site inquiries` / `--site responses` not run in this dry run (no shell). Manual reading: no script names NumB; `ai1` names `responses` and `ClassA`.

## Migration (M2, after the `responses` deploy)

Run by the person on each environment, in the C2 window, when nobody edits:

1. Baseline: for every inquiry, record NumA (対応回数); count inquiries with at least one 対応履歴.
2. Backup the 対応履歴 records to be touched (D14: no versions).
3. For each inquiry with 対応履歴, update **one** linked 対応履歴 with its own unchanged 作業時間 (D16: an unchanged value still recalculates the parent). About 100 records in the original data.
4. Verify: NumB = sum of linked 作業時間 for a sample (and the total, 6,320 min in the original data, P-4/P-5); NumA unchanged for all (REQ-015 AC1).
5. Tell the customer: the touched 対応履歴 show a new 更新日時/更新者 (question Q25).

Dry run on dev with seeded test records first. **Rollback:** redeploy the previous `responses` configuration (Summary #1 only) and `inquiries` (without NumB). NumB values stay stored but hidden (D12) — the slot is never reused. Touched records need no rollback (values unchanged).

## Open points

- PR-4 (two Summaries on one child) — confirmation on dev in P3.
- Confirm NumB empty in every environment's export (slot rule A2).
- Environment holding the real records (see DES-003) — where M2 runs for real.
- Customer questions Q17–Q20, Q23 stay open; new question (日本語):
  - Q25: 合計対応時間を過去の問い合わせにも表示するため、公開時に各問い合わせの対応履歴を1件ずつ再保存します（内容は変わりません）。その対応履歴の「更新日時」「更新者」が作業日時・作業者に変わりますが、問題ありませんか？
