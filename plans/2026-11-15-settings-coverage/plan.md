# Plan — settings coverage for Pleasanter 1.5.2 (implementation plan)

- **Input:** `inventory.md` (this folder): 130 stored `SiteSettings` keys, 30 with round-trip evidence; 12 keys with environment-specific ids that are not (fully) mapped; 6 keys whose change class is wrong; 53 API routes, 15 used.
- **Goal (Nam, 2026-11-15):** the framework has the tools for most Pleasanter 1.5.2 settings, at least those the API supports.
- **"Has the tools" means** that for each setting a project can:
  1. design it with knowledge from the KB;
  2. keep it in git without environment-specific ids;
  3. classify a change to it correctly;
  4. deploy it without `--accept-unverified`;
  5. verify it after deploy.
- **Architecture fit:** P2 (design knowledge), P3 (`pack` / `unpack`, mapping), P5 (`release-plan`, classification, release steps); invariants I2 (complete payload), I4 (decisions by a person), I7 (no secrets), I9 (no claim without evidence); ADR-0001 (scope), ADR-0004 (change classes), ADR-0006 / D15 (principals), ADR-0009 / ADR-0023 (KB evidence), ADR-0025 / ADR-0026 (kb-verify safety).
- **Tier:** Critical overall (mapping, classification, guards). Each task below states its own tier.

## Principles

- **Evidence first (I9).** No key enters `VERIFIED_KEYS`, and no KB row says "verified", without a probe run on dev by the person (`pls kb-verify --env dev`, ADR-0023). The agent writes the probe files. Nam runs them, because writes to Pleasanter are his. The curator records the result.
- **Mapping before evidence for id-bearing keys.** A key that holds ids is unsafe on stg until its ids are mapped, whatever its round-trip evidence (workstream 1 before workstream 3 for those keys).
- **Decisions go to Nam.** ADR Decision changes (stop point 1), protected paths such as the template (stop point 3, patch only), and anything that writes to Pleasanter (stop point 5).
- **One item per commit,** with tests that fail on the parent and both suites green, as `HANDOFF.md` "How we work" requires.
- **YAGNI.** API surfaces that no customer app needs are recorded as tech debt with a trigger, not built (section 7).

## Milestones

| Milestone | Workstreams | Outcome | Needs from Nam |
|---|---|---|---|
| **M1: safe on stg** | WS1, WS2, WS6a | Every id in any key is mapped or refused. Every change is in its right class. | ADR-0006 / ADR-0004 amendment text; nothing on Pleasanter |
| **M2: scalars proven** | WS3a | About 90 scalar keys verified in 6 probe files. `VERIFIED_KEYS` grows from 30 to about 120. | one `kb-verify` run on dev (about 15 min) |
| **M3: open questions answered** | WS3c | `updatesitesettings` vs D40, formula recompute, view access | `kb-verify` run + 2 screen checks |
| **M4: missing tools** | WS4 | `pls summaries sync`, depts in `principals`, partial-update path if M3 proves it | ADR text for each new write path |
| **M5: attributes and design knowledge** | WS3b, WS5 | Column / view / notification attributes verified in batches; P2 designer knows them; evals | `kb-verify` runs; eval batch approval |

Rough size: M1 is 3–4 sessions; M2 is 2 sessions plus Nam's run; M3 is 1–2; M4 is 3; M5 is 4–6, spread over customer demand.

---

## WS1 — Environment mapping of every id (M1, Critical)

Today `to_refs` maps an integer under a key ending in `SiteId`, site ids in id contexts of strings (`[[id]]`, scripts — BR7), process access lists (`acl_to_refs`) and mail tokens of Notifications / Reminders / process notifications (`pls_address_principals`). Everything else passes through raw.

