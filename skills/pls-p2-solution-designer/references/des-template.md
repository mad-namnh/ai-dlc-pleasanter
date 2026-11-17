---
id: DES-NNN
status: awaiting G2
reqs: [REQ-…]
classification: config-only
elements:
  - id: E1
    site: <logical site>
    setting: <what is set>
    req: REQ-…
    rung: 1
impact:
  - rule: <rule id of impact-rules.md>
    element: <existing element>
    action: <what the design does, or checked: none>
---
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

| Rule (`impact-rules.md`) | Existing element | Impact | Action |
|---|---|---|---|
| … | … | … | … |

## Migration (only if data-impacting)

Script, dry run on a copy, rollback.

## Open points

- …

## Front matter (read by `pls check p2`)

- `reqs`: the requirements this design meets (every G1-approved REQ must be in some DES).
- `elements`: one item per design-table row — `id`, `site`, `setting`, `req` (a REQ of `reqs`, or `impact` for an element an impact row needs), `rung` 1–5 and, from rung 3, `reason`.
- `classification`: `config-only` | `data-impacting` (then a `## Migration` section) | `permission-impacting`.
- `impact`: one item per impact-table row — `rule` (an id of `impact-rules.md`), `element`, `action`.
- The format is a small subset of YAML (`key: value`, `key: [a, b]`, block lists of `- k: v` items); `pls check p2` names any line it cannot read.
