"""`pls check p1|p2`: what a requirement or a design document must contain, read from its front matter and body
(ADR-0029 B). The model writes the documents; this module decides whether they are complete. It does not judge
whether a requirement or a design is right — the G1 / G2 approvers do.

A finding is {"phase", "item", "msg"}: item is the REQ / DES id it is about (or "requirements" / "design" for the
whole set). `pls gate G1|G2` refuses while a finding names an item it approves, unless the approver accepts the
findings with a reason (ADR-0029, gate coupling).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pls_as_is_review_records as AR
import pls_front_matter as FM
import pls_gate as GT
import pls_impact_rules as IR

EARS_TYPES = ("ubiquitous", "event-driven", "state-driven", "unwanted behaviour", "optional", "complex")
CLASSES = ("config-only", "data-impacting", "permission-impacting")
REQ_FILE = re.compile(r"^(REQ-\d+)(?:-.*)?\.md$")
DES_FILE = re.compile(r"^(DES-\d+)(?:-.*)?\.md$")
DERIVED = re.compile(r"^derived from (REQ-\d+)\b")
NOT_A_FILE = ("P2 accepted", "drift accepted")
PROBE = re.compile(r"D\d+[a-z]?")
KB_INDEX = Path(__file__).resolve().parents[2] / "skills" / "pls-kb-pleasanter" / "references" / "probes" / "index.json"
EARS_WORDS = {"event-driven": ("when",), "state-driven": ("while",), "unwanted behaviour": ("if", "then"),
              "optional": ("where",)}


def _section(body: str, title: str) -> str | None:
    m = re.search(rf"(?m)^## {re.escape(title)}\s*$", body)
    if not m:
        return None
    nxt = re.search(r"(?m)^## ", body[m.end():])
    return body[m.end():m.end() + nxt.start()] if nxt else body[m.end():]


def _docs(folder: Path, pattern: re.Pattern) -> list[tuple[str, Path]]:
    """(id, path) of the documents of a folder. As-is records of taken-over sites (DES-000-as-is-<site>.md, written by
    pls-x-spec-recovery and reviewed through `pls review as-is`) are not designs: they are left out."""
    if not folder.is_dir():
        return []
    return sorted((m.group(1), p) for p in folder.iterdir() for m in [pattern.match(p.name)]
                  if m and p.is_file() and not p.name.startswith(AR.AS_IS_DES))


def _read(path: Path, phase: str, item: str, out: list) -> tuple[dict | None, str]:
    try:
        fm, body = FM.read(path.read_text(encoding="utf-8"))
    except FM.FrontMatterError as ex:
        out.append({"phase": phase, "item": item, "msg": f"{path.name}: front matter unreadable — {ex}"})
        return None, ""
    if fm is None:
        out.append({"phase": phase, "item": item, "msg": f"{path.name}: no front matter (template: "
                    + ("req-template.md" if phase == "p1" else "des-template.md") + ")"})
    return fm, body


def _as_list(v) -> list:
    return v if isinstance(v, list) else [] if v is None else [v]


ANSWER_REF = re.compile(r"(?:A\d+|P\d+(?:\s+accepted)?)")
CITES_ANSWERS = re.compile(r"\s[—-]\s(?:A\d+|P\d+(?:\s+accepted)?)(?:\s*,\s*(?:A\d+|P\d+(?:\s+accepted)?))*\s*$")


def _sources(v) -> list:
    """The `sources` list, with interview answer numbers put back on their file: the template writes
    `sources/<interview>.md — A3, A7`, which the flow list splits at the comma into `… — A3` and `A7` (TD-75).
    An answer number is joined to the item before it only when that item already cites answers."""
    out: list = []
    for s in _as_list(v):
        t = str(s).strip()
        if out and ANSWER_REF.fullmatch(t) and CITES_ANSWERS.search(str(out[-1])):
            out[-1] = f"{out[-1]}, {t}"
            continue
        out.append(s)
    return out


def kb_probe_ids() -> set[str]:
    """Entry ids of the framework knowledge base's probe index (empty when it cannot be read: no probe id is then known)."""
    try:
        return set(json.loads(KB_INDEX.read_text(encoding="utf-8-sig")).get("entries") or {})
    except (OSError, ValueError, AttributeError):
        return set()


