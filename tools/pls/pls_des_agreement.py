"""Does the built change agree with the designs that ship it? (ADR-0029 B, `pls check p3 --env --des`, `pls gate G3`)

P2 cannot know the change: it is designed before it is built. After P3 the change is the difference between the
configuration in git and what the target environment was given by its last release before the designs were approved.
This module compares that change, as `classify` and `pls scope` see it, with the front matter of the named DES:
- a changed site has an element in one of them;
- the strongest classification they give the site is at least the one `classify` computes;
- every rule id `classify` returns has an impact row;
- every component `pls scope` reports for the site has an `unverified` entry (a probe or a decision record).
It does not judge whether the design is good; G3 approvers still do. pls.py computes the change (it owns the diff).
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pls_front_matter as FM
import pls_gate as GT
import pls_phase_check as PC

SEVERITY = ("config-only", "permission-impacting", "data-impacting")


def _f(item: str, msg: str) -> dict:
    return {"phase": "p3", "item": item, "msg": msg}


def designs(root: Path, ids: list[str]) -> tuple[dict[str, dict], datetime | None, list[dict]]:
    """The front matter of each named DES, the earliest G2 approval among them, and the findings of reading them:
    a DES without a document, without readable front matter, without a standing G2 approval, or edited since that
    approval is not a design the build can be held to.

    The earliest approval, not the latest: a design approved again after a change (G2 "approve with changes") must
    not move the baseline past the dev releases P3 made in between, or the change they carry would not be compared."""
    docs = dict(PC._docs(root / "design" / "decisions", PC.DES_FILE))
    found: dict[str, dict] = {}
    out: list[dict] = []
    approved: list[datetime] = []
    for did in dict.fromkeys(ids):
        path = docs.get(did)
        if path is None:
            out.append(_f(did, f"no document design/decisions/{did}-<slug>.md — the build cannot be compared with it"))
            continue
        try:
            fm, _ = FM.read(path.read_text(encoding="utf-8"))
        except FM.FrontMatterError as ex:
            out.append(_f(did, f"{path.name}: front matter unreadable — {ex}"))
            continue
        if fm is None:
            out.append(_f(did, f"{path.name}: no front matter — the build cannot be compared with it"))
            continue
        g = GT.latest(root, "G2", item=did)
        if not g or g.get("decision") != "approved":
            out.append(_f(did, "not approved at G2 — a release ships approved designs only"))
        else:
            approved.append(min(x["_t"] for x in GT.load(root) if x["gate"] == "G2" and x["decision"] == "approved"
                                and did in x.get("items", [])))
            bound = (g.get("bound_des") or {}).get(did)
            if bound is None:
                out.append(_f(did, f"its G2 approval ({g['at']}) holds no content digest of the DES — approve it again "
                                   "at G2, so the build is compared with the design the approver saw"))
            elif bound != GT.des_digest(root, did):
                out.append(_f(did, f"{path.name} changed since its G2 approval ({g['at']}) — an edited design needs a "
                                   "new G2 before the build is compared with it"))
        found[did] = fm
    return found, (min(approved) if approved else None), out


def _items(fm: dict, key: str) -> list[dict]:
    v = fm.get(key)
    return [x for x in (v if isinstance(v, list) else []) if isinstance(x, dict)]


def scope_key(msg: str) -> str:
    """`pls scope` names a component first: "Notifications (no round-trip evidence)" → "Notifications",
    "DashboardParts[3] type 9 …" → "DashboardParts[3]"."""
    return msg.split(" ", 1)[0]


def compare(root: Path, site: str, change: dict | None, baseline: str | None, scope: list[str],
            des: dict[str, dict]) -> list[dict]:
    """Findings for one site. `change` is `classify` of the diff (None: nothing changed), `baseline` the label of what
    it was computed against (None: no earlier release on the environment), `scope` the `pls scope` messages."""
    mine = {did: fm for did, fm in des.items() if any(str(e.get("site")) == site for e in _items(fm, "elements"))}
    names = ", ".join(sorted(des)) or "no DES"
    if not mine:
        if baseline is None:      # never released on the environment: what it would carry cannot be told offline
            return [_f(site, f"no release of this site was applied on the environment before the DES were approved, and "
                             f"no element of {names} is on it — the build cannot be compared offline; name the DES that "
                             f"designs it, or check it with `pls classify` of the release-plan export and accept")]
        if change is None:
            return []
        return [_f(site, f"changed since {baseline}, but no element of {names} is on this site — name the DES that "
                         f"designs it (--des / --item), or take the change out of the release")]
    out: list[dict] = []
    if baseline is None:
        out.append(_f(site, "no release of this site was applied on the environment before the DES were approved: "
                            "the change cannot be computed offline (first release) — compare the DES with "
                            "`pls classify` of the release-plan export, then accept with a reason"))
    elif change is not None:
        have = max((SEVERITY.index(fm.get("classification")) for fm in mine.values()
                    if fm.get("classification") in SEVERITY), default=-1)
        want = change.get("classification")
        if want in SEVERITY and SEVERITY.index(want) > have:
            why = "; ".join((change.get("data_impacting") or []) + (change.get("permission_impacting") or []))[:300]
            out.append(_f(site, f"`classify` gives {want} ({why}) but {', '.join(sorted(mine))} classify it at most "
                                f"{SEVERITY[have] if have >= 0 else 'nothing'} — raise it in the DES and approve it again at G2 "
                                f"(ADR-0004), or change the build"))
        rows = {str(x.get("rule")) for fm in mine.values() for x in _items(fm, "impact")}
        for rid in dict.fromkeys(str(x.get("id")) for x in change.get("rules") or []):
            if rid not in rows:
                paths = sorted({x.get("path") for x in change["rules"] if str(x.get("id")) == rid})
                out.append(_f(site, f"rule {rid} applies ({', '.join(paths)[:200]}) but no impact row of "
                                    f"{', '.join(sorted(mine))} names it (impact-rules.md) — add the row and approve the DES again at G2"))
    listed = {str(x.get("key")) for fm in mine.values() for x in _items(fm, "unverified")
              if str(x.get("site") or "") in ("", site) and PC.unverified_problem(root, x) is None}
    for msg in scope:
        if scope_key(msg) not in listed:
            out.append(_f(site, f"`pls scope`: {msg} — no valid `unverified` entry (a KB probe, or a decision record "
                                f"that names it) in {', '.join(sorted(mine))} — add it and approve the DES again at G2"))
    return out
