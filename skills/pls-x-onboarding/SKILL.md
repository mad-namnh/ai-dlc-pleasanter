---
name: pls-x-onboarding
description: Brings an existing Pleasanter application (a project in 運用保守, built without this framework) into a project repository, read only, and leads the person through one decision per finding. Covers version, mail/job safety, adopting sites, comparing environments, components without round-trip evidence, principals and scripts. Use before the first P1 of an existing app, or when a site that exists in Pleasanter is not yet in the project.
---

# pls-x-onboarding — take over an existing app

**Goal:** git holds the configuration of the existing app as it runs, every environment is compared with it, and every finding has a decision by the person. **Nothing is written to Pleasanter in this skill.**

Commands here only read Pleasanter (`getsite`, the login page) or local files. Writes (`sandbox`, `bootstrap`, `apply`) belong to P3 after the gates.

## Inputs

- The project repository (`pls init`), the operator's connection for the environments MADLAB can reach.
- From the person: the site ids per environment; **site packages** (UI export) for environments MADLAB cannot reach (often prod). Packages go to `.pls/packages/` (gitignored) — never into a tracked folder.

## Procedure

0. **Environments.** Each environment needs an entry in `environments.json`. Propose the exact entry (name, `role`: dev/stg/prod, `parent_id` if known); after the person approves it you write the entry, and the role only with `pls profile set role <dev|stg|prod> --env <name> --approver <name> --quote "<their words>"` — a role is the person's decision, never edited by hand (lint L-PRF-01); `side_effects` and the local `allow_write` are only ever set by the person; `role: prod` is never writable. An environment with neither a connection nor a site package stays an open point (ask for a package).
1. **Version per environment** (ADR-0009). `pls version --env <e>`; for a package `pls version --env <e> --from-package <file>`. If the label is unknown, ask the person to read `<url>/versions`. Every environment whose version differs from dev is a **finding**: the KB is verified on the dev version only, so releases there carry a version note at G4.
2. **Mail and scheduled jobs** (ADR-0010). Ask the person how each environment sends mail (SMTP, sink, disabled) and whether scheduled jobs run there. They record `side_effects` in `environments.json` by hand (there is no command); you never set it. While dev's mail is `unknown`, P4 cannot test sites with notifications — say so. While the project declares scheduled scripts (step 8) and dev's `jobs` is `unknown`, P4 cannot run tests that change records.
3. **Adopt** the sites on the environment MADLAB can read (usually dev). With a site package of the app's folder (the only way to list a folder's sites): `pls adopt-package --env <e> --package .pls/packages/<file> --names <file>` — one read-only run, referenced sites first, re-mapped at the end; a second environment needs no names file (titles known). Propose the names file (`{"<site id>": "<name>", "<id to skip>": null}`), the person confirms it. Without a package: `pls adopt --env <e> --site <id> --name <logical>`. Logical names are lower case and stable and cannot be changed later: propose them, the person confirms. Adopt referenced (parent) sites first when you know them. Read the report in `ops/adopt/`; the export used is `.pls/exports/<env>-<name>-adopt-<stamp>.json`. Commit after each adopt (`feat(onboarding): adopt <name> from <env>`).
   - **Unmanaged references** in the report: adopt those sites too, or ask whether they stay outside the project. After adopting a referenced site later, re-map the first one: `pls unpack .pls/exports/<env>-<first>-adopt-<stamp>.json --env <env> --site <first>`, then `pls canon --site <first>` and check `pls drift` is still 0.
   - Adopt the same site on a second reachable environment with the same name: only its id is registered and the report shows how it differs from git.
4. **Compare environments** (BR5): `pls env-compare --site <s> --source git --source dev=<export> --source prod=<package>`. For every difference, ask the person and record the answer:
   - `content` → intended per-environment value (move it to `values` and `${env:x}`) **or** drift (decide: adopt as the truth, or revert later in P6);
   - `id-like` → adopt or map that id;
   - `not-in-package` → ask for a package exported with that part.
5. **Components without round-trip evidence** (ADR-0001, `pls_scope`): list them per site. For each, the person decides: probe it on a copy in dev before the first release, or accept it with a decision record (`--accept-unverified`). You never write that record. A probe is not part of onboarding (no writes here): record it as a task before the first release; it is run later with the person's go, like the BR3 spike (`spike/round-trip/scripts/br3_probe.py`).
6. **Principals.** Record which groups the site uses (names from the site package `PermissionIdList`, or ask the person). The role design itself belongs to P2 step 1b; after it, `pls principals --env <e>` binds the groups by name.
7. **Scripts** (BR7): `pls lint` (L-SCR-02 syntax), `pls refs --site <s> --summary` — numbers written as site ids are already `${site:x}`; numbers that only equal a site id stay as written and are listed as POSSIBLE. Do not ask about every POSSIBLE line: group them (status codes, timings, colours, comments) and ask only about lines that may really address a site; only the person marks one (`--ref … --by <name>`) or keeps a recognised one literal (`--keep … --by <name>`). The scripts are never refactored in onboarding. `pls xref --site <s>` for the index.
8. **Scheduled server scripts** (ADR-0012, tenant settings, no API): ask the person for the list; they are kept as files under `config/_tenant/scheduled-scripts/` (`<name>.js` + `_index.json`: a list of `{"name", "schedule", "enabled"}`, lint L-JOB-01) and deployed by hand. Declaring them turns on the jobs guard (ADR-0010): release plans list changed ones with a manual step.
9. **As-is specification:** only for the sites the first change request touches (and later, per change request, the sites it touches) — hand over to `pls-x-spec-recovery`, which starts from `pls spec-skeleton`.
10. **Record** `ops/onboarding/<date>-summary.md`: environments and versions, sites adopted, each finding with its decision and who decided, open points. Commit (`feat(onboarding): …`).

## Stop and ask

At every decision in steps 2–8. Present the finding, the options and your recommendation; record only what the person says.

## Never

- write to Pleasanter; set `side_effects`, `allow_write` or roles; record literal or acceptance decisions yourself;
- copy business data (records) anywhere; put a site package or export into a tracked folder;
- "fix" a difference between environments here — differences are decided, changes go through P1.
