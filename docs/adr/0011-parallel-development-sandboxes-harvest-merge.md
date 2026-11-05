# ADR-0011: Parallel development — sandboxes, harvest and semantic merge

- **Status:** Proposed (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** Nam
- **Related:** I1, I2; ADR-0002 (slot ledger), ADR-0007 (creating sites); review-findings A2; plan Step 4c

## Context

The framework so far assumed **one agent and one person** changing one dev environment. The brownfield candidate has **three developers** changing configuration at the same time, mostly on one shared dev, and its main screen (custom layout in `Htmls` / `Scripts` / `Styles`) is touched by almost every ticket.

How the team works today, and what that means here:
- Settings (columns, views, processes, notifications) are edited in the Pleasanter UI. That is fast and should stay possible; the framework must turn UI edits into reviewable changes instead of forbidding them.
- Scripts and HTML are long text. They are better edited as files, with diff, lint and syntax checks.
- On a shared dev, an export taken for one ticket also contains everybody else's unfinished edits.
- `site.json` holds lists (`Columns`, `Processes`, `Views`, `Notifications`, …). Two developers adding two different columns produce a git conflict on list positions although the changes are independent.
- Column slots (ADR-0002) and element ids (view `Id`, notification `Id`) are allocated per site; two developers can take the same one.

## Open questions

- [ ] Are three extra copies of the actively changed sites acceptable on the customer's dev (size, licences, naming)? — *project lead / customer*.
- [ ] Do element ids referenced elsewhere (e.g. a summary's `SourceCondition` = view `Id`) survive renumbering, or must ids be allocated like slots? — *design + probe*.
- [ ] Does creating a sandbox by `createsite` + full `updatesite` (the verified bootstrap path, D26) reproduce every component the project uses, including `Htmls`/`Scripts`/`Styles` and dashboards? — *spike (plan BR3)*.

## Options

### Option A — Shared dev with a site lock per ticket
- Pros: no new tooling; simple rule.
- Cons: the main screen becomes a bottleneck (one ticket at a time); exports still mix work if someone forgets the lock; no help with merges.

### Option B — Per-developer sandboxes + harvest + semantic merge; shared dev becomes integration only
- Pros: developers work in parallel, including on the main screen; every change reaches git as a branch and a pull request; shared dev only ever runs merged configuration, so tests there mean something.
- Cons: new tooling (sandbox, harvest, merge driver); extra sites on dev; ids and slots need allocation rules.

### Option C — One full Pleasanter instance per developer (e.g. containers)
- Pros: complete isolation, including tenant-level settings.
- Cons: heavy to run and keep in sync with the customer's version and parameters; data and settings outside sites still diverge; far beyond what the team needs now.

## Decision

**Option B (proposed).**

1. **Environments.** Each developer gets an environment `dev-<name>` (`role: dev`, own parent folder, same principals as dev). Shared `dev` becomes the **integration** environment: it only receives releases built from merged git; manual edits there are drift and are reported.
2. **`pls sandbox create|refresh|drop --name <name> --sites <a,b,…>`.** Creates the sites in the developer's folder (bootstrap path, ADR-0007) and deploys the current git configuration to them. `${site:x}` references make the different ids harmless. No business data is copied; tests create their own records.
3. **Editing rule by component:**
   - server scripts, client scripts, HTML, CSS → edit the files in `config/`, deploy to the sandbox with `apply`;
   - columns, views, processes, notifications, standard layouts → edit in the sandbox UI, then harvest;
   - permissions → designed in P2 (`design/roles.json`), edited in `permissions.json`.
4. **`pls harvest --env dev-<name> --site <s>`**: export → unpack → canon into the working tree on the ticket branch, refusing when the tree has uncommitted changes; prints the diff. The pull request description (Japanese summary for business reviewers) is written by the agent from the `pls` diff (I6).
5. **Semantic merge driver** (`pls merge-site`, registered through `.gitattributes` for `config/*/site.json`): merges lists by stable keys (`ColumnName`, process `Name`, view and notification `Id`, script `Name`), as `pls diff` already compares them. A conflict remains only when both sides changed the **same** element; it is shown with both versions.
6. **Allocation:** column slots stay in the slot ledger (ADR-0002), allocated in P2 and committed **before** building, so the first commit wins. Element ids follow the same rule (an `ids` section per site in the ledger), unless the open-question probe shows that renumbering is safe.
7. **Daily drift check** on each sandbox and on integration dev: unharvested edits are reported early, not at release time.

## Consequences

- Easier: three developers work in parallel; every change is reviewed as a diff; integration dev always equals git.
- Harder / costs: new commands and a merge driver with tests; extra sites on dev; the slot/id ledger becomes a shared resource that must be committed first.
- Follow-up: implement `sandbox`, `harvest`, `merge-site` (unit tests with conflicting and non-conflicting list edits); extend the ledger with ids; add the workflow to the P3 skill and a team guide in `docs/`.