def unverified_problem(root: Path, u) -> str | None:
    """Why an `unverified` entry of a DES does not stand for a component without round-trip evidence: it names the key
    `pls scope` reports and either a probe of the knowledge base or a decision record of this project that names the key."""
    if not isinstance(u, dict) or not u.get("key"):
        return f"unverified entry {u!r}: needs key (the component `pls scope` names) and probe or decision"
    key = str(u["key"])
    if bool(u.get("probe")) == bool(u.get("decision")):
        return f"unverified {key}: name exactly one of probe (a KB probe id, e.g. D41) or decision (a record file)"
    if u.get("probe"):
        if not PROBE.fullmatch(str(u["probe"])) or str(u["probe"]) not in kb_probe_ids():
            return f"unverified {key}: probe {u['probe']!r} is not an entry of the knowledge base's probe index"
        return None
    ref = str(u["decision"])
    if not _inside(root, ref):
        return f"unverified {key}: decision {ref} is not a file of this project"
    rel = (root / ref).resolve().relative_to(root.resolve()).as_posix()
    if rel.startswith("config/") or DES_FILE.match(Path(rel).name):
        return f"unverified {key}: decision {ref} is a design or configuration file, not a decision record"
    text = (root / ref).read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"(?<![\w\[]){re.escape(key)}(?![\w\]])", text):      # the key as a whole name
        return f"unverified {key}: decision {ref} does not name {key} — a decision record says which component it accepts"
    return None


def _inside(root: Path, ref: str) -> bool:
    """A file of the project, named relative to its root."""
    p = (root / ref).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return False
    return p.is_file()


def p1(root: Path) -> list[dict]:
    out: list[dict] = []
    req_dir = root / "requirements"
    docs = _docs(req_dir, REQ_FILE)
    index = (req_dir / "index.md").read_text(encoding="utf-8") if (req_dir / "index.md").exists() else ""
    seen: dict[str, str] = {}
    for p in sorted(req_dir.iterdir()) if req_dir.is_dir() else []:
        if p.is_file() and re.match(r"(?i)^req-", p.name) and not REQ_FILE.match(p.name):
            out.append({"phase": "p1", "item": "requirements", "msg": f"{p.name}: not read — name it REQ-<n>-<slug>.md"})
    for rid, path in docs:
        def f(msg: str, rid: str = rid) -> None:
            out.append({"phase": "p1", "item": rid, "msg": msg})
        if rid in seen:
            f(f"{path.name}: id {rid} is also used by {seen[rid]}")
        seen[rid] = path.name
        fm, body = _read(path, "p1", rid, out)
        if fm is None:
            continue
        if fm.get("id") != rid:
            f(f"front matter id {fm.get('id')!r} is not the file's id {rid}")
        if not fm.get("status"):
            f("no status")
        if fm.get("type") not in EARS_TYPES:
            f(f"type {fm.get('type')!r} is not an EARS type ({', '.join(EARS_TYPES)})")
        sources = _sources(fm.get("sources"))
        if not sources:
            f("no source: name the request, interview answer or REQ it comes from")
        for s in sources:
            s = str(s).strip()
            if s in NOT_A_FILE:
                continue
            d = DERIVED.match(s)
            if d:
                if d.group(1) == rid or d.group(1) not in {x for x, _ in docs}:
                    f(f"source {s!r}: derived from a requirement that is not another REQ of this project")
                continue
            ref = re.split(r"\s+[—-]\s+|\s+", s)[0]
            src = (req_dir / ref).resolve()
            try:
                src.relative_to((req_dir / "sources").resolve())
                inside = src.is_file()
            except ValueError:
                inside = False
            if not inside:
                f(f"source {ref} is not a file under requirements/sources/")
        req = _section(body, "Requirement")
        shalls = len(re.findall(r"\bshall\b", req or "", re.I))
        for word in EARS_WORDS.get(fm.get("type"), ()):
            if req is not None and not re.search(rf"\b{word}\b", req, re.I):
                f(f"type {fm.get('type')} but the requirement has no `{word}` (EARS pattern, ears.md)")
        if req is None:
            f("no `## Requirement` section")
        elif shalls != 1:
            f(f"the requirement has {shalls} `shall` — exactly one (split it)")
        crit = _section(body, "Acceptance criteria")
        n_crit = len(re.findall(r"(?m)^\s*\d+\.\s+\S", crit or ""))
        if not n_crit:
            f("no acceptance criteria (numbered list under `## Acceptance criteria`)")
        elif type(fm.get("acceptance")) is not int or fm.get("acceptance") != n_crit:
            f(f"front matter acceptance {fm.get('acceptance')!r} but the section lists {n_crit}")
        for q in _as_list(fm.get("open_questions")):
            if not re.search(rf"(?m)^\|\s*{re.escape(str(q))}\s*\|", index):
                f(f"open question {q} is not in requirements/index.md")
        if not re.search(rf"(?m)^\|\s*{re.escape(rid)}\s*\|", index):
            f("not listed in requirements/index.md")
    return out


