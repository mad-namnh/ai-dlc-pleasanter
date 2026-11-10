# DES-NNN — <title>

- **Status:** awaiting G2
- **Requirements:** REQ-…
- **Change classification (ADR-0004):** config-only | data-impacting | permission-impacting — <reason>

## Ladder (I5)

Rung: <1–5>. <Reason if ≥ 3.>

## Design

| Element | Setting | REQ | Rung |
|---|---|---|---|
| … | … | … | … |

A server script gets its own row that names the site and the script exactly as in `server-scripts/_index.json`, e.g. `| L10 | loans server script `validate-dates` | BeforeCreate: … | 002 | **3** |`, followed by the rung 3 reason. Lint L-LAD-01 looks for both names in a `design/decisions/DES-*.md`; a script named only elsewhere stays undecided.

## Rejected alternatives

- <alternative> — <why (cite pls-kb-pleasanter entry if applicable)>

## Impact analysis

| Existing element | Impact | Action |
|---|---|---|
| … | … | … |

## Migration (only if data-impacting)

Script, dry run on a copy, rollback.

## Open points

- …
