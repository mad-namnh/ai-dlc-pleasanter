# ADR-0006: Site permissions in git (opt-in, logical principals)

- **Status:** Accepted (2026-11-05)
- **Date:** 2026-11-05
- **Deciders:** Nam (tech lead)
- **Related:** review-findings C3, D15; invariants I1, I4; ADR-0004 (permission-impacting class)

## Context

Until now `pls` managed `SiteSettings` only. Site permissions (`InheritPermission`, `Permissions`) were invisible to drift checks, so a customer admin granting access in the UI went unnoticed, and the permission-impacting class of ADR-0004 had nothing to look at except column access control.

Probe on 1.5.2 (D15): `updatesite` accepts both keys and replaces the permission list when given; when they are omitted, permissions stay untouched. Entries are `Type,Id,Value` (`User,1,511`), and user/group/dept IDs differ per environment.

## Options

### Option A — Always manage permissions
- Pros: complete desired state
- Cons: every project must map every principal before the first deploy; a wrong mapping changes who can see customer data

### Option B — Opt-in per site, logical principals
- Pros: no change for sites that do not opt in (keys omitted → untouched); IDs never cross environments
- Cons: sites that do not opt in still have unmanaged permissions (reported, not enforced)

## Decision

**Option B.**

- `config/<site>/permissions.json` = `{"inherit": "${site:x}", "entries": ["${principal:name},<value>", …]}`, written by `pls unpack` from the export.
- `environments.json` → per environment `"principals": {"name": "Group,2"}`.
- `pls pack` / `plan` send `InheritPermission` + `Permissions` **only** when the site has `permissions.json`; raw (unmapped) IDs are refused (L-PERM-01).
- Drift, diff and classify include permissions for opted-in sites; a permission change is **permission-impacting** (dedicated gate, ADR-0004).
- The permission matrix (`design/permissions.md`, role × site × operation) is the human-readable source; checking *effective* access per role needs one test user per role per environment (TD-11).

## Consequences

- Projects that opt in must keep `principals` complete for every environment, including production (filled by the customer's operator; names only in git).
- A deploy with a stale principal mapping fails at `pack` time instead of granting wrong access.
