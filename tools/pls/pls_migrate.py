"""Data migrations of a release over the guarded HTTP transport (ADR-0004, ADR-0008, ADR-0014 TB-7).

A data-impacting release carries migration folders (`release-plan --migration DIR`): `migration.json`, `backup/`,
`dry-run.md`. `pls migrate <release>` sends each folder's explicit `data` with one `bulkupsert` (D13) — after the
write guard, G4 on non-dev environments (the G4 digest covers the migration folders) and the mail / job checks —
and records every run in `plan.json` under `migrations_run` before the call is sent. ADR-0004 order is enforced:
`apply` refuses a release whose migrations have not all run. `--rollback` sends the folder's `rollback.data`, which
a person prepares from `backup/` and dry-runs on a copy; pls never builds a rollback from the backup itself (how a
record read back by `get` behaves when sent to `bulkupsert` is not verified on 1.5.x).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

RUN_KEY = "migrations_run"
UNKNOWN = ("migrating", "uncertain")


class MigrateError(Exception):
    pass


def dirs(plan: dict) -> list[str]:
    m = plan.get("migration")
    return [m] if isinstance(m, str) else [x for x in m if isinstance(x, str)] if isinstance(m, list) else []


def folder(r: Path, mig: str) -> Path:
    return Path(mig) if Path(mig).is_absolute() else r / mig


def load(r: Path, mig: str, rollback: bool) -> dict:
    """{dir, site, keys, data} of one migration folder; refuses anything pls would have to guess."""
    try:
        m = json.loads((folder(r, mig) / "migration.json").read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, ValueError) as ex:
        raise MigrateError(f"{mig}/migration.json is not readable JSON ({ex})")
    if not isinstance(m, dict) or not isinstance(m.get("site"), str):
        raise MigrateError(f"{mig}/migration.json: 'site' (logical site name) is missing")
    keys = m.get("keys")
    if not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys):
        raise MigrateError(f"{mig}/migration.json: 'keys' must list the business identifier columns (D13)")
    if rollback:
        rb = m.get("rollback")
        data = rb.get("data") if isinstance(rb, dict) else None
        if not isinstance(data, list):
            raise MigrateError(f"{mig}/migration.json: 'rollback' is not explicit data ({{\"data\": [...]}}) — a person "
                               "prepares it from backup/ and dry-runs it on a copy; pls does not build it from the backup")
    else:
        data = m.get("data")
        if not isinstance(data, list):
            raise MigrateError(f"{mig}/migration.json has no explicit 'data' — write the result of the mapping (as checked "
                               "in dry-run.md) as data")
    if not data or not all(isinstance(x, dict) for x in data):
        raise MigrateError(f"{mig}: the data to send is empty or not a list of records")
    seen = set()
    for x in data:
        key = tuple(x.get(k) for k in keys)
        if any(v in (None, "") for v in key):
            raise MigrateError(f"{mig}: a record has no value for the keys {keys} — bulkupsert would create a new record")
        if key in seen:
            raise MigrateError(f"{mig}: key {dict(zip(keys, key))} appears twice — non-unique keys stop bulkupsert (D18)")
        seen.add(key)
    return {"dir": mig, "site": m["site"], "keys": keys, "data": data}


def target(e: dict, env: str, site: str) -> int:
    """Site id the migration may write: a site of this environment, never a shared one (ADR-0011)."""
    conf = e["sites"].get(site) or {}
    if not isinstance(conf.get("id"), int) or conf.get("shared_from") or (e.get("sandbox_of") and not conf.get("sandbox")):
        raise MigrateError(f"{site} is not a site this migration may write in {env} (no id, or a shared site)")
    return conf["id"]


def last(plan: dict, mig: str, direction: str) -> dict | None:
    runs = [x for x in plan.get(RUN_KEY) or [] if isinstance(x, dict) and x.get("dir") == mig and x.get("direction") == direction]
    return runs[-1] if runs else None


def state_problem(plan: dict, mig: str, rollback: bool) -> str | None:
    """Why this folder may not run now; None when it may."""
    fwd = last(plan, mig, "forward")
    if rollback:
        back = last(plan, mig, "rollback")
        if not fwd:
            return f"{mig} was never migrated — nothing to roll back"
        if back and back["status"] in UNKNOWN + ("migrated",):
            return f"{mig}: rollback already {back['status']} — a person checks the records against backup/"
        return None
    if plan.get("status") != "planned":
        return f"the release has status {plan.get('status')!r}: migrations run before apply (ADR-0004 order)"
    if fwd and fwd["status"] == "migrated":
        return f"{mig} was already migrated at {fwd.get('finished_at')} — never sent twice"
    if fwd and fwd["status"] in UNKNOWN:
        return (f"{mig}: the last run ended {fwd['status']!r} — the records may have changed. A person compares them with "
                f"backup/; then roll back (pls migrate --rollback) or record the outcome before any re-run")
    return None


def pending(plan: dict) -> list[str]:
    """Migration folders of the release whose forward run has not ended "migrated" (apply refuses on these)."""
    return [m for m in dirs(plan) if (last(plan, m, "forward") or {}).get("status") != "migrated"]


def start(plan: dict, mig: str, direction: str, site: str, count: int) -> dict:
    entry = {"dir": mig, "direction": direction, "site": site, "records": count, "status": "migrating",
             "started_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    plan.setdefault(RUN_KEY, []).append(entry)
    return entry


def finish(entry: dict, res: dict) -> None:
    entry.update(status=res["status"], message=res["message"],
                 finished_at=datetime.now().astimezone().isoformat(timespec="seconds"))
