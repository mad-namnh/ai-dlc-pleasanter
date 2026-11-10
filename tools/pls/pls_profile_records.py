"""Profile records: guard inputs a person states outside the four gates (invariant I4, ADR-0014 TB-1/TB-2).

The guard inputs `pls gate`, `pls jobs-verified` and the onboarding check read — profile rows Approvers, Operators,
Origin — and the `role` of an environment are set only through `pls profile set`, which records the person's words
under `gates/profile/` like a gate decision and then writes the file. Once a field has a record, the recorded value
is the one pls uses: a hand edit of the CLAUDE.md row changes nothing and lint L-PRF-01 reports it. A project made
before these records keeps its rows until the person records them (L-PRF-01 asks for it).

Record files (`_load`, `_write`) are shared with the as-is review records (pls_as_is_review_records).
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

FIELDS = ("Approvers", "Operators", "Origin")       # profile rows (CLAUDE.md)
ROLE = "role"                                       # envs.<env>.role (environments.json)
ROLES = ("dev", "stg", "prod")
PROFILE_DIR = "gates/profile"


def _gt():
    import pls_gate          # imported late: pls_gate reads the effective profile from this module
    return pls_gate


def _row(field: str) -> re.Pattern:
    return re.compile(rf"^\|\s*{field}\s*\|(.*)\|\s*$", re.M)


def _norm(field: str, value: str) -> str:
    v = " ".join(value.split())
    return v.strip("`") if field == "Origin" else v


def _placeholder(field: str, raw: str) -> bool:
    """Template text that names nobody / no origin yet (e.g. `G1, G4: <name>`, "`new` (…) / `existing` (…)")."""
    GT = _gt()
    if field == "Approvers":
        return not GT.approvers(f"| Approvers | {raw} |")
    if field == "Operators":
        return not GT.operators(f"| Operators | {raw} |")
    return _norm(field, raw) not in ("new", "existing")


def _profile_text(root: Path) -> str:
    p = root / "CLAUDE.md"
    return p.read_text(encoding="utf-8-sig") if p.exists() else ""


def _load(root: Path, sub: str, key: str = "value") -> list[dict]:
    """Records of one kind, each with its instant in "_t"; a damaged record refuses (fail closed, as gate records)."""
    GT = _gt()
    d = root / sub
    if not d.exists():
        return []
    now, out = datetime.now().astimezone(), []
    for p in sorted(d.glob("*.json")):
        rel = p.relative_to(root).as_posix()
        try:
            g = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            raise GT.GateError(f"{rel} is not a readable JSON record ({ex}) — a person repairs or removes it")
        t = GT._instant(g.get("at")) if isinstance(g, dict) else None
        ok = isinstance(g, dict) and t is not None and t <= now + GT.FUTURE_TOLERANCE and \
            all(isinstance(g.get(k), str) and g[k].strip() for k in ("approver", "quote", key))
        if not ok:
            raise GT.GateError(f"{rel}: not a valid record (approver, quote, at, {key}) — a person repairs or removes it")
        out.append(dict(g, _t=t))
    return out


def _write(root: Path, sub: str, stem: str, rec: dict, key: str = "value") -> Path:
    d = root / sub
    d.mkdir(parents=True, exist_ok=True)
    now = datetime.now().astimezone()
    prev = [g["_t"] for g in _load(root, sub, key)]
    if prev and now <= max(prev):                     # a new record is always later than every earlier one
        now = max(prev) + timedelta(microseconds=1)
    rec = dict(rec, at=now.isoformat(timespec="microseconds"), date=now.date().isoformat())
    out = d / f"{rec['date']}-{stem}-{now.strftime('%H%M%S')}-{secrets.token_hex(3)}.json"
    with out.open("x", encoding="utf-8") as f:        # never overwritten
        f.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    return out


# ---------------------------------------------------------------- profile fields and environment roles

def latest(root: Path, field: str, env: str | None = None) -> dict | None:
    hits = [g for g in _load(root, PROFILE_DIR) if g.get("field") == field and (field != ROLE or g.get("env") == env)]
    return max(hits, key=lambda g: g["_t"]) if hits else None


def effective_profile_text(root: Path) -> str:
    """CLAUDE.md as pls reads it: each guarded row carries its recorded value when the field has a record."""
    text = _profile_text(root)
    for field in FIELDS:
        rec = latest(root, field)
        if rec is None:
            continue
        shown = f"`{rec['value']}`" if field == "Origin" else rec["value"]
        line = f"| {field} | {shown} |"
        text, n = _row(field).subn(lambda _m: line, text, count=1)
        if not n:
            text += f"\n{line}\n"
    return text


def _check_value(root: Path, field: str, value: str, env: str | None) -> None:
    GT = _gt()
    if field == "Approvers" and not GT.approvers(f"| Approvers | {value} |"):
        raise GT.GateError(f"Approvers {value!r} names no approver for any gate (e.g. 'Nam (all gates)' or 'G1, G4: Nam; G2, G3: Taro')")
    if field == "Operators" and not GT.operators(f"| Operators | {value} |"):
        raise GT.GateError(f"Operators {value!r} names nobody (e.g. 'dev: Nam; stg: Nam; prod: <customer operator>')")
    if field == "Origin" and value not in ("new", "existing"):
        raise GT.GateError("Origin is `new` or `existing`")
    if field == ROLE:
        if value not in ROLES:
            raise GT.GateError(f"role is one of {', '.join(ROLES)}")
        p = root / "environments.json"
        try:
            envs = (json.loads(p.read_text(encoding="utf-8-sig")).get("envs") or {}) if p.exists() else {}
        except (OSError, UnicodeDecodeError, ValueError, AttributeError) as ex:
            raise GT.GateError(f"environments.json is not readable ({ex})")
        if not env or env not in envs:
            raise GT.GateError(f"--env must name an environment of environments.json ({', '.join(sorted(envs)) or 'none'})")
    elif field not in FIELDS:
        raise GT.GateError(f"field is one of {', '.join(FIELDS + (ROLE,))}")
    if field in FIELDS and not _row(field).search(_profile_text(root)):
        raise GT.GateError(f"CLAUDE.md has no '{field}' row — copy it from templates/project/CLAUDE.md first")


def set_field(root: Path, field: str, value: str, approver: str, quote: str, env: str | None = None,
              recorded_by: str = "pls profile set") -> Path:
    """Record the person's decision, then write the value. The approver must be an approver of the effective
    profile; only the very first Approvers value may be stated by a person it names."""
    GT = _gt()
    value = _norm(field, value)
    _check_value(root, field, value, env)
    if not quote.strip():
        raise GT.GateError("--quote: the person's own words for this decision are required (I4)")
    names = GT.approvers(effective_profile_text(root))
    pool = names or (GT.approvers(f"| Approvers | {value} |") if field == "Approvers" else {})
    if not pool:
        raise GT.GateError("the profile names no approver: record Approvers first (pls profile set Approvers …)")
    who = next((n for n in pool if n.casefold() == approver.strip().casefold()), None)
    if who is None:
        raise GT.GateError(f"{approver!r} is not an approver ({', '.join(sorted(pool))})" +
                           ("" if names else " — the first Approvers value must name the person who states it"))
    rec = {"kind": "profile", "field": field, "value": value, "approver": who, "quote": quote.strip(), "recorded_by": recorded_by}
    if field == ROLE:
        rec["env"] = env
    out = _write(root, PROFILE_DIR, f"{field}{'-' + env if env else ''}", rec)
    if field == ROLE:
        p = root / "environments.json"
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
        doc["envs"][env]["role"] = value
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        p = root / "CLAUDE.md"
        shown = f"`{value}`" if field == "Origin" else value
        p.write_text(_row(field).sub(lambda _m: f"| {field} | {shown} |", _profile_text(root), count=1), encoding="utf-8")
    return out


def lint(root: Path) -> list[dict]:
    """L-PRF-01: a guarded profile row or environment role that differs from its record, or has none."""
    GT = _gt()
    try:
        _load(root, PROFILE_DIR)
    except GT.GateError as ex:
        return [{"rule": "L-PRF-01", "site": "-", "msg": str(ex)}]
    issues, text = [], _profile_text(root)
    how = "after the person confirms it: pls profile set {f} \"{v}\" {env}--approver <name> --quote \"<their words>\""
    for field in FIELDS:
        m = _row(field).search(text)
        if not m:
            continue
        row, rec = _norm(field, m.group(1).strip()), latest(root, field)
        if rec and row != rec["value"]:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"CLAUDE.md {field} {row!r} differs from its record "
                           f"{rec['value']!r} (edited by hand?) — pls uses the recorded value; " + how.format(f=field, v=row, env="")})
        elif not rec and not _placeholder(field, m.group(1).strip()):
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"CLAUDE.md {field} has no record — " + how.format(f=field, v=row, env="")})
    p = root / "environments.json"
    envs = (json.loads(p.read_text(encoding="utf-8-sig")).get("envs") or {}) if p.exists() else {}
    for env, ec in envs.items():
        role, rec = (ec or {}).get("role"), latest(root, ROLE, env)
        if rec and role != rec["value"]:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"envs.{env}.role {role!r} differs from its record "
                           f"{rec['value']!r} (edited by hand?) — " + how.format(f=ROLE, v=role, env=f"--env {env} ")})
        elif not rec and role and role != "dev":   # dev entries are made by setup / init / sandbox create
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"envs.{env}.role has no record — " +
                           how.format(f=ROLE, v=role, env=f"--env {env} ")})
    return issues