| Task | What | Files | Tests (fail on parent) | Acceptance |
|---|---|---|---|---|
| **1.1** Principal lists everywhere | Generalise `acl_to_refs` / `acl_from_refs` from `Processes[]` to every `Depts` / `Groups` / `Users` list in `SiteSettings`: `Views[]`, `Exports[]`, `DashboardParts[]`, `StatusControls[]`, `Create/Read/UpdateColumnAccessControls[]`. Driven by one table of paths, not a deep walk, so free-text lists are never touched. Unmapped ids stay raw and are reported. | `pls.py` (`ACL_KEYS`, new `ACL_PATHS`), `pls_scope.py` (drop the StatusControls principal refusal once mapped) | unpack → `${principal:x}` for each path; pack back to ids; unmapped id → L-PERM-01 issue and `pack` refusal; StatusControls with mapped principals is no longer reported by `unverified` | Round trip dev → stg payload holds the stg ids; no raw id in git |
| **1.2** `RecordUsers` / `AllowedUsers` | Find out (source) what `ColumnAccessControl.RecordUsers` holds: column names like `Owner`, or ids? Map only if they are ids. | source read, then `pls.py` | a test only if mapping is needed | an open question closed in the KB (source-derived) |
| **1.3** Site-id lists | `MoveTargets` (`List<long>`) and `IntegratedSites` (`List<string>`) → `${site:x}` per element. An id not in `environments.json` stays raw and is refused at pack (L-REF). | `pls.py` (`to_refs` / `from_refs` by path) | both directions; unknown id refused | — |
| **1.4** Dashboard site strings | `QuickAccessSites`, `TimeLineSites`, `CalendarSites`, `KambanSites`, `IndexSites` (text) and `*SitesData`. First read their format in the source (`DashboardPart.cs`: JSON text? comma list?). Then map site ids inside them. | `pls.py` or a small `pls_dashboard_refs.py` (if over 200 lines) | each part type; a type-0 quick-access part round-trips to `${site:x}` | type-0 parts no longer leak ids (their round-trip evidence comes in WS3b) |
| **1.5** Mail default tokens | `MailToDefault`, `MailCcDefault`, `MailBccDefault`: extend `pls_address_principals` from mail elements to these three top-level strings. `AddressBook`: literal addresses are customer data. Treat them like `${env:x}` values (L-ENV) or keep them out of git (decision for Nam). | `pls_address_principals.py`, `pls_side_effects.py` (`mail_elements`?) | `[Group<id>]` in `MailToDefault` → `[${principal:x}]` and back | — |
| **1.6** Ids inside view filters | **Probe first (WS3c-3).** If `ColumnFilterHash` for `Owner` / `Manager` / user columns stores user ids, map them through a `principals`-like table (`User,<id>`) or refuse them in git. | after the probe | — | decision recorded in ADR-0006 follow-up |

**ADR:** ADR-0006 (principals) and D15 name process access control and mail tokens. Extending the mapping to these paths changes its Decision scope, so it is **stop point 1**. Proposed text goes to Nam before 1.1 is committed.

**Lint:** L-PERM-01 (architecture.md 7.2) widens to the same path table. Its row text changes in the same commit.

---

## WS2 — Change classification (M1, Critical)

| Task | What | Files | Tests | Acceptance |
|---|---|---|---|---|
| **2.1** Formulas | `settings.Formulas[...]` added / changed / removed → **data-impacting**. Message: "stored values of existing records are not recomputed until 同期 (SynchronizeFormulas) is run on the screen (source-derived, probe WS3c-2)". Remove the dead `Columns[x].Formula` rule: 1.5.2 does not record that attribute, per `inventory.md` B. | `pls.py` `classify` | a formula change → data-impacting; the old path no longer matches | plan refused without `--migration`, or with a nothing-to-convert folder on an empty site (ADR-0004 amended 2026-11-15) |
| **2.2** Access lists | `StatusControls`, `Views[].Depts/Groups/Users`, `Exports[].Depts/Groups/Users`, `DashboardParts[].Depts/Groups/Users`, `NotInheritPermissionsWhenCreatingSite` → **permission-impacting**. | `pls.py` `classify` | each path | the permission matrix step of G2 / G4 lists them |
| **2.3** Choice control | `Columns[x].MultipleSelections` / `ChoicesControlType` changed → **data-impacting** if WS3b shows that multi-select stores a JSON array, otherwise config-only. Until then, data-impacting with the note "not verified". | `pls.py` | — | — |
| **2.4** Release step for formulas | If WS3c-2 confirms that there is no recompute: the P5 checklist (`pls package` CHECKLIST, release manager skill) names the screen step 同期 after a formula change, like TD-50 for links. | `pls_package.py`, P5 skill (eval) | checklist text test | — |

