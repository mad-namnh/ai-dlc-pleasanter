# DES-001 — Escalation of high-priority inquiries

- **Status:** awaiting G2 — **not ready to present** until (a) the G2-prerequisite probe P-001 has run on dev, (b) derived requirements REQ-005 and REQ-006 have a G1 decision, (c) the G1 record exists in `gates/` (see Open points).
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004; derived (proposed, awaiting G1): REQ-005, REQ-006
- **Site:** `inquiries` (Results / 記録テーブル, existing; `config/inquiries/`)
- **Change classification (ADR-0004):** **config-only** — adds a status, a column in a never-allocated slot, a プロセス and one view filter value; no existing record value changes, nothing is removed, no permission changes (the process has no access control, per the G1 assumption Q1). Becomes **permission-impacting** if Q1 is answered "assignee only" (see Permission design). Becomes script-touching (rung 3, existing script) if REQ-005/REQ-006 are approved.

## Ladder (I5)

Rung: **2** (プロセス with display condition, data change and mail notification) plus rung 1 settings. No new code. The existing rung-3 script `ai1` (DES-000) is touched only if derived requirement REQ-006 is approved; its rung-3 reason stays the one in DES-000.

## Design

| # | Element | Setting | REQ | Rung |
|---|---|---|---|---|
| E1 | Status `150` | `Columns[Status].ChoicesText`: insert line `150,エスカレーション中,エ,status-inprogress` after the `300,…` line (order in the dropdown: 受付, 対応中, 顧客回答待ち, エスカレーション中, 解決, クローズ) | 001, 002 | 1 |
| E2 | Column `DateC` = エスカレーション日時 | `Columns[DateC]`: `LabelText "エスカレーション日時"`, `EditorReadOnly: true`, `EditorFormat "Ymdhm"`. In `EditorColumnHash.General` after `Manager` (required, D22) and in `GridColumns` after `Manager`. Not added to `FilterColumns` (not required) | 001 (AC2, AC3) | 1 |
| E3 | プロセス `escalate` (DisplayName エスカレーション) | `ScreenType` 20 (default, edit), `ExecutionType` 0 (button), `ActionType` 0 (save), `CurrentStatus: -1`, `ChangedStatus: 150`, `ConfirmationMessage "サポート責任者にエスカレーションします。よろしいですか？"`, `SuccessMessage "エスカレーションしました。"`. No `Groups`/`Users`/`Depts` (Q1 assumption: anyone with edit rights) | 001 | 2 |
| E4 | Display condition of `escalate` | `View.ColumnFilterHash`: `{"Status": "[\"100\",\"200\",\"300\"]", "ClassE": "[\"高\"]"}`. Required by D21 (a process must carry a `View`; `CurrentStatus` alone is not a condition). Enforced server-side for API execution (D10). Excludes 150 → no double escalation | 002 (AC1–3) | 2 |
| E5 | Data change of `escalate` | `DataChanges: [{Id: 1, Type: "InputDateTime", ColumnName: "DateC", BaseDateTime: "CurrentTime"}]` — stamps execution date-time. **Depends on probe P-001** (InputDateTime + CurrentTime into an `EditorReadOnly` column is not in the KB; only `InputDate`/`CurrentDate` is, schema.md) | 001 (AC2) | 2 |
| E6 | Mail notification of `escalate` | `Notifications: [{Id: 1, Type: 1, Address: "[Manager]", Subject: "【エスカレーション】[ClassA] [Title]", Body: "問い合わせ番号: [ClassA]\n件名: [Title]\n顧客名: [ClassB]\n優先度: [ClassE]\nエスカレーション日時: [DateC]"}]`. Delivery not testable on dev → verified on stg (Q4) | 003 | 2 |
| E7 | View 2 未完了 | `Views[Id=2].ColumnFilterHash.Status`: `"[\"100\", \"200\", \"300\", \"150\"]"` | 004 | 1 |

