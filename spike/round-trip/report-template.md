# Round-trip spike report — YYYY-MM-DD

> This report is committed to the framework repository → it must be **sanitized**: no site names, person names, internal URLs or customer configuration values.

## Environment

- Pleasanter: 1.5.__.__ (exact patch)
- PostgreSQL: __
- Configuration source: self-made sample sites / copy of customer configuration (environment: __)
- How it was run: Python scripts with API key / browser runner with session

## Results per question

| Question | Result | Evidence |
|---|---|---|
| 1. Identical round-trip (create) | | `data/dev/roundtrip-create/report.md` |
| 1. Identical round-trip (update) | | `data/dev/roundtrip-update/report.md` |
| 2. Components requiring manual work | | `inventory-checklist.md` |
| 3. Idempotent | | update report, pair "write 2 vs write 1" |
| 4. Fields containing secrets | | `scan_secrets.py` output (paths only) |

## Endpoint confirmation (step 0)

| Operation | 1.5.x endpoint | Response shape | Notes |
|---|---|---|---|
| Get site | | | |
| Create site | | | |
| Update site | | | |

## Site package vs API

- Preserved by site packages but not by the API:
- Preserved by the API but not by site packages:

## Built-in MCP (if tried)

- Available tools:
- Useful for the framework:

## New findings → review-findings

| New ID | Severity | Content |
|---|---|---|
| | | |

## Decision

**Go / Change direction / No-go** — rationale:

Follow-up updates: ADR-0001 (scope), ADR-0004 (list of data-impacting changes), ADR-0005 (fields containing secrets).
