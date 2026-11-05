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

1. **Version per environment** (ADR-0009). `pls version --env <e>`; for a package `pls version --env <e> --from-package <file>`. If the label is unknown, ask the person to read `<url>/versions`. Note every environment whose version differs from dev.
2. **Mail and scheduled jobs** (ADR-0010). Ask the person how each environment sends mail (SMTP, sink, disabled) and whether scheduled jobs run there. They record `side_effects` in `environments.json`; you never set it.
3. **Adopt** each site on the environment MADLAB can read (usually dev): `pls adopt --env <e> --site <id> --name <logical>`. Logical names are lower case and stable. Read the report in `ops/adopt/`.
   - **Unmanaged references** in the report: adopt those sites too, or ask whether they stay outside the project.
   - Adopt the same site on a second reachable environment with the same name: only its id is registered and the report shows how it differs from git.
4. **Compare environments** (BR5): `pls env-compare --site <s> --source git --source dev=<export> --source prod=<package>`. For every difference, ask the person and record the answer:
   - `content` → intended per-environment value (move it to `values` and `${env:x}`) **or** drift (decide: adopt as the truth, or revert later in P6);
   - `id-like` → adopt or map that id;
   - `not-in-package` → ask for a package exported with that part.
5. **Components without round-trip evidence** (ADR-0001, `pls_scope`): list them per site. For each, the person decides: probe it on a copy in dev before the first release, or accept it with a decision record (`--accept-unverified`). You never write that record.
6. **Principals.** From the group names (site package `PermissionIdList`, `/api/groups/get`), propose `design/roles.json`; after the person agrees, `pls principals --env <e>`.
7. **Scripts** (BR7): `pls lint` (L-SCR-02 syntax), `pls refs --site <s>` — show every SUSPICIOUS line; only the person keeps a number literal (`--keep … --by <name>`). `pls xref --site <s>` for the index.
8. **Scheduled server scripts** (ADR-0012, tenant settings, no API): ask the person for the list; they are kept as files under `config/_tenant/scheduled-scripts/` and deployed by hand.
9. **As-is specification:** hand over to `pls-x-spec-recovery` for every adopted site.
10. **Record** `ops/onboarding/<date>-summary.md`: environments and versions, sites adopted, each finding with its decision and who decided, open points. Commit (`feat(onboarding): …`).

## Stop and ask

At every decision in steps 2–8. Present the finding, the options and your recommendation; record only what the person says.

## Never

- write to Pleasanter; set `side_effects`, `allow_write` or roles; record literal or acceptance decisions yourself;
- copy business data (records) anywhere; put a site package or export into a tracked folder;
- "fix" a difference between environments here — differences are decided, changes go through P1.