**ADR:** ADR-0004's classification table (Proposed classification / Decision 1) lists the static rules. Adding rows is **stop point 1**: text to Nam.

---

## WS3 — Evidence (KB probes; Nam runs them on dev)

The probe format is `skills/pls-kb-pleasanter/references/probes/*.json`. It uses `expect_stored` for what Pleasanter stores and `tests` for behaviour. kb-verify safety (ADR-0025 / ADR-0026): probe sites may hold **no notifications or reminders at any depth**, and records are only the probe's own.

### 3a. Scalar keys in batches (M2, Standard — probe files; Critical — `VERIFIED_KEYS`)

Each probe sets **non-default** values (D8: defaults are dropped) on its own probe site and expects them stored. One file per area, so a failure points to one area:

| Probe | Keys (from `inventory.md` A) | Count |
|---|---|---|
| D43-scalars-editor | SwitchRecordWithAjax, SwitchCommandButtonsAutoPostBack, AutoVerUpType, AfterCreateActionType, AfterUpdateActionType, AllowEditingComments, AllowCopy, AllowReferenceCopy, CharToAddWhenCopying, AllowSeparate, AllowLockTable, OpenEditInNewTab, DeleteImageWhenDeleting, GuideAllowExpand, GuideExpand, Responsive, HideLink, DisableLinkToEdit, EnableExpandLinkPath, GeneralTabLabelText | 20 |
| D44-scalars-grid-filters | GridPageSize, GridEditorType, HistoryOnGrid, AllowRestoreHistories, AllowPhysicalDeleteHistories, Use*Filter ×11, AlwaysRequestSearchCondition, DisableSiteConditions, AllowViewReset, SaveViewType, SearchType, FullText* ×4, LinkPageSize, LinkTableView | 30 |
| D45-scalars-view-modes | Enable* ×8, CalendarType, NoDisplayCrosstabGraph, ShowGanttProgressRate, ImageLibPageSize, FirstDayOfWeek, FirstMonth | 14 |
| D46-scalars-formulas-code | FormulasGetErrorDetails, OutputFormulaLogs, ProcessOutputFormulaLogs, ServerScriptsAllDisabled, ScriptsAllDisabled, StylesAllDisabled, HtmlsAllDisabled, ServerScriptsGetErrorDetails, ExtendedHeader, DashboardPartsAsynchronousLoading | 10 |
| D47-scalars-import-export-form | AllowStandardExport, StandardExportType, ImportEncoding, UpdatableImport, DefaultImportKey, RejectNullImport, AllowMigrationMode, FormStartDateTime, FormEndDateTime, FormUnavailableMessage, FormThanksMessage | 11 |
| D48-structure-lists | HistoryColumns, Sections + SectionLatestId, Tabs + TabLatestId, RelatingColumns, BulkUpdateColumns, PermissionForUpdating, Aggregations `Type` 1/2 + `Target` | 9 |

- **Steps:**
  1. Read each key's type and default from the source (the `RecordingData` condition), so the probe value is not the default.
  2. Write the probes.
  3. `pls kb-verify` dry check (no write) in the suite. Nam runs it on dev.
  4. The curator records each key (verified / failed / clamped) in `schema.md` with the probe name.
  5. Add the verified keys to `VERIFIED_KEYS`, with the probe as evidence in the docstring.
- **Acceptance:** `VERIFIED_KEYS` holds every key whose probe stored it as sent. Failed or clamped keys are recorded as such and stay out.
- **Not proven by these probes:** what each switch does on the screen. Design guidance for a switch is added only when a person observes it, or a behaviour probe exists (WS5).

### 3b. Attributes inside verified lists (M5, by demand)

