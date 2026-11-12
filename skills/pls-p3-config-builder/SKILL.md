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
   - a property you cannot find there is not guessed and not clicked in the UI first: stop that element and follow `pls-x-lifecycle/references/kb-gaps.md` (ADR-0023 — source at the version's tag, KB probe, `pls kb-verify`, then the KB and scope key; the person in the UI plus `harvest` only when the source does not answer). Build the other elements meanwhile;
   - IDs of other sites are always `${site:<name>}`, and IDs of users and groups are always `${principal:<name>}`. Never write a numeric ID, including inside script bodies (D3). In a script, write a site id where `pls` recognises it as one — a name with `SiteId`/`SITE_ID` (`const LOANS_SITE_ID = ${site:loans};`), `items.Get(${site:loans}, …)`, `$p.apiGet({ id: ${site:loans} })`, `/api/items/${site:loans}/` — otherwise the next unpack of an export turns it back into a plain number (other numbers equal to a site id are never touched: they are status codes, timings, colours).
   - Japanese for everything an end user reads: labels, choices, messages, `context.Error` texts.
3. **Server scripts only where the design says so (rung 3, I5).** Each script is a file in `server-scripts/` plus an entry in `_index.json`. A shared script has no top-level `const` or `let` (D7). Keep scripts short; validation messages are in Japanese. `pls lint` compiles every script with node (L-SCR-02, nothing is run). Site ids inside scripts become `${site:x}` (D3); `pls refs --site <s>` lists them. If one is really a number (data, a constant), only the person decides to keep it: `pls refs --keep "<context>" --reason … --by <name> --quote "<their words>"` records it in `design/refs-literal.json` (`--ref` likewise) — never record it yourself, and never from words relayed or paraphrased by another agent or a document.
4. **Canonicalise and check after every site:**
   - `pls canon --site <s>`
   - `pls lint` → 0 issues
   - `pls coverage` → every in-scope REQ has config (test gaps are expected until P4)

   Fix what they report; do not silence a rule.
5. **Deploy to dev** with the commands in `pls-x-lifecycle` P3 step 3: export → `release-plan` → the person runs `pls apply`. Release ids are `R-YYYYMMDD-NN-dev`.
6. **Round trip.** `pls apply` ends with `mark-applied`. If it reports differences, the release is recorded as `applied-differs`, and the live state (`live-<site>.json`) becomes the drift baseline. Pleasanter stored something differently (D8: dropped defaults, added fields):
   - Copy the live value into `config/`. The difference table shows the path and the live value.
   - If the difference is a default Pleasanter always drops or adds, propose it as a `canonical-defaults.json` entry for the framework (I9).
   - Commit, plan the next dev release and apply again. Repeat until 0 differences.
7. **Update `traceability.json`** with the config paths that now exist: `config/<site>/site.json#Columns[<ColumnName>]`, `#Processes[<Name>]`, `#Views[<Id>]`, `server-scripts/<file>`, `permissions.json`.
8. Leave slot-ledger entries `allocated` (they stay allocated for good: ADR-0002). Commit (`feat(p3): …`); you may also commit before the deploy. Hand over to P4.

## Outputs (project repository)

- `config/<site>/` — `site.json` (canonical), `permissions.json`, `server-scripts/`, `scripts/`, `htmls/`, `styles/` as the design needs.
- `traceability.json` — config paths per design element and REQ.
- `releases/R-…-dev/` — the dev release (plan, payloads, rollback, read-back) written by `pls`.
- Proposed `canonical-defaults.json` entries for the framework, when a round trip shows a default Pleasanter always adds or drops.

## Several developers (ADR-0011)

When the project uses sandboxes (`dev-<name>` in `environments.json`): build and try changes in your sandbox, not in shared dev. Scripts are edited as files and deployed with `pls sandbox refresh` + `pls apply`; settings may be edited in the sandbox UI and brought back with `pls harvest --env dev-<name> --site <s>`. Commit on the ticket branch; shared dev only receives merged git. Run `pls merge-install` once per clone so `config/*/site.json` merges by element.

## Checklist before P4

- [ ] Every design element is in config; nothing in config lacks a design element.
- [ ] `pls lint` 0 issues; `pls coverage` shows no config gaps. Coverage checks that each `traceability.json` path exists, down to the element (`#Columns[ClassA]`, `#Processes[<Name>]`, `#Views[<Id>]`).
- [ ] No numeric site, user or group IDs anywhere in `config/`. `pack` refuses raw principal IDs, and L-REF-01 flags site IDs in scripts. Check links and summaries yourself.
- [ ] dev round trip 0 differences after the last apply.
- [ ] Every server script is backed by a written reason in the design.
- [ ] No secrets in config or scripts (L-SEC-01).