Config paths P3 will create or change: see `traceability.json`.

### Permission design (step 1b)

Roles derived from the requirements:

| Role | Who | inquiries: read / create / update / delete / manage | Process `escalate` |
|---|---|---|---|
| editor (incl. 対応担当) | anyone with edit rights on the site today | unchanged (inherited from the parent folder; no `permissions.json` in `config/`) | may press (Q1 assumption) |
| サポート責任者 | the user in column `Manager` of the record | unchanged | receives the mail; may press if they have edit rights |
| read-only users (if any exist) | — | unchanged | **sees the button** when the condition matches (D19) but is refused with 403 on press; no data change |

- No group is referenced by this design: no `${principal:…}` in the configuration, `design/roles.json` has no roles. No groups need to be created after G2.
- **If Q1 is answered "対応担当のみ"** (REQ-001 text says "the assignee executes"): process access control (`Users`/`Groups`, D20) cannot express "the record's own Owner" — it takes fixed principal lists. That answer would need a group (e.g. `inquiries_assignees`) → permission-impacting, roles.json entry, groups created by the person after G2, and a role test in P4 (TD-11). Back to G1 in that case.
- P4: profile says role tests are `deferred`; if read-only users exist on stg, one negative test (read-only user → 403 on `escalate`) is planned but carried as deferred.

## Rejected alternatives

- **Server script that sets status/date and sends mail** — rung 3 not needed; a プロセス covers status change + data change + notification + display condition (ladder.md, "typical traps").
- **Checkbox "エスカレーション済" to drive the display condition** — rejected by D9 (checkbox filter is 2-state); state is modelled by status 150 (Q2).
- **Process without `View` (only `CurrentStatus`)** — rejected by D21 (API execution 500 / UI error; and `CurrentStatus` cannot express three statuses + priority).
- **Reusing an existing date column (DateA 受付日 / DateB 対応期限)** — they hold other data; a new never-allocated slot is used (A2, ADR-0002).
- **Using the existing site notification #1 for the escalation mail** — it is a generic change notification (MonitorChangesColumns Status/ClassE, subject 「未対応です」); it cannot carry the escalation-specific content and fires on unrelated changes. The process notification fires only on escalation.
- **Hiding the button from read-only users with process access control** — not chosen under the Q1 assumption; pressing is refused anyway (D19), so this is a screen nuisance, not a data risk. Revisit if Q1 changes.

## Impact analysis

Walked every element of `config/inquiries/site.json` and both scripts. `pls xref --site inquiries` **was not run** in this dry run (no shell available); the script impact below is from reading the script text — P3 must run `pls xref` and compare.