| Probe set | Attributes | Why |
|---|---|---|
| Columns: validation | `Max`, `Min`, `Step`, `DecimalPlaces`, `MaxLength`, `NoDuplication`, `MessageWhenDuplicated`, `ValidateNumber/Date/Email/EqualTo`, `ClientRegexValidation`, `ServerRegexValidation` | common in business apps; which are checked on an API write (like D27 for required)? |
| Columns: choices and layout | `ChoicesControlType`, `MultipleSelections`, `NotInsertBlankChoice`, `Hide`, `GridLabelText`, `Section`, `CopyByDefault`, `TextAlign`, `ControlType` | multi-select storage (2.3), sections |
| Columns: auto-numbering | `AutoNumbering*` (column) and `Processes[].AutoNumbering` | "exists, not exercised" |
| Columns: attachments | `LimitQuantity`, `LimitSize`, `TotalLimitSize`, `BinaryStorageProvider`, … | stored values only |
| Views: modes | calendar ×12, gantt ×4, kanban ×7, time series ×5, per-view `GridColumns` / `FilterColumns`, command switches | view modes after `Enable*` (3a) |
| Processes | `AllowBulkProcessing`, `OnClick`, `Icon`, `ValidateInputs` regex / min / max, `AfterProcessStatusChangeActionType` | — |
| Dashboards | type 0 (after 1.4), type 5 kanban, index parts | BR3 left them out |
| Exports, column access control | stored shape; effect with test users (ADR-0018) | after 1.1 |
| Notifications / Reminders other types | **Not possible in kb-verify** (no notifications on probe sites, by safety design). Stored-shape evidence only from a person's round trip on a dev site with mail and webhooks disabled. That needs Nam's decision and maybe an ADR-0025 amendment. | webhook `Token` is a secret (I7, ADR-0005): pls must keep it out of git — check `L-SEC-01` covers `Notifications[].Token` |

### 3c. Open questions (M3)

| Probe | Question (`inventory.md` D) | Method |
|---|---|---|
| WS3c-1 `updatesitesettings` | Does a partial update of `Columns` (JSON link with `Lookups`) list the master on the screen without a screen save (D40 (C), TD-50)? | **New capability:** kb-verify only calls `updatesite`. This needs a guarded `updatesitesettings` step in kb-verify (ADR-0025 amendment) or a one-off probe by Nam with the person's screen check |
| WS3c-2 formula recompute | Does changing `Formulas[]` recompute existing records? Does `SynchronizeFormulas` exist on the screen? | kb-verify: create records, change the formula (second save), read values; screen check for 同期 |
| WS3c-3 view access and filter ids | Effect of `Views[].Groups`; storage of `Owner` filters | kb-verify with test-user roles (ADR-0026) |

---

## WS4 — Missing tools for API surfaces (M4)

| Task | What | Tier | ADR / stop point | Acceptance |
|---|---|---|---|---|
| **4.1** `pls summaries sync <release>` | Calls `SynchronizeSummaries` (source: `Summaries.Synchronize`) for each summary the release adds or changes. Guarded like `apply`: write guard, G4 on non-dev, typed confirmation, run log. Recorded in `plan.json` as a release step after `apply`. `release-plan` lists it when a summary changes (replaces the D16 note "NOT recalculated"). | Critical | new write path → ADR (amend ADR-0004 Decision 3 order: configuration → recalculation) — stop point 1 | fake-server tests; a dev run by Nam |
| **4.2** Depts in `principals` | `pls principals` reads depts (`/api/depts/get`) next to groups and users; `--create` on dev only, like groups. | Standard | none (ADR-0006 already names `Dept,<id>`) | `${principal:x}` resolves for a dept on dev and stg |
| **4.3** Partial-update deploy (conditional) | Only if WS3c-1 shows `updatesitesettings` makes JSON links work: `apply` sends the `Columns` / `Links` part through `updatesitesettings` after `updatesite`, or `pls links refresh`. Removes the manual screen step of TD-50. | Critical | ADR (new write path, ADR-0008 transport) — stop point 1 | D40 (C) closed by a probe |
| **4.4** Formula sync step | If WS3c-2 confirms that there is no recompute and no API route: a release step "person runs 同期 on the screen", recorded with `pls step` and in the P5 checklist (2.4). | Standard | — | — |

---

## WS5 — Design knowledge (M5, Standard; skill text → evals)

- **KB:** one `schema.md` row per verified key and attribute, with the probe as evidence (curator only, from the probe report).
- **P2 designer** (`pls-p2-solution-designer`), ladder rung guidance:
  - which verified switch or attribute meets a requirement before a script does (I5 ladder);
  - the impact checklist rows for 2.1–2.4 (formula sync, permission-impacting access lists).
