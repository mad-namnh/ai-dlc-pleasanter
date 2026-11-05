# ADR-0004: Data-impacting changes and a dedicated gate

- **Status:** Proposed
- **Date:** 2026-11-04
- **Related:** review-findings A1, D4, ADR-0001, ADR-0002

## Context

On sites that already hold data, some configuration changes are effectively schema changes. Configuration can be rolled back from a snapshot; data cannot. Changes need automatic classification and a dedicated gate for the risky kind.

Spike round 1: omitting a column definition in an `updatesite` payload removes the definition (the column falls back to defaults). The effect on existing cell data has **not** been verified on a site with data yet.

## Open questions

- [ ] Which configuration changes affect existing data on 1.5.x (display type, choices, formulas, validation, delete behaviour, …) — *Spike*
- [ ] Does removing a column definition via `updatesite` affect stored values? — *Spike round 2 (site with synthetic data)*
- [ ] Limits of the bulk upsert API (volume, performance, version history) — *Spike*
- [ ] Does the customer require a DB backup before such changes? — *Customer IT*

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

*(Not decided)* — Proposal: **A first, B once a runner exists** (ADR-0003).

## Consequences

- The CLI needs a change-classification command, run in CI, with the result shown in the diff report.
- Each data-impacting change has a migration folder: script, dry-run log, rollback.
