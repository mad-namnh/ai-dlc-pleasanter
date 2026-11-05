---
name: pls-p2-solution-designer
description: Phase P2 of AI-DLC for Pleasanter. Designs how G1-approved requirements are met in Pleasanter with the simplest mechanism (standard settings before code), allocates column slots, analyses impact on existing behaviour, classifies the change and updates traceability, ready for gate G2. Use after G1 and before any configuration is edited.
---

# pls-p2-solution-designer

**Goal:** for each approved requirement, decide *how* Pleasanter will meet it — as simply as possible — and prove nothing existing breaks.
**You do not edit `config/` here.** That is P3.

## Inputs

- G1-approved `requirements/REQ-*.md`.
- Current `config/<site>/` (unpacked), `design/slot-ledger.json`, `design/decisions/`, `traceability.json`.
- **`pls-kb-pleasanter`** — read `references/behaviours.md` and `references/schema.md` before choosing a mechanism.

## Procedure

1. **Map each requirement to Pleasanter elements** (columns, choices/statuses, editor layout, views, プロセス, notifications, reminders, permissions, scripts).
2. **Climb the ladder only when forced** (invariant I5, `references/ladder.md`). Record the rung for every element; anything at rung 3 or higher needs a written reason why lower rungs cannot work.
3. **Check feasibility against the knowledge base.** If a mechanism depends on behaviour not listed in `pls-kb-pleasanter`, **probe it on dev** (read-only discovery first, e.g. the `SetSiteSettings` dialog endpoint; a temporary setting on dev only if needed, restored afterwards) and add the result to the knowledge base. A probe counts as evidence only if it reproduces the combination the design relies on (permission + process + display condition, summary + existing children, …); say what the probe contained. Record rejected alternatives and why, citing the knowledge-base entry (e.g. a checkbox-based display condition is rejected because of D9).
4. **Allocate column slots** in `design/slot-ledger.json` using the existing entry shape: `"<slot>": {"label", "status": "allocated", "zone", "req"}` (add `"design": "DES-NNN"` when useful). Pick the first slot of the needed type that the ledger has never allocated, and record in the design that it must be confirmed empty in every environment's export. Never reuse a slot that held data (A2, ADR-0002).
5. **Impact analysis** with `references/impact-checklist.md`: every existing view, notification, reminder, aggregation, script and permission that the change touches. New impacts become derived requirements → back to P1/G1 (do not silently absorb them).
6. **Classify the change** (ADR-0004): config-only / data-impacting / permission-impacting, with reasons. Data-impacting changes need a migration plan in the design.
7. **Write `design/decisions/DES-NNN-<slug>.md`** (`references/des-template.md`): design table (element → setting → REQ), ladder rungs, rejected alternatives, impact table, classification, open points.
8. **Update `traceability.json`**: REQ → design ids and the config paths that P3 will create (`config/<site>/site.json#Processes[<name>]`, `#Columns[<slot>]`, `#Views[<id>]`, script files).
9. **Self-check**, run `pls lint` (L-SLOT-01 is expected to report ledger slots not yet in config — that is the P3 to-do list), hand over for **G2**. Never approve yourself (I4).

## Outputs (project repository)

```
design/decisions/DES-NNN-<slug>.md
design/slot-ledger.json
traceability.json
(pls-kb-pleasanter additions, in the framework repository, when you probed new behaviour)
```

## Checklist before G2

- [ ] Every approved REQ maps to at least one design element; every element maps to a REQ or to an impact item.
- [ ] Every element has a ladder rung; rung ≥ 3 has a reason.
- [ ] No reliance on unverified Pleasanter behaviour.
- [ ] Impact checklist completed; derived requirements raised, not absorbed.
- [ ] Slots allocated; no slot reuse with existing data.
- [ ] Classification stated; data-impacting → migration + rollback described.
- [ ] Permission-impacting → for each role, what it can see **and press** (process buttons, D19/D20) is stated, and a test with a user of that role is planned for P4 (TD-11).
- [ ] Principal IDs (permissions, process access control, notification recipients) are `${principal:x}` references, never raw IDs.
- [ ] Configuration paths in `traceability.json` use stable keys (`Name`, `ColumnName`, view `Id`).

## Example (illustrative — not a template to copy)

Equipment-loan site, requirement "総務 can send a reminder for overdue loans": a プロセス (rung 2) with display condition on Status + 返却期限 (not on a checkbox — D9), a data change stamping a new read-only date column in a free slot, a mail notification; rejected alternative: server script that loops over records (rung 3 not needed); impact: views and notifications that filter by status, scripts with status maps; classification config-only because nothing is removed and no existing data changes.
Your design depends on *these* requirements and *this* configuration — derive it, do not pattern-match the example.
