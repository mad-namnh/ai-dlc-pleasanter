---
name: pls-p3-config-builder
description: Phase P3 of AI-DLC for Pleasanter. Builds the G2-approved design into the unpacked configuration in git (config/<site>/ site.json, scripts, permissions), keeps it canonical and lint-clean, and deploys it to dev as a dev release until the round trip shows 0 differences. Use after G2, and whenever P4 sends a build defect back.
---

# pls-p3-config-builder

**Goal:** git holds exactly the configuration the design describes, in Pleasanter's canonical form, and dev runs it.
**You build what G2 approved, nothing more.** If the design is wrong or silent, stop and go back to P2/G2. Do not decide it here.

## Inputs

- `design/decisions/DES-*.md` (G2 approved), `design/slot-ledger.json`, `traceability.json` (config paths P2 planned).
- `config/<site>/` — for a new app, the skeleton unpacked after bootstrap. See `pls-x-lifecycle` P3 step 1.
- `pls-kb-pleasanter` — `references/schema.md` for property names and values, `behaviours.md` for traps.
- `references/config-layout.md` (this skill) — the files under `config/` and the reference syntax.

## Procedure

1. **List the work.** For each design element, write down the config path it becomes, taken from `traceability.json`. `pls lint` reports L-SLOT-01 for every slot the ledger allocates but the config does not use yet. That is your to-do list.
2. **Edit the config, one site at a time, smallest change first:**
   - columns, then editor/grid/filter layout, then views, then processes, then summaries/links, then permissions, then scripts;
   - property names and values only from KB `schema.md`, or from an existing export of the same environment;
   - a property you cannot find there is a probe for P2, not a guess;
   - IDs of other sites are always `${site:<name>}`, and IDs of users and groups are always `${principal:<name>}`. Never write a numeric ID, including inside script bodies (D3).
   - Japanese for everything an end user reads: labels, choices, messages, `context.Error` texts.
3. **Server scripts only where the design says so (rung 3, I5).** Each script is a file in `server-scripts/` plus an entry in `_index.json`. A shared script has no top-level `const` or `let` (D7). Keep scripts short; validation messages are in Japanese.
4. **Canonicalise and check after every site:**
   - `pls canon --site <s>`
   - `pls lint` → 0 issues
   - `pls coverage` → every in-scope REQ has config (test gaps are expected until P4)

   Fix what they report; do not silence a rule.
5. **Deploy to dev** with the commands in `pls-x-lifecycle` P3 step 3: export → `release-plan` → the person runs `pls apply`. Release ids are `R-YYYYMMDD-NN-dev`.
6. **Round trip.** `pls apply` ends with `mark-applied`. If it reports differences, Pleasanter stored something differently (D8: dropped defaults, added fields):
   - Copy the live value into `config/`. The difference table shows the path and the live value.
   - If the difference is a default Pleasanter always drops or adds, propose it as a `canonical-defaults.json` entry for the framework (I9).
   - Commit, plan the next dev release and apply again. Repeat until 0 differences.
7. **Update `traceability.json`** with the config paths that now exist: `config/<site>/site.json#Columns[<ColumnName>]`, `#Processes[<Name>]`, `#Views[<Id>]`, `server-scripts/<file>`, `permissions.json`.
8. Leave slot-ledger entries `allocated` (they stay allocated for good: ADR-0002). Commit (`feat(p3): …`); you may also commit before the deploy. Hand over to P4.

## Checklist before P4

- [ ] Every design element is in config; nothing in config lacks a design element.
- [ ] `pls lint` 0 issues; `pls coverage` shows no config gaps. Coverage only checks that the file in each path exists, not the `#…` part (TD-14), so check each `traceability.json` path against `site.json` yourself.
- [ ] No numeric site, user or group IDs anywhere in `config/`. `pack` refuses raw principal IDs, and L-REF-01 flags site IDs in scripts. Check links and summaries yourself.
- [ ] dev round trip 0 differences after the last apply.
- [ ] Every server script is backed by a written reason in the design.
- [ ] No secrets in config or scripts (L-SEC-01).