- **P5 release manager:**
  - the summary sync and formula sync steps (WS4);
  - TD-52 (data load in its own release; nothing-to-convert dev/stg only);
  - TD-57 (Role tests only through `pls profile set`).
- **Lifecycle skill:** TD-57.
- **Evals:** one new case per changed skill section. Ask Nam before the batch (eval runs blind).

## WS6 — Lint and reporting

| Task | What | Tier |
|---|---|---|
| **6a** L-PERM-01 paths | Same path table as 1.1 / 1.3 / 1.5 (M1). | Critical |
| **6b** `pls scope` report | Per site: the keys and dashboard types without evidence, read from git, so P2 sees them at design time instead of at `release-plan`. Output follows `pls_scope.unverified`. | Standard |
| **6c** Secrets | Check `L-SEC-01` and `pack` refuse `Notifications[].Token`, `Reminders[].Token` and `Headers` with credentials (I7, ADR-0005); add paths if missing. | Critical |

## 7. Not built now (tech debt with a trigger)

| Item | Why not now | Trigger |
|---|---|---|
| CSV `Import` / `Export` of items | `migrate` (bulkupsert) covers master loads | a load of more than a few thousand rows, or a customer CSV process |
| `BulkDelete`, `Upsert` | test data is cleaned per record | test data of more than about 100 records per run |
| Binaries (site image, attachments) | site image is cosmetic; attachments are data | a design that depends on a site image |
| Extensions API, Extended SQL | tenant-wide; security review needed; no app uses it | a customer app on onboarding that uses extensions |
| Users update / import, sessions, outgoing mails, background tasks | operations, not configuration | — |
| Tenant settings, `Parameters/*.json` | not reachable by API | an onboarding finds a design that depends on them (record as a customer prerequisite) |

## Order of work (first steps)

1. **WS2.1 + 2.2** (classification). Small, high value. Needs the ADR-0004 text approved by Nam.
2. **WS1.1 + 6a** (principal paths). Needs the ADR-0006 text.
3. **WS1.3 – 1.5.**
4. **WS3a** probe files (agent) → Nam's kb-verify run → curator → `VERIFIED_KEYS`.
5. **WS3c** probes → decisions on 4.3 / 4.4.
6. **WS4.1, 4.2.**
7. **WS3b / WS5** as projects need them.

## Risks

| Risk | Mitigation |
|---|---|
| A scalar probe changes the behaviour of the probe site in a way that affects other probes | one probe site per probe file (ADR-0026 `sites`); teardown to defaults |
| `AllowMigrationMode`, `ServerScriptsAllDisabled` and similar switches change server behaviour on dev | the probe site is the probe's own; teardown restores; nothing else is on that site |
| Mapping a path that holds free text by mistake | a path table, not a deep walk; a test with text that contains digits |
| Evidence drifts after a Pleasanter upgrade | `pls version` check; the KB `verified_on` lists the build (ADR-0023); re-run the probes on upgrade |

## Unresolved questions (for Nam)

1. `AddressBook` / `Mail*Default` hold customer mail addresses. Should they stay in git as `${env:x}` values, or stay out of git (excluded from `pack`)?
2. Probing notification and reminder types needs a decision: a person's round trip on a dev site with sending disabled, or an ADR-0025 amendment that lets kb-verify create disabled notifications.
3. Priority between M2 (prove scalars, broad) and M3/M4 (D40 fix, summary sync, deep): the plan puts M1 → M2 → M3 → M4. Is that the right order?

## Decisions (Nam, 2026-11-15, verbatim "1. loai han khoi git, 2. sửa ADR-0025 để kb-verify được tạo notification ở trạng thái tắt, 3.ok")

1. `AddressBook`, `MailToDefault`, `MailCcDefault`, `MailBccDefault`: **excluded from git** (not packed, not unpacked; the live value is kept on deploy). WS1.5 changes accordingly: no token mapping for these keys; instead an exclusion with a test and an ADR text (stop point 1) when WS1.5 starts.
2. Notification / reminder probes: **amend ADR-0025** so kb-verify may create notifications and reminders that are disabled (`Disabled: true`), stored-shape only. Exact ADR text to Nam before WS3b notification probes.
3. Order M1 → M2 → M3 → M4: approved. First task: WS2 (classification).
