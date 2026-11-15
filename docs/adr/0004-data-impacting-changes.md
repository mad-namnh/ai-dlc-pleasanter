# ADR-0004: Data-impacting changes and a dedicated gate

- **Status:** Accepted (2026-11-05) — Option A; Option B when a customer-side runner exists. Amended 2026-11-15 (nothing to convert)
- **Date:** 2026-11-04
- **Related:** review-findings A1, D4, ADR-0001, ADR-0002

## Context

On sites that already hold data, some configuration changes are effectively schema changes. Configuration can be rolled back from a snapshot; data cannot. Changes need automatic classification and a dedicated gate for the risky kind.

Spike round 1: omitting a column definition in an `updatesite` payload removes the definition (the column falls back to defaults). The effect on existing cell data has **not** been verified on a site with data yet.

## Open questions

- [x] Does removing a column definition via `updatesite` affect stored values? — **No** (1.5.2, probe 2026-11-05, D12): the value is hidden, survives API updates, and **reappears** when the slot is defined again.
- [x] Removing a choice / status in use — value stays on the record; the edit screen offers it as an orphan option (D12).
- [x] Bulk upsert — works with `Keys` (update matched, create others, D13). API updates create **no record versions** (D14) → a backup is the only way back.
- [ ] Effect of formula / display-type / validation changes on stored values — *later probe, when a slice needs it*
- [ ] Bulk upsert volume limits and performance — *first real migration*
- [ ] Does the customer require a DB backup before such changes? — *Customer IT (TD-02)*
- [ ] Does an administrator / site-manager key see every record of a site through the items API `get` (record permissions, default view filters)? The nothing-to-convert check counts what the key sees — *kb-verify probe (TD-53)*

## Proposed classification

| Class | Examples | Gate |
|---|---|---|
| **Config-only** | Labels, ordering, views, notifications, styles | Standard gate |
| **Data-impacting** | Reusing / repurposing a column slot, removing a column that holds data, changing choices in use, changing formulas that recompute values, changing workflow so old statuses become invalid | Dedicated gate: migration script + dry run on a copy of the data + rollback plan + business approver on the customer side |
| **Permission-impacting** | Site/record/column permission changes | Dedicated gate: permission matrix before/after |

## Options

### Option A — Classify with static rules on the diff
- Pros: deterministic, explainable
- Cons: the rule list must be maintained

### Option B — Static rules + query production for whether a slot holds data
- Pros: more accurate (removing an empty column ≠ removing a column with data)
- Cons: needs read access to production (via runner/operator)

## Decision

**Option A now, Option B once a customer-side runner exists (ADR-0003).**

Probes changed the meaning of "data-impacting": on 1.5.2 configuration changes do not *destroy* stored values (D12), they *hide or orphan* them, and a later reuse of the slot makes them visible again. The risk is wrong meaning, not lost bytes. So:

1. `pls classify` marks as data-impacting: column definition removed, choices/statuses removed, formula/default changed (static rules, D11/D12).
2. `pls plan` / `pls release-plan` **refuse** a data-impacting change unless `--migration DIR` holds:
   - `migration.json` — `site`, `keys` (business identifier columns for `bulkupsert`), the conversion (mapping or data), `rollback`; `pls migrate` sends only explicit `data` (the result of a mapping, as checked in the dry run) and, with `--rollback`, only `rollback.data` that a person prepared from `backup/`;
   - `backup/` — every record of the affected site exported **before** the change (`pls backup` over HTTP; needed because of D14);
   - `dry-run.md` — log of the conversion run on a copy of the site with a copy of the data.

   **Nothing to convert.** When the affected site holds no records, `migration.json` may say `"nothing_to_convert": true` with `"data": []` instead of `keys`, the conversion and `rollback` (an explicit flag; empty data alone is still refused). `backup/` and `dry-run.md` stay required as for any migration. The folder's `site` must be a site of the release with a data-impacting change. It is not allowed for production: `pls package` and a plan for a `role: prod` environment refuse it, because its check runs only through `pls migrate` and `pls apply`. `pls migrate` sends nothing: it reads the site live and records the folder as migrated only when the operator's key sees 0 records there (the API lists only records the key may read — KB D36), otherwise it refuses. `pls apply` reads each such site again after the confirmation, right before the first configuration write, and refuses the whole release, writing nothing, if any record is visible by then; a record created after that read and before `updatesite` is not caught (Pleasanter has no conditional write). `--rollback` skips such a folder (it sent nothing) and rolls back the others.
3. Order at release time: backup → conversion (`bulkupsert`) → configuration change → verification; rollback = configuration rollback + `bulkupsert` of the backup. Enforced by `pls migrate` (HTTP, guarded like `apply`; each run recorded in `plan.json` `migrations_run` before the call, `uncertain` when no answer arrives) and by `apply`, which refuses a release whose migrations have not run. Open question: whether records read back by `get` (with ids, timestamps) can be sent to `bulkupsert` unchanged on 1.5.x is not verified, so pls does not build a rollback from `backup/` itself. For a nothing-to-convert folder the conversion step is the live emptiness check, repeated by `apply`.
4. The slot ledger never re-allocates a slot that held data (D12 makes old values resurface).
5. Business approver on the customer side signs the migration at G4.

## Consequences

- The CLI needs a change-classification command, run in CI, with the result shown in the diff report.
- Each data-impacting change has a migration folder: script, dry-run log, rollback.
- As built (2026-11-15, settings coverage `plans/2026-11-15-settings-coverage/`): Pleasanter 1.5.2 records calculations in `SiteSettings.Formulas[]`, not in a column, so Decision 1's "formula changed" covers `Formulas[]` added / changed / removed (data-impacting; whether existing records are recomputed is source-derived only — the screen has 同期 / `SynchronizeFormulas`, no API route). Permission-impacting also covers `StatusControls[]` and the `Groups` / `Users` / `Depts` access lists of views, exports and dashboard parts.
- As built (2026-11-15, from the store-promo trial: a first master load was dropped from a config-only plan): a `--migration` folder given for a release that is **not** data-impacting — a data load such as a first master load — gets the same folder checks, is kept in `plan.json` and gets the same order (`pls migrate` before `apply`, `apply` refuses until it has run). Because the load runs before the configuration, it goes in a release of its own, **after** the release that defines the site's columns and keys: how `bulkupsert` behaves on columns or keys the site does not define yet is not verified on 1.5.x. The P5 skill text does not say this yet (tech debt).
