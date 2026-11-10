"""The as-is review that lets adopted server scripts clear L-LAD-01 (invariant I4, I5).

`pls spec-skeleton` writes `design/as-is/<site>.md`; the person reviews it. `pls review as-is <site>` records that
review under `gates/review/` with the person's words and the sha256 of the document as reviewed. Only then does
`design/decisions/DES-000-as-is-<site>.md` give the scripts it names their ladder reason, and only for scripts the
reviewed document names, while the document is unchanged. The as-is document itself decides nothing.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pls_profile_records as PR

REVIEW_DIR = "gates/review"
AS_IS_DES = "DES-000-as-is-"


def _as_is(root: Path, site: str) -> Path:
    return root / "design" / "as-is" / f"{site}.md"


def record_review(root: Path, site: str, approver: str, quote: str) -> Path:
    """The person reviewed design/as-is/<site>.md: recorded with the document's sha256 (a G2 approver decides)."""
    GT = PR._gt()
    doc = _as_is(root, site)
    if not doc.is_file():
        raise GT.GateError(f"{doc.relative_to(root).as_posix()} does not exist — pls spec-skeleton --site {site} first")
    if not quote.strip():
        raise GT.GateError("--quote: the person's own words for this review are required (I4)")
    who = GT._approver_for(root, approver, "G2")
    return PR._write(root, REVIEW_DIR, f"as-is-{site}", {
        "kind": "as-is-review", "site": site, "document": doc.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(doc.read_bytes()).hexdigest(), "approver": who, "quote": quote.strip(),
        "recorded_by": "pls review"}, key="sha256")


def reviewed_as_is(root: Path) -> dict[str, str]:
    """site → text of design/as-is/<site>.md, when the latest review of that site covers the document as it is now."""
    out = {}
    for g in sorted(PR._load(root, REVIEW_DIR, "sha256"), key=lambda g: g["_t"]):
        site, doc = g.get("site"), _as_is(root, str(g.get("site")))
        if g.get("kind") == "as-is-review" and doc.is_file() and hashlib.sha256(doc.read_bytes()).hexdigest() == g["sha256"]:
            out[site] = doc.read_text(encoding="utf-8")
        else:
            out.pop(site, None)
    return out


def names(text: str, word: str) -> bool:
    """True when `word` stands in `text` as a whole name: not as part of a longer ASCII word, id or file name
    (`ab` is not named by `label` or `ab-test`). Japanese text around a name does not hide it."""
    return bool(word) and re.search(r"(?<![A-Za-z0-9_-])" + re.escape(word) + r"(?![A-Za-z0-9_-])", text) is not None


def ladder_decided(root: Path):
    """(script name, site) → True when a design decision gives that site's server script its ladder reason
    (L-LAD-01, I5).

    Only decision documents count: design/decisions/DES-*.md that name both the script and its site as whole names.
    Other design files (as-is documents, probes, notes) decide nothing, and a decision about another site does not
    cover a script of the same name here. DES-000-as-is-<site>.md counts only for scripts of that site that are
    named in the reviewed, unchanged design/as-is/<site>.md (the person reviewed exactly that list)."""
    decisions = root / "design" / "decisions"
    other, adopted = [], {}
    reviewed = reviewed_as_is(root) if decisions.exists() else {}
    for p in sorted(decisions.glob("DES-*.md")) if decisions.exists() else []:
        if p.name.startswith(AS_IS_DES):
            site = p.stem[len(AS_IS_DES):]
            if site in reviewed:
                adopted[site] = (p.read_text(encoding="utf-8"), reviewed[site])
            continue
        other.append(p.read_text(encoding="utf-8"))

    def decided(name: str | None, site: str) -> bool:
        if not name:
            return False
        if site in adopted and names(adopted[site][0], name) and names(adopted[site][1], name):
            return True
        return any(names(d, name) and names(d, site) for d in other)
    return decided
