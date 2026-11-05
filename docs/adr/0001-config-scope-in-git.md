# ADR-0001: Scope of configuration managed in git

- **Status:** Proposed
- **Date:** 2026-11-04
- **Related:** review-findings B4, D3, D4, D6, ADR-0004, ADR-0005

## Context

The source of truth of a Pleasanter project is configuration stored in the database. The framework can only control what it can reliably export to files and re-import. On 1.5.x, the SiteSettings schema is not documented field by field. The scope must be based on **round-trip spike results**, not assumptions.

## Open questions

- [ ] Which components round-trip 100% through the site API (see `spike/round-trip/inventory-checklist.md`)? — *Spike*
- [ ] Do site package export/import preserve things the site API does not? — *Spike* (round 1: yes, structured cross-site references are remapped — D6)
- [ ] Are server-side files (`Parameters/`, extended SQL, …) brought under management; who can read/write them? — *Customer IT*
- [ ] Users / groups / departments: managed in git, or treated as reference data owned by the customer? — *Customer*
- [ ] Do dashboards, aggregation pages and tenant-level settings round-trip? — *Spike*

## Options

### Option A — Manage only what round-trips 100%
- Pros: safe; git always reflects reality
- Cons: the rest is manual and may be large

### Option B — Also manage partially round-tripping parts, with manual runbooks
- Pros: broader coverage; everything is documented
- Cons: git may diverge from reality for the manual parts; needs post-deploy verification

### Option C — Add direct database reads/writes for what the API does not cover
- Pros: near-complete coverage
- Cons: high risk; depends on internal DB structure; hard to get customer approval and to survive version upgrades

## Spike results, round 1 (2026-11-05)

- getsite/createsite/updatesite round-trip with **0 differences**, idempotent, on 1.5.2.
- `updatesite` replaces the whole configuration (desired state) — D4.
- Site packages remap structured references; the API does not — D6. Neither handles SiteIds inside scripts — D3.
- Only 8/15 core components covered so far; round 2 must add 期限付きテーブル (time-limited tables), 計算式 (formulas), プロセス (processes), ステータス制御 (status control), client scripts, permissions.

## Spike results, round 2 — BR3 (2026-11-05)

`spike/round-trip/report-br3-20261105.md`: `Htmls`, `Scripts`, `Styles` and dashboard parts of types 1, 3 and 4 round-trip with 0 differences, raw and through `pls` (D29, D30). Dashboard parts of types 1/4 need `View` (HTTP 500 otherwise). Background server scripts are tenant settings without an API (D31, ADR-0012). The components with evidence are listed in `tools/pls/pls_scope.py`; `release-plan` refuses a site using any other component unless a person accepts it with `--accept-unverified <decision record>`. This puts option B into practice: everything else is either probed first or accepted explicitly.

**Known limits (code review, 2026-11-05):**
- The check is per **top-level key**. Attributes inside a verified key that were never used on the evidence sites pass unchecked: per-column extended HTML/CSS and regex validation in `Columns`, webhook notifications, calendar/kanban/gantt settings in `Views`, unused flags of `Processes` / `ServerScripts`, `Htmls.PositionType` other than 1000/1010. A second-level allowlist for the risky ones is a follow-up (BR4 lists them per site when a project is adopted).
- Dashboard parts are checked one level deeper: type, and `View` on types 1/4/5 (HTTP 500 otherwise, D30).
- One decision record accepts every finding of the release; the plan stores the findings and the record's sha256.
- The single-site `pls plan` has no scope check; its plans cannot be applied over HTTP (multi-site `release-plan` only).

## Decision

*(Not decided — waiting for spike round 2)*

Initial proposal: **B**, provided the manual part is below ~20% of checklist components and contains no high-risk components (permissions, workflow). Do not choose C without a very strong reason.

## Consequences

- The in-scope list becomes the input for the CLI unpack/pack and JSON schema validation.
- Out-of-scope parts need runbooks and post-deploy verification steps.