def p2(root: Path) -> list[dict]:
    out: list[dict] = []
    reqs = {rid for rid, _ in _docs(root / "requirements", REQ_FILE)}
    covered: set[str] = set()
    for folder in (root / "design", root / "design" / "decisions"):
        for p in sorted(folder.iterdir()) if folder.is_dir() else []:
            if p.is_file() and re.match(r"(?i)^des-", p.name) and not p.name.startswith(AR.AS_IS_DES) and (
                    folder.name == "design" or not DES_FILE.match(p.name)):
                out.append({"phase": "p2", "item": "design", "msg": f"{p.relative_to(root).as_posix()}: not read — "
                            "name it design/decisions/DES-<n>-<slug>.md"})
    for did, path in _docs(root / "design" / "decisions", DES_FILE):
        def f(msg: str, did: str = did) -> None:
            out.append({"phase": "p2", "item": did, "msg": msg})
        fm, body = _read(path, "p2", did, out)
        if fm is None:
            continue
        if fm.get("id") != did:
            f(f"front matter id {fm.get('id')!r} is not the file's id {did}")
        if not fm.get("status"):
            f("no status")
        des_reqs = [str(x) for x in _as_list(fm.get("reqs"))]
        if not des_reqs:
            f("no reqs: the requirements this design meets")
        for x in des_reqs:
            if x not in reqs:
                f(f"reqs names {x}, which has no requirements/{x}-*.md")
        covered |= set(des_reqs)
        cls = fm.get("classification")
        if cls not in CLASSES:
            f(f"classification {cls!r} is not one of {', '.join(CLASSES)}")
        elif cls == "data-impacting" and not (_section(body, "Migration (only if data-impacting)")
                                              or _section(body, "Migration") or "").strip():
            f("data-impacting without a `## Migration` section (ADR-0004)")
        elements = _as_list(fm.get("elements"))
        if not elements:
            f("no elements: element → setting → REQ")
        for e in elements:
            if not isinstance(e, dict):
                f(f"element {e!r} is not an object (id, site, setting, req, rung)")
                continue
            eid = e.get("id")
            for k in ("id", "site", "setting", "req", "rung"):
                if e.get(k) in (None, ""):
                    f(f"element {eid or '?'}: no {k}")
            if e.get("req") and str(e["req"]) not in des_reqs and str(e["req"]) != "impact":
                f(f"element {eid}: req {e['req']} is not in reqs (or `impact` for an element an impact needs)")
            rung = e.get("rung")
            if rung is not None and (type(rung) is not int or not 1 <= rung <= 5):
                f(f"element {eid}: rung {rung!r} is not 1–5 (ladder, I5)")
            elif type(rung) is int and rung >= 3 and not e.get("reason"):
                f(f"element {eid}: rung {rung} needs a reason why lower rungs cannot work (I5)")
        with_element = {str(e.get("req")) for e in elements if isinstance(e, dict)}
        for x in des_reqs:
            if x not in with_element:
                f(f"{x} is in reqs but no element names it (every in-scope REQ has a design element)")
        impact = _as_list(fm.get("impact"))
        if not impact:
            f("no impact rows: walk impact-rules.md (one row per matching rule, `checked: none` when nothing changes)")
        for row in impact:
            if not isinstance(row, dict) or row.get("rule") not in IR.BY_ID:
                f(f"impact row {row!r}: rule must be an id of impact-rules.md")
            elif not row.get("action"):
                f(f"impact row {row['rule']}: no action")
        for u in _as_list(fm.get("unverified")):          # components `pls scope` reports (checked against the build at p3)
            why = unverified_problem(root, u)
            if why:
                f(why)
    approved_ids = {i for g in GT.load(root) if g.get("gate") == "G1" for i in g.get("items") or []}
    for rid in sorted((reqs | approved_ids) - covered):     # a REQ approved at G1 counts even if its file is gone
        g = GT.latest(root, "G1", item=rid)
        if g and g.get("decision") == "approved":
            out.append({"phase": "p2", "item": rid, "msg": "approved at G1 but no DES names it in reqs"})
    return out


CHECKS = {"p1": p1, "p2": p2}


def for_gate(root: Path, gate: str, items: list[str]) -> list[dict]:
    """The findings that block an approval of these items (ADR-0029 B4): the check's findings for each item and for
    misnamed documents, a finding for an item no document names (an approval is never recorded unread), and — for G2 —
    every G1-approved REQ that no DES covers."""
    found = CHECKS["p1" if gate == "G1" else "p2"](root)
    folder, pattern = ((root / "requirements", REQ_FILE) if gate == "G1" else (root / "design" / "decisions", DES_FILE))
    ids = {x for x, _ in _docs(folder, pattern)}
    out = [x for x in found if x["item"] in items or x["item"] in ("requirements", "design")]
    out += [{"phase": "p1" if gate == "G1" else "p2", "item": i,
             "msg": f"no document {folder.relative_to(root).as_posix()}/{i}-<slug>.md — nothing to check"}
            for i in items if i not in ids]
    if gate == "G2":
        out += [x for x in found if x["msg"].startswith("approved at G1 but no DES") and x not in out]
    return out
