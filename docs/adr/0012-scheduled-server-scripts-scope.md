# ADR-0012: Scope of scheduled (background) server scripts

- **Status:** Proposed (2026-11-05) — probe done (BR3): no API → option B recommended
- **Date:** 2026-11-05
- **Deciders:** Nam
- **Related:** ADR-0001 (configuration scope, option B), ADR-0010 (job safety), D3, D7; plan Step 4c

## Context

The brownfield candidate runs **jobs implemented as server scripts** on a schedule. Site server scripts (`SiteSettings.ServerScripts`) run on record events (before/after create, update, …); they are exported, diffed and deployed by `pls` today. A script that runs **on a schedule** is expected to be configured outside `SiteSettings` (likely at tenant level). If so:
- `getsite` does not return it, so `pls export` does not see it;
- it is not in git, has no drift check and no diff;
- it is deployed by hand on each environment, which is one of the project's current pains.

The KB has no entry about scheduled scripts. Where they are stored, how they are scheduled and whether an API reads or writes them are **not verified** and must not be assumed (framework rule 5).

## Open questions

- [x] Where are scheduled server scripts stored and configured on 1.5.x? — **Tenant settings**, tenant management → サーバスクリプト (manual; D31).
- [x] Is there an API to read them? To write them? — **No.** None documented; read-only probe of `/api/tenants/get`, `/api/tenants/1/get`, `/api/tenants/gettenant`, `/api/items/1/gettenant` → 404 (BR3, 2026-11-05).
- [ ] How is the schedule expressed, and is it per environment? Do they run on dev today? — Schedule: 毎時 (5-minute steps) / 毎日 / 毎週 / 毎月 / 1回だけ + タイムゾーン. Per environment only from **1.5.7.0** (`BackgroundService.json` / `Service.json`). Whether they run on the candidate's dev: *project team*.
- [ ] Does the ~10 s server-script timeout (KB fact 8) also apply to scheduled scripts? — *probe*.
- [ ] Do the scripts contain SiteIds or other environment-specific values (D3)? — *inventory of the project's scripts*.

## Options

### Option A — Out of scope; runbook only
- Pros: no tooling.
- Cons: the most error-prone deployment stays manual and invisible to drift.

### Option B — Files in git + manual deploy + verification
- Pros: works even without a write API; diff, lint and review like other scripts; a read API (if any) gives drift.
- Cons: deploy stays manual; without a read API, verification is a person comparing text.

### Option C — Fully managed through the API
- Pros: same lifecycle as site configuration: export, diff, drift, release plan, apply, rollback.
- Cons: only possible if a read **and** write API exists and round-trips with 0 differences.

## Decision

**Decide by the probe (proposed):** read + write API that round-trips → **C**; read only → **B** with automatic drift; neither → **B** with a person's verification step, recorded in the release.

In every case:
1. **Layout:** `config/_tenant/scheduled-scripts/<name>.js` (body) + `_index.json` (name, schedule, enabled flag, per-environment values by `${env:x}`). Bodies use `${site:x}` / `${principal:x}`, never raw ids (D3).
2. **Lint:** the server-script rules apply (no top-level `const`/`let` where scripts are concatenated, D7; L-REF-01; L-SEC-01), plus `node --check`.
3. **Safety:** scheduled scripts count as **jobs** for ADR-0010; releases that add or change them follow its guards; dev runs them only when `jobs` is not `unknown`.
4. **Release:** a release that changes a scheduled script lists it in `plan.json` and in the diff report, with the deploy method (API or manual) and the verification step.
5. **KB:** the probe results become KB entries (storage, API, schedule, timeout) with `verified_on` (ADR-0009).

## Consequences

- Easier: scheduled jobs become reviewable and part of releases instead of hand-copied text.
- Harder / costs: a tenant-level area in `config/` that is not tied to a site; possibly a manual deploy step that the release must track.
- Follow-up: run the read-only probe on dev; choose B or C; implement export/unpack (and apply if C); add to the P3 and P5 skills.
