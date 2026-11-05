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

1. **Map each requirement to Pleasanter elements** (columns, choices/statuses, editor layout, views, プロセス, notifications, reminders, permissions, scripts). If a requirement needs a **site that does not exist yet**, decide its logical name, site type, relations and permissions with `references/new-sites.md` (creation: ADR-0007).
1b. **Permission design: a step of its own.** Derive the roles from the requirements (who registers, approves, views, may not change …).
   - For each role, define:
     - the Pleasanter **group**: reuse one the person names, otherwise propose a name such as `<project>_<role label>`;
     - its rights per site (read / create / update / delete / manage);
     - the process buttons it may press (access control, D20).
   - Write the **permission matrix** (role × site × operation, role × process) in the DES.
   - Write `design/roles.json`: `{"roles": {"<role>": {"principal": "Group", "group_name": "<name>", "description": "<who>"}}}`. The operator `admin` (the person's own user) is already bound by `pls init`.
   - Use only `${principal:<role>}` in the configuration.
   - The groups are created by the person **after G2**. `pls principals --env dev` then binds their ids by name. Nothing about groups is prepared before the design.
2. **Climb the ladder only when forced** (invariant I5, `references/ladder.md`). Record the rung for every element; anything at rung 3 or higher needs a written reason why lower rungs cannot work.
3. **Check feasibility against the knowledge base.** If a mechanism depends on behaviour not listed in `pls-kb-pleasanter`, **probe it on dev** (read-only discovery first, e.g. the `SetSiteSettings` dialog endpoint; a temporary setting on dev only if needed, restored afterwards) and add the result to the knowledge base. A probe counts as evidence only if it reproduces the combination the design relies on (permission + process + display condition, summary + existing children, …); say what the probe contained. A probe whose result can **change the design** (add or remove an element, a requirement or a classification) is a **G2 prerequisite**: run it before G2. If it cannot be run before G2, design the branch that is **safe if the expectation is wrong** (e.g. restrict a process with access control instead of relying on a read-only permission to hide its button) and present the probe as a confirmation, not as the decision — never present only the expected branch. Record rejected alternatives and why, citing the knowledge-base entry (e.g. a checkbox-based display condition is rejected because of D9).
4. **Allocate column slots** in `design/slot-ledger.json` using the existing entry shape: `"<slot>": {"label", "status": "allocated", "zone", "req"}` (add `"design": "DES-NNN"` when useful). Pick the first slot of the needed type that the ledger has never allocated, and record in the design that it must be confirmed empty in every environment's export. Never reuse a slot that held data (A2, ADR-0002).
5. **Impact analysis** with `references/impact-checklist.md`: every existing view, notification, reminder, aggregation, script and permission that the change touches. New impacts become derived requirements → back to P1/G1 (do not silently absorb them). For a site with scripts, run `pls xref --site <s>` and read `ops/xref/<s>.json`: it lists which scripts use each column and site you change (static text match — a name in a comment counts too, a name built at run time does not).
6. **Classify the change** (ADR-0004): config-only / data-impacting / permission-impacting, with reasons. Data-impacting changes need a migration plan in the design.
7. **Write `design/decisions/DES-NNN-<slug>.md`** (`references/des-template.md`): design table (element → setting → REQ), ladder rungs, rejected alternatives, impact table, classification, open points.
8. **Update `traceability.json`**: REQ → design ids and the config paths that P3 will create (`config/<site>/site.json#Processes[<name>]`, `#Columns[<slot>]`, `#Views[<id>]`, script files).
9. **Self-check**, run `pls lint` (L-SLOT-01 is expected to report ledger slots not yet in config — that is the P3 to-do list), hand over for **G2**. Never approve yourself (I4).

## Outputs (project repository)

```
design/decisions/DES-NNN-<slug>.md
design/slot-ledger.json
design/roles.json        # roles → Pleasanter groups (permission design, step 1b)
traceability.json
(pls-kb-pleasanter additions, in the framework repository, when you probed new behaviour)
```

## Checklist before G2

- [ ] Every approved REQ maps to at least one design element; every element maps to a REQ or to an impact item.
- [ ] Every element has a ladder rung; rung ≥ 3 has a reason.
- [ ] No reliance on unverified Pleasanter behaviour. Every probe that could change the design has run, or the design takes the branch that is safe if the expectation is wrong.
- [ ] Impact checklist completed; derived requirements raised, not absorbed.
- [ ] Slots allocated; no slot reuse with existing data.
- [ ] Classification stated; data-impacting → migration + rollback described.
- [ ] Permission-impacting → for each role, what it can see **and press** (process buttons, D19/D20) is stated, and a test with a user of that role is planned for P4 (TD-11).
- [ ] Principal IDs (permissions, process access control, notification recipients) are `${principal:x}` references, never raw IDs. The permission matrix is in the DES, and every role used is in `design/roles.json` with a group name (step 1b).
- [ ] Configuration paths in `traceability.json` use stable keys (`Name`, `ColumnName`, view `Id`).
- [ ] New sites: logical name, `ReferenceType` with reason, title per environment, relations, permissions, release order; built-in columns only from a skeleton export (`references/new-sites.md`).

## Example (illustrative — not a template to copy)

Equipment-loan site, requirement "総務 can send a reminder for overdue loans": a プロセス (rung 2) with display condition on Status + 返却期限 (not on a checkbox — D9), a data change stamping a new read-only date column in a free slot, a mail notification; rejected alternative: server script that loops over records (rung 3 not needed); impact: views and notifications that filter by status, scripts with status maps; classification config-only because nothing is removed and no existing data changes.
Your design depends on *these* requirements and *this* configuration — derive it, do not pattern-match the example.
