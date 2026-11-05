# ADR-0004: Data-impacting changes and a dedicated gate

- **Status:** Accepted (2026-11-05) — Option A; Option B when a customer-side runner exists
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
   - `migration.json` — `site`, `keys` (business identifier columns for `bulkupsert`), the conversion (mapping or data), `rollback`;
   - `backup/` — every record of the affected site exported **before** the change (runner `backupRecords`; needed because of D14);
   - `dry-run.md` — log of the conversion run on a copy of the site with a copy of the data.
3. Order at release time: backup → conversion (`bulkupsert`) → configuration change → verification; rollback = configuration rollback + `bulkupsert` of the backup.
4. The slot ledger never re-allocates a slot that held data (D12 makes old values resurface).
5. Business approver on the customer side signs the migration at G4.

## Consequences

- The CLI needs a change-classification command, run in CI, with the result shown in the diff report.
- Each data-impacting change has a migration folder: script, dry-run log, rollback.