| Existing element | Impact | Action |
|---|---|---|
| Status choices (100,200,300,900,910) | new value 150 | E1 |
| View 1 標準 | no status filter → escalated records listed | none |
| View 2 未完了 (`Status` 100/200/300) | would hide 150 | E7 (REQ-004, already approved) |
| View 3 状況×チャネル (crosstab Y = Status) | new row エスカレーション中 appears | none — accepted at G1 (Q2: 「一覧・集計に新しい状況が増えます」) |
| Aggregation 1 (GroupBy Status) | new group 150 | none — accepted at G1 (Q2) |
| **Site notification 1** (mail to `[Manager]`, MonitorChangesColumns Status + ClassE, `AfterCondition: 2` = view 未完了, subject 「優先度「高」の問い合わせが未対応です」) | Once view 2 includes 150 (E7), the escalation itself (Status 200→150, a monitored column) leaves the record inside view 2 → the manager would also get 「…未対応です」 for every escalation, and for later status/priority changes of escalated records. Today 150 does not exist. Whether a process save triggers site notifications, and the exact meaning of `Expression: 1`, are **not in the KB** (probe P-001 step 6). Safe branch: assume it fires | **Derived requirement REQ-005** (proposed, back to G1). Not absorbed. Candidate resolutions in REQ-005 |
| **Reminder 1** (to `[Owner]`, DateB within 3 days, `Condition: 2`) | If `Condition` is a view Id (KB silent; schema.md documents view-Id conditions only for notifications), escalated records now get the due-date reminder to the Owner. Probably intended (the record stays open), but it is a behaviour change | Open question Q7; confirmation via P-001 step 7 (read-only: open reminder 1 in the dev settings dialog) |
| **Script `ai1`** status map `CONF.choices.Status` (100,200,300,900,910) | No entry for 150 → for an escalated record the AI prompt shows 「状況: 150」 instead of the label. Script header: generated from `spec.json`, hand edits are overwritten on re-registration — `spec.json` is not in this project | **Derived requirement REQ-006** (proposed, back to G1); `spec.json` location is an open question |
| Script `ai1` `_rel_Status` map (responses site) | not affected (other site) | none |
| Script `aiEnv` | not affected | none |
| Column slots | DateC new; ledger never allocated it | Must be **confirmed empty in dev (44565) and stg (44573)** before P3 writes it (record data, not only settings — D12: a slot defined earlier keeps hidden values). Check in P3 preflight |
| Editor layout / grid / link columns / title | DateC added to editor + grid; title and links unchanged | E2 |
| Filters (FilterColumns) | none needed | none |
| Permissions | none changed (Q1 assumption) | see Permission design |
| Links / summaries | `NumA` 対応回数 is read-only (probably a summary from `responses`, not in `config/`); not touched | none |

## Migration

Not data-impacting: no migration. Existing records stay in their statuses; DateC is empty for all existing records (no back-fill — no requirement asks for it). Rollback: release rollback of `inquiries` site settings; if any record reached 150 before a rollback, it keeps 150 as an orphan status (D12) — rolling back after use needs a data step (set those records back to their previous status), to be written in the release plan if a rollback is ever needed.

## Probes

`design/probes/P-001-escalation-process.md` — **G2 prerequisite** (written, not run: no environment reachable in this run). Steps 2–3 decide whether E5 + AC3 work at rung 2; steps 6–7 confirm the safe branch taken for REQ-005 / Q7.

## Open points

1. **G1 record missing:** `requirements/index.md` says G1 approved by Nam on 2026-11-05, but there is no `gates/` record (`pls gate`); the last `pls lint` (ops log, 2026-11-11 13:50) refused with L-GATE-01 ×4 and L-PRF-01 ×4. Nam records G1 with `pls gate` (his words) — the agent does not.
2. **`config/` freshness:** the ops log shows `config/inquiries/` was unpacked from the **stg rollback file** of release R-20261105-01 (the state *before* that release). Confirm that this is the current desired configuration of dev and stg (export + compare) before P3; if not, this impact analysis must be redone.
3. P-001 must run on dev before G2 (E5 + AC3 depend on it).
4. REQ-005, REQ-006 need a G1 decision (derived; not absorbed).
5. Q1 wording conflict: REQ-001 says "the assignee executes", the approved assumption says "anyone with edit rights".
6. Re-escalation after a manual status change: a user can set 150 back to 100/200/300 by hand; the button then shows again and a second escalation overwrites DateC and sends a second mail. Q3 says re-escalation is not needed, but nothing prevents it. Preventing it would need a condition on "DateC empty" — date "未設定" filter not in the KB (D23 covers numeric only). Question Q6.
7. Empty サポート責任者: if `Manager` is empty, the escalation mail has no recipient (behaviour not in the KB). Question Q5.
8. Mail delivery not testable on dev (Q4: verified on stg by the customer). The P4 test on dev checks the configuration and the status/date only.
9. KB version: entries are verified on 1.5.2; the dev/stg version was not checked (`pls version` not run).
10. Observation outside this change: `environments.json` gives stg the same `AI_GATEWAY_URL` as dev (`…-gateway-dev-…`). Confirm intended.
