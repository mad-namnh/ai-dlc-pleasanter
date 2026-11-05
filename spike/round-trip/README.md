# Spike B4 — Pleasanter 1.5.x configuration round-trip

## Questions to answer

1. Does site configuration exported via the API/site package → re-imported → exported again come out **identical** to the original (after removing volatile fields such as IDs and timestamps)?
2. Which components do **not** survive and must be handled manually?
3. Does writing the same configuration twice give the same result (**idempotent**)?
4. Which fields of the configuration contain secrets / sensitive information?

## Decision criteria

| Outcome | Condition | Action |
|---|---|---|
| **Go** | Core components (columns, editor, grid, プロセス, ステータス制御, notifications, scripts, site permissions) round-trip 100%; manual part < ~20% of the checklist; idempotent | Decide ADR-0001 option B, move to the vertical slice |
| **Change direction** | Core passes but an important group (e.g. permissions, extended columns) does not round-trip | Narrow the git scope, write runbooks for manual parts, consider site packages instead of the API |
| **No-go** | Columns/editor/プロセス do not round-trip reliably, or not idempotent | Stop and revisit the strategy (ADR-0001 option C or another model) |

## Preparation

1. A Pleasanter 1.5.x environment on the **same patch** as the customer:
   - **Default: MADLAB internal dev Pleasanter** — declared as the `dev` environment in the config.
   - Optional: a local Docker instance (`env/README.md`) when a clean, resettable environment is needed.
2. On dev, create **a dedicated folder (フォルダ) for the spike**, e.g. `zz_spike_roundtrip`, and put its SiteId in `roundtrip_parent_id`. All sample sites and round-trip copies live there.
3. Create an API key for a tenant-admin user on dev (site APIs require it).
4. `cp scripts/config.example.json scripts/config.json` and set `environments.dev.base_url`. If dev uses an internal certificate, set the CA path in `ca_bundle`.
5. Put the API key in an environment variable (never in a file):
   - PowerShell: `$env:PLEASANTER_DEV_API_KEY = "..."`
   - bash: `export PLEASANTER_DEV_API_KEY=...`
6. Python 3.10+, no third-party packages.

If the machine running the scripts cannot reach dev (proxy / internal network), use the browser runner in `browser/` instead — it authenticates with the logged-in browser session and needs no API key.

### Write protection

| Environment | Writes allowed? |
|---|---|
| localhost | Yes |
| `role: "dev"` + `allow_write: true` | Yes — you must **retype the host name** to confirm (or pass `--yes`) |
| any other `role` (`stg`, `prod`, …) or missing | **Never**, even with `allow_write: true` |

Exports (read-only) work against any declared environment.

## Steps

### Step 0 — Confirm endpoints (30 min)

Check against the 1.5.x manual that the get/create/update site endpoints match `config.example.json` (`endpoints`). If they differ, change `config.json`, **not** the code.

### Step 1 — Create sample sites (2–3 h)

In the dev UI (inside the spike folder), create a set of sites that **covers the checklist** (`inventory-checklist.md`): at least one 期限付きテーブル (time-limited table) + one 記録テーブル (record table) linked to each other, with プロセス, ステータス制御, notifications, リマインダー (reminders), server scripts, client scripts, styles, site/column permissions, views, formulas, choices (選択肢).

> Do not use customer data in this step. Real configuration is only used in step 5, in an environment where it is allowed.

### Step 2 — Export

```bash
python scripts/export_sites.py --config scripts/config.json --env dev --label original
```
Output: `data/dev/original/<siteId>.json` (raw) and `.normalized.json`.

### Step 3 — "create" round-trip (new site from the exported configuration)

```bash
python scripts/roundtrip.py --config scripts/config.json --env dev --mode create --label original
```
Creates a new site under `roundtrip_parent_id`, exports it, diffs against the original → `data/dev/roundtrip-create/report.md`.

### Step 4 — "update" round-trip + idempotence

```bash
python scripts/roundtrip.py --config scripts/config.json --env dev --mode update --label original --repeat 2
```
Writes the original configuration back onto the same site twice, exports after each write, diffs. Writes 1 and 2 must not differ.

### Step 5 — Site packages

Export a site package of the same sites in the UI (or via `copysitepackage`) → import into another folder → repeat step 2 on the imported sites → compare. Record what site packages preserve that the API does not (and vice versa).

If allowed: repeat on **a copy of the customer's real configuration** (no data) in an environment the customer permits.

### Step 6 — Evaluate the built-in MCP (D1, optional)

Enable `Parameters/McpServer.json` on dev (if editing Parameters is allowed), connect, list the tools and note which are useful for the framework (configuration reads? records only?).

### Step 7 — Secret scan

```bash
python scripts/scan_secrets.py data/dev/original
```
Record which fields contain URLs, tokens, mail addresses, hostnames.

### Step 8 — Write the report

Fill in `report-template.md`, save as `report-YYYYMMDD.md` (sanitized), and update `docs/review-findings.md` and ADR-0001.

## Safety

- `scripts/common.py` blocks writes to any environment that is not localhost or a write-enabled dev (table above). Do not loosen this.
- Internal dev may be shared with other projects: work only inside the spike folder; never modify sites outside it.
- Never write to the original sample sites; round-trips run on copies.
- `data/` is gitignored. Never commit it.
- The `report.md` generated under `data/` prints **real values** (before/after) for your review — it may contain webhook URLs or person names. Only reports sanitized per `report-template.md` may leave `data/`.
- In `create` mode, cross-site references (links, lookups pointing to old SiteIds) will differ — flagged 🔗 in the report. This is evidence for cross-site ID resolution (A3), not a round-trip failure.
