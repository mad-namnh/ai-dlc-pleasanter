"""Profile records: guard inputs a person states outside the four gates (invariant I4, ADR-0020, ADR-0014 TB-1/TB-2).

The guard inputs `pls gate`, `pls jobs-verified` and the onboarding check read — profile rows Approvers, Operators,
Origin — and the `role` of an environment are set only through `pls profile set`, which records the person's words
under `gates/profile/` like a gate decision and then writes the file. Once a field has a record, the recorded value
is the one pls uses: a hand edit of the CLAUDE.md row changes nothing and lint L-PRF-01 reports it. A project made
before these records keeps its rows until the person records them (L-PRF-01 asks for it).

`dev-writes` (per environment, ADR-0024) is the person's standing permission for `apply` / `bootstrap` / `migrate` on
an environment whose role is dev; the record itself is the state (no file mirrors it), revoked by an `off` record.

The row Role tests (whether restricted roles are proven as each role at G3, or deferred to configuration checks) is
recorded the same way, but no pls command reads it — the skills do: its record gives tamper evidence (L-PRF-01 reports
an unrecorded, unknown or differing row), not enforcement.

Record files (`_load`, `_write`) are shared with the as-is review records (pls_as_is_review_records).
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path

FIELDS = ("Approvers", "Operators", "Origin", "Role tests")       # profile rows (CLAUDE.md)
ROLE_TESTS = ("deferred", "per-role keys")          # values of the row Role tests
CODE_VALUES = ("Origin", "Role tests")               # rows whose value is shown in backticks
ROLE = "role"                                       # envs.<env>.role (environments.json)
ROLES = ("dev", "stg", "prod")
DEV_WRITES = "dev-writes"                           # standing permission for writes to one dev environment (ADR-0024)
DEV_WRITES_VALUES = ("on", "off")
PER_ENV = (ROLE, DEV_WRITES)                        # fields recorded per environment
OWNER_FIELDS = ("Approvers", "Operators", ROLE)     # changed only by a G4 approver without an end date (_check_owner)
NO_OWNER_REPAIR = ("the team lead repairs it by hand once, keeping every earlier record (gate decisions are judged by "
                   "the profile of their time): add one file gates/profile/<date>-Approvers-repair.json with "
                   "{\"kind\": \"profile\", \"field\": \"Approvers\", \"value\": \"G1–G3: …; G4: <owner>\", "
                   "\"approver\": \"<owner>\", \"quote\": \"<their words>\", \"at\": \"<now, ISO with offset>\", "
                   "\"recorded_by\": \"hand repair\"} and commit it; the latest record is the one pls reads")
PROFILE_DIR = "gates/profile"


def _gt():
    import pls_gate          # imported late: pls_gate reads the effective profile from this module
    return pls_gate


def _row(field: str) -> re.Pattern:
    return re.compile(rf"^\|\s*{field}\s*\|(.*)\|\s*$", re.M)


def _norm(field: str, value: str) -> str:
    v = " ".join(value.split())
    return v.strip("`") if field in CODE_VALUES else v


def _placeholder(field: str, raw: str) -> bool:
    """Template text that names nobody / no origin yet (e.g. `G1, G4: <name>`, "`new` (…) / `existing` (…)")."""
    GT = _gt()
    if field == "Approvers":
        return not GT.approvers(f"| Approvers | {raw} |")
    if field == "Operators":
        return not GT.operators(f"| Operators | {raw} |")
    if field == "Role tests":                        # the template offers both values, joined by " / "
        return all(v in raw for v in ROLE_TESTS) and " / " in raw
    return _norm(field, raw) not in ("new", "existing")


def _profile_text(root: Path) -> str:
    p = root / "CLAUDE.md"
    try:
        return p.read_text(encoding="utf-8-sig") if p.exists() else ""
    except (OSError, UnicodeDecodeError) as ex:      # no profile read = no approver known: refuse, never guess
        raise _gt().GateError(f"CLAUDE.md (the project profile) cannot be read as UTF-8 text ({ex}) — save it as UTF-8")


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
        out.append(dict(g, _t=t, _path=rel))
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
    with out.open("x", encoding="utf-8", newline="\n") as f:        # never overwritten
        f.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    return out


# ---------------------------------------------------------------- profile fields and environment roles

def latest(root: Path, field: str, env: str | None = None, at: datetime | None = None) -> dict | None:
    """The record of `field` in force now, or at the instant `at` (the last one recorded at or before it)."""
    hits = [g for g in _load(root, PROFILE_DIR) if g.get("field") == field and (field not in PER_ENV or g.get("env") == env)
            and (at is None or g["_t"] <= at)]
    # two records at the same instant: the one that allows less wins (a withdrawn permission is never outranked)
    return max(hits, key=lambda g: (g["_t"], g.get("value") != "on")) if hits else None


def earliest(root: Path, field: str) -> dict | None:
    """The first record of a profile row (fields recorded per environment are not looked up here)."""
    hits = [g for g in _load(root, PROFILE_DIR) if g.get("field") == field and field not in PER_ENV]
    return min(hits, key=lambda g: g["_t"]) if hits else None


def effective_profile_text(root: Path, at: datetime | None = None) -> str:
    """CLAUDE.md as pls reads it: each guarded row carries its recorded value when the field has a record — the value
    in force now, or at the instant `at` (an approval is judged by the profile it was given under, ADR-0020). A field
    with no record at all keeps the row of the file; an instant before its first record reads that first record."""
    text = _profile_text(root)
    for field in FIELDS:
        rec = latest(root, field, at=at)
        if rec is None and at is not None:
            rec = earliest(root, field)          # before the first record: the first one, never the hand-editable row
        if rec is None:
            continue
        shown = f"`{rec['value']}`" if field in CODE_VALUES else rec["value"]
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
    if field == "Role tests" and value not in ROLE_TESTS:
        raise GT.GateError("Role tests is `deferred` or `per-role keys`")
    if field == DEV_WRITES:
        if value not in DEV_WRITES_VALUES:
            raise GT.GateError("dev-writes is `on` or `off`")
        envs = _envs(root)
        if not env or env not in envs:
            raise GT.GateError(f"--env must name an environment of environments.json ({', '.join(sorted(envs)) or 'none'})")
        roles = {(envs.get(env) or {}).get("role"), _role(root, env, envs)}     # the file and the role record
        if value == "on" and roles != {"dev"}:
            raise GT.GateError(f"dev-writes applies only to an environment whose role is dev in environments.json and "
                               f"in its role record ({env}: {sorted(map(str, roles))}) — stg and prod always ask the "
                               f"person (ADR-0024)")
        return
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
        raise GT.GateError(f"field is one of {', '.join(FIELDS + PER_ENV)}")
    if field in FIELDS and not _row(field).search(_profile_text(root)):
        raise GT.GateError(f"CLAUDE.md has no '{field}' row — copy it from templates/project/CLAUDE.md first")


def set_field(root: Path, field: str, value: str, approver: str, quote: str, env: str | None = None,
              recorded_by: str = "pls profile set") -> Path:
    """Record the person's decision, then write the value. The approver must be an approver of the effective
    profile; only the very first Approvers value may be stated by a person it names. Approvers, Operators and role
    need a G4 approver without an end date (_check_owner)."""
    GT = _gt()
    value = _norm(field, value)
    _check_value(root, field, value, env)
    if not quote.strip():
        raise GT.GateError("--quote: the person's own words for this decision are required (I4)")
    current = effective_profile_text(root)
    # the first value: no Approvers record yet and a row that grants nothing (the template placeholder). A row whose
    # grants have all ended, or a recorded value, is never "first" — otherwise anyone could state one and own the row
    first = latest(root, "Approvers") is None and not GT.grants(current)
    names = GT.approvers(current)
    pool = (GT.approvers(f"| Approvers | {value} |") if field == "Approvers" else {}) if first else names
    if not pool:
        raise GT.GateError("the profile names no approver: record Approvers first (pls profile set Approvers …)" if first
                           else "the profile names no approver today (every grant has ended or names nobody) — "
                           + NO_OWNER_REPAIR)
    who = next((n for n in pool if n.casefold() == approver.strip().casefold()), None)
    if who is None:
        raise GT.GateError(f"{approver!r} is not an approver ({', '.join(sorted(pool))})" +
                           (" — the first Approvers value must name the person who states it" if first else ""))
    if field in OWNER_FIELDS:
        _check_owner(GT, field, value, who, current, first=first)
    rec = {"kind": "profile", "field": field, "value": value, "approver": who, "quote": quote.strip(), "recorded_by": recorded_by}
    if field in PER_ENV:
        rec["env"] = env
    out = _write(root, PROFILE_DIR, f"{field.replace(' ', '-').lower() if ' ' in field else field}{'-' + env if env else ''}", rec)
    if field == DEV_WRITES:
        return out                                  # the record is the state: no file mirrors it
    if field == ROLE:
        p = root / "environments.json"
        doc = json.loads(p.read_text(encoding="utf-8-sig"))
        doc["envs"][env]["role"] = value
        p.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    else:
        p = root / "CLAUDE.md"
        shown = f"`{value}`" if field in CODE_VALUES else value
        p.write_text(_row(field).sub(lambda _m: f"| {field} | {shown} |", _profile_text(root), count=1), encoding="utf-8", newline="\n")
    return out


def _check_owner(GT, field: str, value: str, who: str, current: str, first: bool) -> None:
    """Approvers, Operators and an environment's role decide who may release outside dev: only a G4 approver without
    an end date (an owner) changes them, so a G1–G3 approver or a time-boxed G4 delegate cannot widen their own
    rights. A G4 grant in a new Approvers value has an end date unless its name is already an owner; the value keeps
    at least one owner (nobody could change the row again otherwise) and no end date already past.
    A profile with approvers but no owner refuses: nobody may decide, or a G1–G3 approver could make themselves the
    owner (L-PRF-01 reports it; NO_OWNER_REPAIR says how the person repairs it)."""
    owners = GT.owners(current)
    if not first and not owners:
        raise GT.GateError(f"the profile names no G4 approver without an end date, so nobody may change {field} — "
                           + NO_OWNER_REPAIR)
    if not first and who not in owners:
        raise GT.GateError(f"{field} is changed only by a G4 approver without an end date ({', '.join(sorted(owners))}); "
                           f"{who} is not one — ask them to state the change")
    if field != "Approvers":
        return
    row = f"| Approvers | {value} |"
    new_owners = GT.owners(row)
    if first and who not in new_owners:
        raise GT.GateError(f"the first Approvers value names the person who states it as a G4 approver without an end "
                           f"date (e.g. 'G1–G3: A, B; G4: {who}'); {who} is not one in {value!r}")
    if not new_owners:
        raise GT.GateError(f"Approvers {value!r} names no G4 approver without an end date: nobody could change the row "
                           "again — keep the owner (e.g. 'G4: Nam; G4 until 2026-12-05: Taro')")
    added = sorted(n for n in new_owners if n not in owners) if owners and not first else []
    if added:
        raise GT.GateError(f"a new G4 approver needs an end date: write 'G4 until <YYYY-MM-DD>: {', '.join(added)}' "
                           f"(a delegation ends by itself; only {', '.join(sorted(owners))} hold G4 without one)")
    today = date.today()
    past = sorted({f"{n} ({g} until {u.isoformat()})" for n, gs in GT.grants(row).items()
                   for g, u in gs.items() if u is not GT.PERMANENT and u < today})
    if past:
        raise GT.GateError(f"Approvers {value!r} has a grant whose last day is already past: {', '.join(past)}")


def _envs(root: Path) -> dict:
    p = root / "environments.json"
    try:
        return (json.loads(p.read_text(encoding="utf-8-sig")).get("envs") or {}) if p.exists() else {}
    except (OSError, UnicodeDecodeError, ValueError, AttributeError) as ex:
        raise _gt().GateError(f"environments.json is not readable ({ex})")


def _role(root: Path, env: str, envs: dict) -> str | None:
    """The role pls trusts: environments.json, overruled by the role record when they differ (L-PRF-01)."""
    rec = latest(root, ROLE, env)
    return rec["value"] if rec else ((envs.get(env) or {}).get("role"))


def dev_writes(root: Path, env: str) -> dict | None:
    """The standing permission for writes to `env` (ADR-0024): its latest record when it is `on` and the environment
    is dev in environments.json and in its role record. None means: ask the person. Anything that cannot be read is
    None too (fail closed: the typed confirmation is asked)."""
    GT = _gt()
    try:
        rec = latest(root, DEV_WRITES, env)
        envs = _envs(root)
        names = GT.approvers(effective_profile_text(root))
    except GT.GateError:
        return None
    if not rec or rec.get("value") != "on" or (envs.get(env) or {}).get("role") != "dev" or _role(root, env, envs) != "dev":
        return None
    # stated by a person who is an approver now: a record by a former approver does not count. A hand-written record
    # that names a current approver is not told apart from one written by pls (same trust as gate records, TB-3).
    if not any(n.casefold() == str(rec.get("approver", "")).casefold() for n in names):
        return None
    return rec


def lint(root: Path) -> list[dict]:
    """L-PRF-01: a guarded profile row or environment role that differs from its record, or has none."""
    GT = _gt()
    try:
        _load(root, PROFILE_DIR)
    except GT.GateError as ex:
        return [{"rule": "L-PRF-01", "site": "-", "msg": str(ex)}]
    issues, text = [], _profile_text(root)
    how = "after the person confirms it: pls profile set {f} \"{v}\" {env}--approver <name> --quote \"<their words>\""
    quoted = lambda f: f'"{f}"' if " " in f else f          # noqa: E731 — a field with a space is one argument
    for field in FIELDS:
        m = _row(field).search(text)
        if not m:
            continue
        row, rec = _norm(field, m.group(1).strip()), latest(root, field)
        if rec and row != rec["value"]:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"CLAUDE.md {field} {row!r} differs from its record "
                           f"{rec['value']!r} (edited by hand?) — pls uses the recorded value; " + how.format(f=quoted(field), v=row, env="")})
        elif not rec and field == "Role tests" and not _placeholder(field, m.group(1).strip()) and row not in ROLE_TESTS:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"CLAUDE.md Role tests {row!r} is not a value pls knows "
                           f"(`deferred` or `per-role keys`) and has no record — " + how.format(f=quoted(field), v="<value>", env="")})
        elif not rec and not _placeholder(field, m.group(1).strip()):
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"CLAUDE.md {field} has no record — " + how.format(f=quoted(field), v=row, env="")})
    current = effective_profile_text(root)
    if GT.grants(current) and not GT.owners(current):
        issues.append({"rule": "L-PRF-01", "site": "-", "msg": "Approvers names no G4 approver without an end date: "
                       "Approvers, Operators and environment roles cannot be changed — " + NO_OWNER_REPAIR})
    p = root / "environments.json"
    envs = (json.loads(p.read_text(encoding="utf-8-sig")).get("envs") or {}) if p.exists() else {}
    names = {n.casefold() for n in GT.approvers(current)}
    for env in sorted({g.get("env") for g in _load(root, PROFILE_DIR) if g.get("field") == DEV_WRITES}):
        rec = latest(root, DEV_WRITES, env)
        if rec and rec.get("value") == "on" and str(rec.get("approver", "")).casefold() not in names:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"{rec['_path']}: dev-writes on for {env} stated by "
                           f"{rec.get('approver')!r}, who is not an approver of the profile — pls ignores it and asks the "
                           f"person; record it again with an approver's words, or withdraw it (dev-writes off)"})
    for env, ec in envs.items():
        role, rec = (ec or {}).get("role"), latest(root, ROLE, env)
        if rec and role != rec["value"]:
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"envs.{env}.role {role!r} differs from its record "
                           f"{rec['value']!r} (edited by hand?) — " + how.format(f=ROLE, v=role, env=f"--env {env} ")})
        elif not rec and role and role != "dev":   # dev entries are made by setup / init / sandbox create
            issues.append({"rule": "L-PRF-01", "site": "-", "msg": f"envs.{env}.role has no record — " +
                           how.format(f=ROLE, v=role, env=f"--env {env} ")})
    return issues
