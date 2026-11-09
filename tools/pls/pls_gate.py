"""Gate decisions as records (invariant I4): who approved what, in their own words, checked against the profile.

The agent never approves a gate. After the person states a decision, `pls gate` writes one file per decision
under `gates/`, named by date, gate, time and a random suffix, so records of parallel branches never share a
name and a record is never overwritten. The record is what other
commands trust:
- `release-plan` for a stg target needs a G3 approval of that release;
- `apply` / `bootstrap` on stg need a G4 approval naming that release or bootstrap id;
- lint L-GATE-01: every "G<n> approved" status line in a REQ, DES, G3 or approvals file has its record.
Only names listed as approvers in the project profile (`CLAUDE.md`, row "Approvers") are accepted.
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import datetime, timedelta
from pathlib import Path

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
    prof = root / "CLAUDE.md"
    names = approvers(prof.read_text(encoding="utf-8")) if prof.exists() else {}
    if not names:
        raise GateError("the project profile names no approver: ask the person who approves this gate and add the name "
                        "to the Approvers row of CLAUDE.md after they say it")
    match = next((n for n in names if n.casefold() == name.strip().casefold()), None)
    if not match:
        raise GateError(f"{name!r} is not an approver in the project profile (approvers: {', '.join(sorted(names))})")
    if gate not in names[match]:
        raise GateError(f"{match} approves {', '.join(sorted(names[match]))} in the project profile, not {gate}")
    return match


def load(root: Path) -> list[dict]:
    d = root / "gates"
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))] if d.exists() else []


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
    prev = [datetime.fromisoformat(g["at"]) for g in load(root) if g.get("at")]
    if prev and now <= max(prev):
        now = max(prev) + timedelta(microseconds=1)
    at = now.isoformat(timespec="microseconds")
    out = d / f"{today}-{gate}-{at[11:19].replace(':', '')}-{secrets.token_hex(3)}.json"
    with out.open("x", encoding="utf-8") as f:          # "x": an existing record is never overwritten
        f.write(json.dumps({"gate": gate, "decision": decision, "approver": who, "date": today, "at": at,
                            "quote": quote.strip(), "items": items, "releases": releases, "recorded_by": "pls gate"},
                           ensure_ascii=False, indent=2) + "\n")
    return out


def latest(root: Path, gate: str, *, item: str | None = None, release: str | None = None) -> dict | None:
    """The last decision of this gate that covers the item or release (a later rejection overrides an approval)."""
    hits = [g for g in load(root) if g.get("gate") == gate and
            (item is None or item in (g.get("items") or [])) and (release is None or release in (g.get("releases") or []))]
    return sorted(hits, key=lambda g: (g.get("date", ""), g.get("at", "")))[-1] if hits else None


def require(root: Path, gate: str, release: str, why: str) -> None:
    g = latest(root, gate, release=release)
    if g and g.get("decision") == "approved":
        _approver_for(root, g.get("approver", ""), gate)      # a hand-written record by anyone else does not count
    if not g or g.get("decision") != "approved":
        raise GateError(f"{why} needs a recorded {gate} approval of {release} "
                        f"({'last decision: ' + g['decision'] if g else 'none recorded'}) — "
                        f"after the person approves, record it with `pls gate {gate} --approver <name> --release {release} --quote …`")


# ---------------------------------------------------------------- onboarding before change work (Origin `existing`)

_ORIGIN = re.compile(r"^\|\s*Origin\s*\|\s*`?(new|existing)`?\s*\|", re.M)
ONBOARDING_SUMMARY = "ops/onboarding/*-summary.md"


def origin(root: Path) -> str | None:
    """Origin of the project profile (`new` / `existing`); None when the row is missing or still the template text."""
    prof = root / "CLAUDE.md"
    m = _ORIGIN.search(prof.read_text(encoding="utf-8")) if prof.exists() else None
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
    prof = root / "CLAUDE.md"
    names = {n.casefold() for n in approvers(prof.read_text(encoding="utf-8"))} if prof.exists() else set()

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
