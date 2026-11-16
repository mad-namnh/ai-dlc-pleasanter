# ADR-0026: KB probes with several probe sites, updates of their own records and group variables

- **Status:** Accepted (2026-11-14, Nam) — option B
- **Date:** 2026-11-14
- **Deciders:** Nam
- **Related:** I5, I9 (`docs/architecture.md` §2); ADR-0009 (`kb-verify` and its safety rules), ADR-0023 (configuration shapes the KB does not cover — steps 4–6), ADR-0025 (guarded probes: server scripts, test-user keys — this ADR amends it as well); origin: trial `pls-trial-store-promo` DES-001, KB gaps G-1, G-5, G-8 (hand-over 2026-11-14, task log `plans/2026-11-14-kb-gap-store-promo-probes/`)

## Context

A design element that the KB does not cover is verified by a probe that `pls kb-verify` runs on dev (ADR-0023). Probes are confined by ADR-0009 / ADR-0025: one probe site, steps `create` / `get` / `list` / `exec` on that site, no `site`, `run_on` or `vars` key, ids only from the probe's own records and the administrator.

The trial design needs behaviour that this cannot express:

- **G-1** record permissions given at creation (`PermissionForCreating`): with a group column (`[[Groups*]]`) the record's permission goes to the group **stored in the column**, so the probe must write a role's group id into a record; the design also has a child site linked to the parent; and "a store user can update its own record, accounting cannot" needs an update step.
- **G-5** lookups (`Link.Lookups`): copying 単価 from a master record needs two sites, and "a later change of the master is not copied again" needs an update of the master and of the line.
- **G-8** whether a status control stops an API write of `Status` needs an update step.

The Pleasanter source answers the shapes (notes in the task log, `source-notes.md`), not what the server does. Nam (2026-11-14): extend `kb-verify` rather than leave these to projects.

## Options

### Option A — Keep the probe rules; these behaviours are tested in each project (P3/P4)
- Pros: nothing to build; the probe surface stays as reviewed.
- Cons: G-1, G-5 and G-8 stay "source-derived" in the KB; every project finds the answer again after G2 (what ADR-0023 set out to stop).

### Option B — Three additions, each confined to what the probe created (recommended)
1. **`update` step** — on a record created earlier by the same probe (`record: "$<saved>"`, checked when the file is loaded, like `get` / `exec`); with `expectHttp` for a refusal. `delete` stays forbidden. Added after review (2026-11-14, F1): a save name is never one of kb-verify's own variables (`today`, `admin_uid`, `group_<role>` …), a create expected to be refused saves nothing, saves do not cross specs, and the runner refuses a step on any record id that a create of the same spec did not return.
2. **Group variables** — `$group_<role>` is the group id of a role **declared in the probe's `roles`** and bound on the environment (`principals.<role>` = `Group,<id>`); only in step data. A guarded probe (ADR-0025) already requires that binding. No other principal id is available.
3. **Several probe sites** — `"sites": {"<key>": {"ReferenceType": …, "SiteSettings": {…}, "teardown": {…}}}` beside the main `site`:
   - each one is created under the probe folder with its own title `zz_kbprobe_<probe>__<key>` and the same own-site proof (folder, title, type, not an app site) before any write, kept in the same state file;
   - in any site's settings (and in `expect_stored`), `${probe_site:<key>}` (and `${probe_site:main}`) is replaced by that probe site's id — as an integer when it is the whole value, as text inside a string; an unknown key refuses the probe file;
   - a step may name `"site": "<key>"` (or `"main"`) for `create` and `list`; any other value, and `site` on a spec, stay forbidden; `exec` finds processes on the main site only;
   - no server script outside the main site's top-level settings, no notifications or reminders at any depth (ADR-0009 / ADR-0025 unchanged);
   - a guarded probe's extra sites get the same end as its main site: teardown saved without scripts, the roles' grant removed, then deleted and believed only on `getsite` 404 (ADR-0025 guard 6); an unguarded probe keeps its sites for reuse, like its main site;
   - the roles' grant (`roles`) is set on every site of the probe.
- Pros: G-1, G-5, G-8 become probes with evidence per version; every addition is limited to the probe folder, the probe's own sites and records, and the roles the probe declares.
- Cons: more code in `kb-verify` and a larger probe file to review; a multi-site probe leaves more sites to delete when a run stops; still no probe for a script that reaches another site (G-3 stays manual, ADR-0025 unchanged).

### Option C — As B without several sites
- Pros: smaller change.
- Cons: G-5 and the child site of G-1 stay manual.

## Decision

**Option B**, accepted by Nam on 2026-11-14 (AskUserQuestion, his answer: "Option B (Recommended)"). It keeps every probe write inside the probe folder, the probe's own sites and records, and the roles the probe declares.

## Consequences

- Easier: P2 designs with record permissions at creation, lookups and status controls on verified evidence; the KB entries move from "source-derived" to "verified on 1.5.2" after one `kb-verify` run.
- Harder: a role probe needs every role it declares bound and with a test user on the environment where it runs; a probe whose roles are missing is `error`, not `fail`.
- Built with this ADR: `pls_kbverify.py` (loader rules), `pls_kbverify_guarded.py` (extra-site teardown and deletion), `pls.py` `kb-verify` (site creation, substitution, per-step site, `$group_<role>`); tests in `tools/pls/tests/`.
