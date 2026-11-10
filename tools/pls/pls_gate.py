"""Gate decisions as records (invariant I4): who approved what, in their own words, checked against the profile.

The agent never approves a gate. After the person states a decision, `pls gate` writes one file per decision
under `gates/`, named by date, gate, time and a random suffix, so records of parallel branches never share a
name and a record is never overwritten. The record is what other
commands trust:
- `release-plan` for a stg target needs a G3 approval of that release;
- `apply` / `bootstrap` on stg need a G4 approval naming that release or bootstrap id, bound to its content
  (pls_release_digest): a release changed after G4 is refused;
- lint L-GATE-01: every "G<n> approved" status line in a REQ, DES, G3 or approvals file has its record.
Only names listed as approvers in the project profile (`CLAUDE.md`, row "Approvers") are accepted; once the row has a
`pls profile set` record, the recorded value is the one read (pls_profile_records).
The last decision counts: ordered by the instant in `at` (a rejection wins a tie); a record dated in the future or
of the wrong shape refuses every gate check until a person repairs or removes it.
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

import pls_profile_records as PR
import pls_release_digest as RD

GATES = ("G1", "G2", "G3", "G4")
DECISIONS = ("approved", "rejected", "changes-requested")
_ROW = re.compile(r"^\|\s*Approvers\s*\|(.*)\|\s*$", re.M)
_STATUS = re.compile(r"^.*\bStatus\b.*?\b(G[1-4])\b.*?\bapproved\b(.*)$", re.M | re.I)
_WHO = re.compile(r"^\s*(?:\(\s*|by\s+)([^,()\d]+?)\s*(?:[,)]|\bon\b|$)", re.I)
_ID = re.compile(r"^(REQ|DES)-\d+")
_G4_ROW = re.compile(r"^\|\s*G4\s*\|\s*approved", re.M)


class GateError(Exception):
    pass


def approvers(profile_text: str) -> dict[str, set[str]]:
    """Approver name → gates they may approve, from the profile row "Approvers".

    Accepted forms (segments separated by ';'): `Nam (all gates)`, `Nam`, `Nam (G1, G2), Taro (G3, G4)`,
    `G1, G4: Nam; G2, G3: Taro`. Placeholders (`<…>`, empty, "tbd") name no approver.
    """
    m = _ROW.search(profile_text)
    if not m:
        return {}
    out: dict[str, set[str]] = {}

    def add(name: str, gates: set[str]):
        name = name.strip()
        if name and gates and "<" not in name and name.lower() not in ("tbd", "-", "none"):
            out.setdefault(name, set()).update(gates)

    for seg in m.group(1).split(";"):
        seg = seg.strip()
        if re.match(r"^(G[1-4][\s,]*)+:", seg):                       # "G1, G4: Nam, Taro"
            head, names = seg.split(":", 1)
            for n in re.split(r",|/|\band\b", names):
                add(n, _gates(head))
            continue
        for part in re.split(r",(?![^()]*\))", seg):                   # "Nam (G1, G2), Taro (all gates)"
            nm = re.match(r"\s*([^()]+?)\s*(?:\(([^)]*)\))?\s*$", part)
            if nm:
                g = nm.group(2)
                add(nm.group(1), set(GATES) if g is None else _gates(g))
    return out


def _gates(text: str) -> set[str]:
    """Gates named in `text`: "all gates", "G1, G2", "G1-G4" / "G1–G4". Anything else (a note such as "PM",
    or "all except G4") names no gate, so the person is asked instead of every gate being granted."""
    t = text.lower()
    if "except" in t or "not" in t.split():
        return set()
    if re.fullmatch(r"\s*all(\s+gates)?\s*", t):
        return set(GATES)
    out = set()
    for a, b in re.findall(r"G([1-4])\s*[-–~]\s*G([1-4])", text):
        out |= {f"G{i}" for i in range(int(a), int(b) + 1)}
    return out | set(re.findall(r"G[1-4]", text))


def _approver_for(root: Path, name: str, gate: str) -> str:
    names = approvers(PR.effective_profile_text(root))
    if not names:
        raise GateError("the project profile names no approver: ask the person who approves this gate and add the name "
                        "to the Approvers row of CLAUDE.md after they say it")
    match = next((n for n in names if n.casefold() == name.strip().casefold()), None)
    if not match:
        raise GateError(f"{name!r} is not an approver in the project profile (approvers: {', '.join(sorted(names))})")
    if gate not in names[match]:
        raise GateError(f"{match} approves {', '.join(sorted(names[match]))} in the project profile, not {gate}")
    return match


# ---------------------------------------------------------------- operators (manual deploy steps, ADR-0012)

_OPS_ROW = re.compile(r"^\|\s*Operators\s*\|(.*)\|\s*$", re.M)


def operators(profile_text: str) -> dict[str, set[str]] | None:
    """Environment → names of the people who run its manual deploy steps, from the profile row "Operators"
    (`dev: Nam; stg: Nam, Taro; prod: <customer operator>`). None when the profile has no such row (older projects);
    placeholders (`<…>`, empty, "tbd") name nobody."""
    m = _OPS_ROW.search(profile_text)
    if not m:
        return None
    out: dict[str, set[str]] = {}
    for seg in m.group(1).split(";"):
        if ":" not in seg:
            continue
        env, names = seg.split(":", 1)
        for n in re.split(r",|/|\band\b", re.sub(r"\([^)]*\)", "", names)):     # "(note)" is not a name
            n = n.strip()
            if n and "<" not in n and n.lower() not in ("tbd", "-", "none"):
                out.setdefault(env.strip().strip("`"), set()).add(n)
    return out


def job_verifier(root: Path, name: str, env: str, approved_by: str | None = None) -> dict:
    """Who may confirm the manual deploy of scheduled scripts on `env`: an operator of that environment (profile row
    Operators) or a G4 approver. Without an Operators row only G4 approvers (older projects). `approved_by`, when
    given, must be a G4 approver. Returns the record fields; raises GateError for a name the profile does not hold."""
    ops = operators(PR.effective_profile_text(root))
    op = next((n for n in (ops or {}).get(env, set()) if n.casefold() == name.strip().casefold()), None)
    if op:
        rec = {"by": op, "role": "operator", "env": env}
    else:
        try:
            rec = {"by": _approver_for(root, name, "G4"), "role": "g4-approver", "env": env}
        except GateError as ex:
            if ops is None:
                raise
            listed = ", ".join(sorted((ops or {}).get(env, set()))) or "nobody"
            raise GateError(f"{name!r} is neither an operator of {env} (Operators row: {listed}) nor a G4 approver ({ex})")
    if approved_by:
        rec["approved_by"] = _approver_for(root, approved_by, "G4")
    return rec


# A record may come from another machine whose clock runs a little ahead; anything later than this is not a real
# decision yet and would outrank every decision recorded after it.
FUTURE_TOLERANCE = timedelta(minutes=5)


def _instant(value) -> datetime | None:
    """`at` of a record as an aware datetime (an instant), or None when it is not an ISO time with a UTC offset."""
    if not isinstance(value, str):
        return None
    try:
        t = datetime.fromisoformat(value)
    except ValueError:
        return None
    return t if t.tzinfo is not None and t.utcoffset() is not None else None


def _record_problem(g, now: datetime) -> str | None:
    """Why a gate record cannot be trusted as written; None when its fields have the shapes the guards read."""
    if not isinstance(g, dict):
        return "is not a JSON object"
    if g.get("gate") not in GATES:
        return f"gate {g.get('gate')!r} is not one of {', '.join(GATES)}"
    if g.get("decision") not in DECISIONS:
        return f"decision {g.get('decision')!r} is not one of {', '.join(DECISIONS)}"
    if not isinstance(g.get("approver"), str) or not g["approver"].strip():
        return "approver is not a name"
    for k in ("items", "releases"):        # a string would match ids by substring ("R-30" contains "R-3")
        v = g.get(k, [])
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            return f"{k} is not a list of ids"
    t = _instant(g.get("at"))
    if t is None:
        return f"at {g.get('at')!r} is not an ISO time with a UTC offset"
    if t > now + FUTURE_TOLERANCE:
        return f"at {g['at']} is in the future"
    return None


def load(root: Path) -> list[dict]:
    """Every record under gates/, each with its instant in "_t". A record that cannot be read or has the wrong shape
    raises GateError naming the file: a guard never decides from a record it cannot interpret (fail closed)."""
    d = root / "gates"
    if not d.exists():
        return []
    now, out = datetime.now().astimezone(), []
    for p in sorted(d.glob("*.json")):
        rel = p.relative_to(root).as_posix()
        try:
            g = json.loads(p.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, ValueError) as ex:
            raise GateError(f"{rel} is not a readable JSON record ({ex}) — a person repairs or removes it; "
                            f"gate checks refuse until then")
        why = _record_problem(g, now)
        if why:
            raise GateError(f"{rel}: {why} — a person repairs or removes the record; gate checks refuse until then")
        out.append(dict(g, _t=_instant(g["at"])))
    return out


def record(root: Path, gate: str, decision: str, approver: str, quote: str, items: list[str], releases: list[str],
           today: str) -> Path:
    gate = gate.upper()
    if gate not in GATES:
        raise GateError(f"gate must be one of {', '.join(GATES)}")
    if decision not in DECISIONS:
        raise GateError(f"decision must be one of {', '.join(DECISIONS)}")
    if not quote.strip():
        raise GateError("--quote: the person's own words for this decision are required (I4)")
    if gate in ("G1", "G2") and not items:
        raise GateError(f"{gate} needs --item for every {'REQ' if gate == 'G1' else 'DES'} id it decides")
    if gate in ("G3", "G4") and not releases:
        raise GateError(f"{gate} needs --release (G4 also names a bootstrap id when the release creates sites)")
    who = _approver_for(root, approver, gate)
    d = root / "gates"
    d.mkdir(exist_ok=True)
    now = datetime.now().astimezone()
    # the clock can repeat a value (coarse on Windows): a new record is always later than every record already there,
    # so "the last decision wins" never depends on the random file suffix
    prev = [g["_t"] for g in load(root)]
    if prev and now <= max(prev):
        now = max(prev) + timedelta(microseconds=1)
    at = now.isoformat(timespec="microseconds")
    rec = {"gate": gate, "decision": decision, "approver": who, "date": today, "at": at,
           "quote": quote.strip(), "items": items, "releases": releases, "recorded_by": "pls gate"}
    if gate == "G4" and decision == "approved":
        # what the person approved: the content of each planned release (unplanned ids stay unbound → apply refuses)
        bound = {}
        for rel in releases:
            try:
                bound[rel] = RD.digest(root, rel)
            except RD.DigestError:
                bound[rel] = None
        rec["bound"] = bound
    out = d / f"{today}-{gate}-{at[11:19].replace(':', '')}-{secrets.token_hex(3)}.json"
    with out.open("x", encoding="utf-8", newline="\n") as f:          # "x": an existing record is never overwritten
        f.write(json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
    return out


def latest(root: Path, gate: str, *, item: str | None = None, release: str | None = None) -> dict | None:
    """The last decision of this gate that covers the item or release (a later rejection overrides an approval).

    Ordered by the instant in `at`, not by the recorder's local date (approvers in different time zones); on the
    same instant any decision other than "approved" wins, so a tie never lets an approval through."""
    hits = [g for g in load(root) if g["gate"] == gate and
            (item is None or item in g.get("items", [])) and (release is None or release in g.get("releases", []))]
    return max(hits, key=lambda g: (g["_t"], g["decision"] != "approved")) if hits else None


def require(root: Path, gate: str, release: str, why: str) -> None:
    g = latest(root, gate, release=release)
    if g and g.get("decision") == "approved":
        _approver_for(root, g.get("approver", ""), gate)      # a hand-written record by anyone else does not count
    if not g or g.get("decision") != "approved":
        raise GateError(f"{why} needs a recorded {gate} approval of {release} "
                        f"({'last decision: ' + g['decision'] if g else 'none recorded'}) — "
                        f"after the person approves, record it with `pls gate {gate} --approver <name> --release {release} --quote …`")
    if gate == "G4":
        try:
            why_not = RD.check(root, release, (g.get("bound") or {}).get(release))
        except RD.DigestError as ex:
            why_not = str(ex)
        if why_not:
            raise GateError(f"{why}: {why_not}")


# ---------------------------------------------------------------- onboarding before change work (Origin `existing`)

_ORIGIN = re.compile(r"^\|\s*Origin\s*\|\s*`?(new|existing)`?\s*\|", re.M)
ONBOARDING_SUMMARY = "ops/onboarding/*-summary.md"


def origin(root: Path) -> str | None:
    """Origin of the project profile (`new` / `existing`); None when the row is missing or still the template text."""
    m = _ORIGIN.search(PR.effective_profile_text(root))
    return m.group(1) if m else None


def onboarding_missing(root: Path) -> bool:
    """True for a taken-over app (Origin `existing`) whose onboarding has not been recorded yet."""
    return origin(root) == "existing" and not any(root.glob(ONBOARDING_SUMMARY))


def require_onboarding(root: Path, what: str) -> None:
    """Refuse change work on a taken-over app before its onboarding (lifecycle section 0): the as-is state, the
    environments and the open decisions are unknown until then."""
    if onboarding_missing(root):
        raise GateError(f"{what}: the profile says Origin `existing` and there is no onboarding summary ({ONBOARDING_SUMMARY}). "
                        "Run the onboarding first (skill pls-x-onboarding, read only); save a change request that arrives "
                        "before it as requirements/sources/<date>-pending-<slug>.md without analysis")


def lint(root: Path) -> list[dict]:
    """L-GATE-01: an approval written in a document has a matching record by a profile approver.
    L-ONB-01: no REQ / DES documents for a taken-over app before its onboarding."""
    issues = []
    if onboarding_missing(root):
        docs = [p.relative_to(root).as_posix() for d, pat in (("requirements", "REQ-*.md"), ("design/decisions", "DES-*.md"))
                if (root / d).exists() for p in sorted((root / d).glob(pat))]
        if docs:
            issues.append({"rule": "L-ONB-01", "site": "-", "msg": f"Origin `existing` without an onboarding summary "
                           f"({ONBOARDING_SUMMARY}), but change documents exist: {', '.join(docs[:5])}"
                           f"{' …' if len(docs) > 5 else ''} — onboarding comes first (lifecycle section 0)"})
    try:
        load(root)
    except GateError as ex:            # a damaged record is itself the finding; the checks below would all refuse
        issues.append({"rule": "L-GATE-01", "site": "-", "msg": str(ex)})
        return issues
    names = {n.casefold() for n in approvers(PR.effective_profile_text(root))}

    def who_of(rest: str) -> str | None:
        m = _WHO.match(rest)
        return m.group(1) if m else None

    def check(path: Path, gate: str, who: str | None, item: str | None, release: str | None):
        rel = path.relative_to(root).as_posix()
        if who is not None and who.strip().casefold() not in names:
            issues.append({"rule": "L-GATE-01", "site": "-", "msg": f"{rel}: {gate} approved by {who.strip()!r}, who is not an approver in CLAUDE.md"})
        g = latest(root, gate, item=item, release=release)
        if not g or g.get("decision") != "approved":
            issues.append({"rule": "L-GATE-01", "site": "-", "msg": f"{rel}: says {gate} approved but gates/ has no approval record "
                                                                    f"for {item or release} (`pls gate`)"})

    for p in sorted((root / "requirements").glob("REQ-*.md")) if (root / "requirements").exists() else []:
        for gate, rest in _STATUS.findall(p.read_text(encoding="utf-8")):
            check(p, gate.upper(), who_of(rest), _ID.match(p.name).group(0) if _ID.match(p.name) else p.stem, None)
    for p in sorted((root / "design" / "decisions").glob("DES-*.md")) if (root / "design" / "decisions").exists() else []:
        for gate, rest in _STATUS.findall(p.read_text(encoding="utf-8")):
            check(p, gate.upper(), who_of(rest), _ID.match(p.name).group(0) if _ID.match(p.name) else p.stem, None)
    for p in sorted((root / "releases").glob("*/g3-verification.md")) if (root / "releases").exists() else []:
        for gate, rest in _STATUS.findall(p.read_text(encoding="utf-8")):
            check(p, gate.upper(), who_of(rest), None, p.parent.name)
    for p in sorted((root / "releases").glob("*/approvals.md")) if (root / "releases").exists() else []:
        if _G4_ROW.search(p.read_text(encoding="utf-8")):
            check(p, "G4", None, None, p.parent.name)
    return issues
