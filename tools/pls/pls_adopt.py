"""Adopting an existing site into a project (plan BR4, ADR-0001/0002). Pure helpers; pls.py does the I/O.

`pls adopt --env <e> --site <id> --name <logical>` is READ-ONLY towards Pleasanter: one getsite. Locally it
- registers the site in environments.json (id, title, managed_sites);
- unpacks the export into config/<name> (the normal unpack);
- records every used column slot in the slot ledger with zone "customer" (ADR-0002, option C for existing sites);
- writes an adoption record releases/A-…/ (status "applied", payload = the export) so `pls drift` measures the
  environment against the adopted state from day one;
- writes a report ops/adopt/<date>-<env>-<name>.md: components without round-trip evidence, sites referenced but
  not managed (their ids stay raw), principals not mapped, server scripts without a design decision.
"""
from __future__ import annotations

import re
from typing import Any

import pls_scripts as SX

REF_IN_TEXT = re.compile(r"\[\[(\d+)")          # ChoicesText "[[123]]" and "[[123,…]]"


def slot_entries(slots: dict[str, str], today: str, filter_only: set[str] | None = None) -> dict[str, dict]:
    """Ledger entries for the slots a live site uses (column → label). Slots that appear only in FilterColumns are
    kept (the collision check treats every slot on the live site as taken) but marked, so reports can tell them apart:
    a site may list hundreds of filterable slots it never defined."""
    filter_only = filter_only or set()
    return {col: {"label": label, "status": "allocated", "zone": "customer", "req": "adopted", "adopted": today}
            | ({"placement": "filter-only"} if col in filter_only else {})
            for col, label in sorted(slots.items())}


def referenced_sites(settings: Any) -> set[int]:
    """Site ids a configuration points to: integer values of *SiteId keys, and [[id]] in choice texts."""
    out: set[int] = set()

    def walk(o: Any, key: str = "") -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, bool):
            return
        elif isinstance(o, int) and key.endswith("SiteId") and o > 0:
            out.add(o)
        elif isinstance(o, str):
            out.update(int(m) for m in REF_IN_TEXT.findall(o))
    walk(settings)
    return out


def raw_principals(permissions: dict | None) -> list[str]:
    return [x for x in (permissions or {}).get("entries") or [] if not str(x).startswith("${principal:")]


def report(name: str, env: str, site_id: int, title: str, rt: str, counts: dict, scope: list[str], unmanaged: list[int],
           principals: list[str], undecided_scripts: list[str], record: str, today: str, extra: dict | None = None) -> str:
    def lines(items, empty="none"):
        return "\n".join(f"- {x}" for x in items) if items else f"- {empty}"
    return f"""# Adoption report — {name} ({env}, site {site_id})

- **Date:** {today}
- **Site:** {title} ({rt}), id {site_id} — read only (one getsite); nothing was written to Pleasanter
- **Adoption record (drift baseline):** `{record}`
- **Size:** {', '.join(f'{k} {v}' for k, v in counts.items() if v) or 'empty'}

## Components without round-trip evidence (ADR-0001)

`pls release-plan` refuses this site until each is probed on a copy in dev, or a person accepts it with `--accept-unverified <decision record>`.

{lines(scope)}

## Sites referenced but not managed

Their ids stay raw in `config/` and would not be remapped in another environment. Adopt them too, or map them in `environments.json`. Ids of unmanaged sites written inside scripts cannot be found automatically (BR7).

{lines([str(x) for x in unmanaged])}

## Principals not mapped (L-PERM-01)

Create a role per group in `design/roles.json` and run `pls principals`, or map them in `environments.json` `principals`.

{lines(principals)}

## Server scripts without a design decision (L-LAD-01)

Existing code: record its purpose in a design decision before it is changed (I5).

{lines(undecided_scripts)}

{"".join(f"## {title}\n\n{lines(items)}\n\n" for title, items in (extra or {}).items())}## Next

1. Review this report with the team; decide per finding (probe, accept, adopt related sites, map principals).
2. `pls lint` lists the same points as rule ids.
3. Before any change: `pls drift --env {env} --site {name} <fresh export>` must show 0 differences against the adoption record.
"""


SAFE_NAME = re.compile(r"[a-z0-9][a-z0-9_\-]*")


def script_id_uses(raw_scripts: dict, ids: dict[str, str]) -> list[str]:
    """Every place where a number equal to a managed site id appears inside a script body. Written as a site id
    (an id context) it becomes ${site:x} in git (D3); anywhere else it stays as it is and is listed as POSSIBLE, for
    a person to mark it as a reference if it really is one (`pls refs --ref`)."""
    out = []
    for kind, items in raw_scripts.items():
        for it in items or []:
            body = it.get("Body") or ""
            label = it.get("Name") or it.get("Title") or f"Id {it.get('Id')}"
            for sid, name in ids.items():
                for m in re.finditer(SX.id_pattern(sid), body):   # the same rule as the replacement itself
                    line = body.count("\n", 0, m.start()) + 1
                    ctx = body[max(0, m.start() - 25):m.end() + 25].replace("\r", "").replace("\n", "⏎")
                    if SX.in_id_context(body, m.start(), m.end()):
                        out.append(f"{kind} '{label}' line {line}: {sid} → ${{site:{name}}} … `{ctx}`")
                    else:
                        out.append(f"POSSIBLE — kept as written; {kind} '{label}' line {line}: {sid} (= {name}?) … `{ctx}`")
    return out
