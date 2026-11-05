# DES-001 — Escalation of high-priority inquiries

- **Status:** awaiting G2 (designed by the AI assistant, 2026-11-05; not self-approved, I4)
- **Site:** `inquiries`
- **Requirements:** REQ-001, REQ-002, REQ-003, REQ-004 (G1 approved by Nam, 2026-11-05, assumptions Q1–Q4)
- **Change classification (ADR-0004):** **config-only** — one status choice is *added* (none removed or renamed, D11), one column is added in a slot that the ledger has never allocated (DateC), one process and one view filter value are added. No existing record value changes and no permission changes (Q1: anyone with edit rights may escalate, so no `AccessControl` on the process and no change to the permission matrix). No migration needed. Caveat: the "slot never held data" check for DateC could not be probed on an environment in this session (see open point O1).

## Ladder (I5)

Highest rung used: **2** (プロセス with display condition, data change and notification). No server script, no SQL, no external integration. Everything else is rung 1 (status choice, column, editor layout, view filter).

## Design

| # | Element | Setting (P3 creates it at) | REQ | Rung |
|---|---|---|---|---|
| E1 | New status **150 エスカレーション中** | `Columns[Status].ChoicesText`: insert line `150,エスカレーション中,エ,status-inprogress` between 100/200/300 and 900 (existing lines unchanged) | REQ-001 (AC1), Q2 | 1 |
| E2 | New column **エスカレーション日時** in slot **DateC** | `Columns[DateC]`: `LabelText "エスカレーション日時"`, `EditorReadOnly true`, `EditorFormat "Ymdhm"` | REQ-001 (AC2, AC3) | 1 |
| E3 | Editor layout | `EditorColumnHash.General`: insert `DateC` directly after `DateB` | REQ-001 (AC3) | 1 |
| E4 | Process **escalate** (button) | `Processes[]`: `Id 1`, `Name "escalate"`, `DisplayName "エスカレーション"`, `ScreenType 20` (default, dropped on save — D8), `ExecutionType 0` (added button), `ActionType 0` (save), `CurrentStatus -1`, `ChangedStatus 150`, `ConfirmationMessage "サポート責任者にエスカレーションします。よろしいですか？"`, `SuccessMessage "エスカレーションしました。"`, no `AccessControl` (Q1) | REQ-001 | 2 |
| E5 | Display condition of E4 | `Processes[escalate].View.ColumnFilterHash = {"Status": "[\"100\",\"200\",\"300\"]", "ClassE": "[\"高\"]"}` — status and choice columns, no checkbox (D9). Enforced server-side for API execution too (D10). After execution the status is 150, which is outside the condition → no double escalation (Q3) | REQ-002 (AC1–3) | 2 |
| E6 | Data change of E4 | `Processes[escalate].DataChanges[]`: `{Id 1, Type "InputDateTime", ColumnName "DateC", BaseDateTime "CurrentTime"}` | REQ-001 (AC2) | 2 |
| E7 | Mail notification of E4 | `Processes[escalate].Notifications[]`: `{Id 1, Type 1, Address "[Manager]", Subject "【エスカレーション】[ClassA] [Title]", Body "問い合わせ番号: [ClassA]\n件名: [Title]\n顧客名: [ClassB]\n優先度: [ClassE]\nエスカレーション日時: [DateC]"}` | REQ-003 (AC1, AC2) | 2 |
| E8 | View **未完了** (Id 2) filter | `Views[2].ColumnFilterHash.Status = "[\"100\", \"200\", \"300\", \"150\"]"` (sorter unchanged) | REQ-004 (AC1) | 1 |

Notes for P3: run `pls canon --site inquiries` after editing (D8: `ScreenType 20` dropped; `View`, `DataChanges[]`, `Notifications[]` defaults added). Grid (`GridColumns`) and filter bar (`FilterColumns`) are **not** changed: no requirement asks for DateC there; `Status` is already in both, so 150 appears automatically.

## Rejected alternatives

- **Checkbox 「エスカレーション済」 + display condition "not checked"** — impossible: checkbox view filters are 2-state (D9). State is modelled with Status 150 instead (Q2).
- **Server script (BeforeUpdate) that sets status/date and sends mail** — rung 3 not needed: a プロセス covers status change + data change + notification + display condition (ladder trap #1). It would also add to the existing `ai1` BeforeUpdate path and its ~10 s limit.
- **Site-level notification watching Status → 150** instead of a process notification — needs an additional view as condition and would also fire for manual status edits and imports; the process notification fires exactly on the escalation action (REQ-003).
- **Display condition only, without status change** (keep status, rely on DateC empty) — "date is empty" as a display condition is not a verified behaviour in `pls-kb-pleasanter`; Status-based condition is verified (schema.md, D10).
- **Reusing slot ClassH / NumA etc.** — all allocated and holding data (A2, ADR-0002). DateC is the first free date slot.

## Impact analysis (`impact-checklist.md`)

Walked every element of `config/inquiries/site.json` and `server-scripts/`.

| Existing element | Impact | Action |
|---|---|---|
| View 1 「標準」 (no filter) | 150 records listed as before | none |
| View 2 「未完了」 (Status 100/200/300) | Escalated records would disappear from the open list | **already raised and approved as REQ-004** → E8 |
| View 3 「状況×チャネル」 (crosstab, GroupByY Status) | New row 「エスカレーション中」 appears | none — accepted with Q2 ("一覧・集計に新しい状況が増えます") |
| Aggregation 1 (GroupBy Status) | New group 150 appears | none — accepted with Q2 |
| **Notification 1** (`[Manager]`, monitors Status/ClassE, `AfterCondition 2` = view 未完了, subject 「優先度「高」の問い合わせが未対応です」) | Today a 200→150 change would not satisfy the after-condition. **After E8 (REQ-004) it does**: every escalation (a Status change into view 2) also triggers this notification → the manager gets a second, misleading mail ("未対応です") in addition to E7 | **Derived requirement DR-1 raised → P1/G1** (not absorbed) |
| **Reminder 1** (DateB within 3 days → `[Owner]`, `Condition 2`) | If `Condition` is the view Id (as for notification conditions), escalated records keep receiving the due-date reminder only because of E8; without E8 they would silently stop. Semantics of `Reminders[].Condition` are **not** in `pls-kb-pleasanter` and could not be probed (no environment) | **Derived requirement DR-2 raised → P1/G1**; probe P-2 |
| Status column choices 900/910 | unchanged; no record uses 150 yet → adding is not data-impacting (D11 only concerns removal) | none |
| `FilterColumns` / `GridColumns` / `LinkColumns` (Status) | 150 appears in the status filter and grid automatically | none |
| `TitleColumns` | unaffected | none |
| **Server script `ai1`** (BeforeCreate/BeforeUpdate, not shared) | `CONF.choices.Status` maps 100/200/300/900/910 only → for an escalated record the AI prompt shows 「状況: 150」 instead of the label. Also: the script is generated from `spec.json` (header says hand edits are overwritten), which is not in this repository | **Derived requirement DR-3 raised → P1/G1**; open point O4 |
| Server script `ai1` on process save | E4 saves the record → BeforeUpdate runs. `ai1` does nothing unless CheckA is on; if a user ticks CheckA and presses エスカレーション, the AI call (≤ 9 s) runs in the same save. Behaviour unchanged, within the ~10 s limit | none (note for P4: one test with CheckA on) |
| Shared script `aiEnv` | unaffected (`var`, D7) | none |
| Permissions | No change; any user with edit rights sees the button when E5 holds (Q1) | none — not permission-impacting |
| Process API execution | Display condition enforced (D10) → P4 negative API test: 優先度 中 or status 150 → HTTP 400 | P4 test |
| Mail delivery | Not testable on dev (Q4: verified in stg by the customer) | open point O3 |
| Cross-site links / lookups | none touched (`${site:responses}` in `ai1` unaffected) | none |

### Derived requirements raised (back to P1 / G1 — not designed here)

- **DR-1** — Should the existing notification 1 (「優先度「高」の問い合わせが未対応です」) fire when an inquiry is escalated? Options for the customer: (a) accept two mails; (b) exclude 150 from its condition (needs its own condition view, since view 2 must include 150 for REQ-004); (c) other. 確認事項（案）: 「エスカレーション時に、既存の『優先度「高」の問い合わせが未対応です』通知もサポート責任者に送られるようになります。送信してよいですか？」
- **DR-2** — Should escalated inquiries continue to receive the 対応期限 reminder to the 対応担当? (Assumed yes; depends on probe P-2.) 確認事項（案）: 「エスカレーション中の問い合わせにも、対応期限のリマインダーを対応担当に送り続けますか？」
- **DR-3** — The AI first-response script (`ai1`) shall show 「エスカレーション中」 for status 150 in its prompt (regenerate from `spec.json` with the new status map).
- **DR-4** — サポート責任者 (Manager) is not a required field. If it is empty, E7 has no recipient and REQ-003 is not met. 確認事項（案）: 「サポート責任者が未設定の問い合わせをエスカレーションした場合、どうしますか？（必須にする／エスカレーション不可にする／別の宛先に送る）」

Recommendation to the G2 reviewer: E1–E8 are complete for REQ-001…004, but **DR-1 changes what a user experiences on every escalation** and should be decided at G1 before P3 deploys E8.

## Migration

Not applicable (config-only). Rollback for P3/P5: redeploy the previous complete payload (D4). Rollback is safe only while no record has status 150 or a DateC value; after use, removing 150 or DateC becomes data-impacting (D11, A2) and needs its own decision.

## Verification status of the Pleasanter behaviour used

No Pleasanter environment was reachable in this session, so **no dev probe was done** and nothing was added to `pls-kb-pleasanter`.

| Behaviour relied on | KB evidence | Status |
|---|---|---|
| Process with `ChangedStatus`, `View.ColumnFilterHash` display condition on Status + ClassE | schema.md (Processes); D10 | verified (1.5.2) |
| Display condition enforced on API execution | D10 | verified (1.5.2) |
| `DataChanges` Type `InputDateTime` + `BaseDateTime "CurrentTime"` | schema.md lists both values | schema verified; writing into an `EditorReadOnly` column via a process is implied by the KB example (督促日時) but not stated as an entry → **P-1** |
| Process notification `Type 1`, `Address "[Manager]"`, placeholders `[ClassA]` | schema.md | verified for Body; placeholders in `Subject` → **P-3** |
| `Reminders[].Condition` = view Id | not in KB | **P-2** (affects DR-2 only, not E1–E8) |

Probes to run on **dev** before/at P3 (read-only first: `SetSiteSettings` with `ControlId=NewProcessDataChange` / `NewProcessNotification` / reminder dialog), then add the results to `pls-kb-pleasanter`:

- **P-1** InputDateTime data change fills an `EditorReadOnly` DateC column (and the field list of the InputDateTime dialog on the installed version).
- **P-2** Meaning of `Reminders[].Condition`.
- **P-3** Placeholders `[ClassA]` `[Title]` are expanded in a process notification `Subject`.

## Open points

- **O1** Confirm on dev/stg/prod exports that slot DateC has never held data (ledger has no history for it; probe not possible in this session).
- **O2** Probes P-1…P-3 above (not done — no reachable environment).
- **O3** Mail delivery (REQ-003 AC3) is not verifiable on dev; verified in stg by the customer (Q4).
- **O4** `ai1` is generated from `spec.json`, which is not in this repository; DR-3 needs that source.
- **O5** Derived requirements DR-1…DR-4 await P1/G1.
- **O6** Status CSS class `status-inprogress` and short label 「エ」 chosen by the designer; customer may prefer others (cosmetic, rung 1).

## Self-check (2026-11-05)

- `pls lint`: 1 issue — `L-SLOT-01 ledger allocates DateC but configuration does not define it` (expected: P3 to-do).
- `pls coverage`: REQ-001…004 GAP (expected: config not yet built in P3, tests come in P4).
- Checklist: every REQ maps to ≥ 1 element and every element to a REQ (E1–E8); highest rung 2; impacts raised as DR-1…DR-4; DateC allocated (O1 pending); config-only; traceability uses stable keys (`Columns[ColumnName]`, `Processes[Name]`, `Views[Id]`). Unverified behaviour is listed as probes P-1…P-3 rather than assumed.
