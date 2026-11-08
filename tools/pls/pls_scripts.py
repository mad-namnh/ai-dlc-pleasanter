"""Script tooling (plan BR7): syntax check, site ids inside script bodies, cross-reference index.

A site id written as a site id (`siteId === 797`, `SITE_ID", 116`, `/items/797/`, `[[797]]`) becomes ${site:x} in
git (D3), so a script keeps working in another environment. Every other number stays as it is, even when it equals a
site id: status codes, timings, colours and choice codes often do (PLAY BOARD trial), and rewriting them would change
code that runs today. `pls refs` lists those numbers as POSSIBLE; a person decides, recorded in
design/refs-literal.json — {"literal": [...], "reference": [...]}, entries {"site", "number", "context", "reason",
"by", "date"}: `literal` keeps a number inside an id context, `reference` turns a number outside one into ${site:x}.
A decision applies only to the **script bodies of that site** and only where the raw text contains the recorded
context (contexts, not line numbers, so the decision survives edits elsewhere in the script).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

# (site, number) → contexts that keep it literal / make it a reference; loaded once per pls run from
# design/refs-literal.json
LITERAL: dict[tuple[str, str], list[str]] = {}
REFERENCE: dict[tuple[str, str], list[str]] = {}
REF_TOKEN = re.compile(r"\$\{(site|env|principal):([A-Za-z0-9_\-]+)\}")
MIN_CONTEXT = 8          # characters of a context besides the number itself


def check_context(context: str, number: str) -> str | None:
    """Why a context is unusable, or None. A short or generic context would protect numbers it was not meant for."""
    if not context or number not in context:
        return f"the context must contain the number {number}"
    rest = context.replace(number, "", 1)
    if len(rest.strip()) < MIN_CONTEXT:
        return f"the context needs at least {MIN_CONTEXT} characters besides the number"
    if not re.search(r"[^\d\W_]|[^\x00-\x7f]", rest):
        return "the context needs at least one letter (digits and punctuation alone match too much)"
    if "${" in context or "⏎" in context or "\n" in context:
        return "the context must be raw text on one line (no ${…} references, no line breaks)"
    return None


def load_literal(project: Path) -> None:
    LITERAL.clear()
    REFERENCE.clear()
    f = project / "design" / "refs-literal.json"
    if not f.exists():
        return
    try:
        doc = json.loads(f.read_text(encoding="utf-8-sig"))
        for key in ("literal", "reference"):
            for x in doc.get(key) or []:
                site, num, ctx = str(x["site"]), str(x["number"]), x["context"]
                why = check_context(ctx, num)
                if why:
                    raise ValueError(f"{key} entry {num!r} for {site}: {why}")
                if key == "literal":            # a literal number is the same in every environment
                    LITERAL.setdefault((site, num), []).append(ctx)
                else:                           # a reference follows its target site: stored without the number
                    if not x.get("target"):
                        raise ValueError(f"reference entry {num!r} for {site}: 'target' (logical site) is missing")
                    REFERENCE.setdefault(site, []).append((str(x["target"]), _template(ctx, num)))
    except (ValueError, KeyError, TypeError, AttributeError) as ex:
        LITERAL.clear()
        REFERENCE.clear()
        raise ValueError(f"design/refs-literal.json: {ex}") from ex


def _template(context: str, number: str) -> str:
    """The context with its site id cut out: `{id}` stands where the number was (the first standalone occurrence)."""
    m = re.search(id_pattern(number), context)
    return context[:m.start()] + "{id}" + context[m.end():] if m else context


def for_site(site: str | None) -> dict[str, list[str]]:
    """number → literal contexts recorded for one site (empty for settings, meta and unknown sites)."""
    return {num: ctx for (s, num), ctx in LITERAL.items() if s == site} if site else {}


def references_for(site: str | None, ids: dict[str, str]) -> dict[str, list[str]]:
    """number → reference contexts of one site, written with THIS environment's id of each target site (`ids`:
    number → logical name), so a decision recorded on dev also holds for an stg or prod export."""
    by_name = {name: num for num, name in ids.items()}
    out: dict[str, list[str]] = {}
    for target, tpl in REFERENCE.get(site, []) if site else []:
        if target in by_name:
            out.setdefault(by_name[target], []).append(tpl.replace("{id}", by_name[target]))
    return out


def reference_tokens(site: str | None) -> list[str]:
    """Reference contexts of one site as they read in git (`${site:target}` where the number was)."""
    return [tpl.replace("{id}", "${site:%s}" % target) for target, tpl in REFERENCE.get(site, [])] if site else []


def id_pattern(number: str) -> str:
    """A standalone site id: not part of a longer number, and never the fraction or integer part of a decimal
    (`4.797`, `797.5`) — seen in SVG path data and minified libraries (site 797, BR7) — and never a number glued
    to a letter, `_`, `#` or `%`: CSS and time values (`110px`, `110ms`, `110%`), colours (`#110`) and names
    (`item110`, `v110a`) are not ids (PLAY BOARD trial: 20 such values had been replaced).
    ASCII only, so an id written right after Japanese text is still found."""
    return r"(?<![0-9A-Za-z_.#])%s(?![0-9A-Za-z_%%]|\.\d)" % re.escape(number)


def _spans(s: str, contexts: list[str]) -> list[tuple[int, int]]:
    out = []
    for ctx in contexts:
        start = s.find(ctx)
        while start != -1:
            out.append((start, start + len(ctx)))
            start = s.find(ctx, start + 1)
    return out


# Text right before a number that makes it a site id. Anything else stays a literal number: in a real app (PLAY
# BOARD) about 9 in 10 numbers equal to a site id were status codes, timings, colours, choice codes or prose.
# A name that holds a site id: siteId, SiteId, getSiteId, SITE_ID, NOTIFICATION_SITE_ID, site_id, SITE_ID_DEFAULT —
# not websiteId, siteIdx, SITE_IDLE_TIMEOUT (a camel-case or `_` boundary before "site", nothing but `_…` after "id").
SITE_ID_NAME = r"(?:(?<![A-Za-z])site|Site|SITE)_?(?:Id|ID|id)(?:_\w*)?(?![A-Za-z0-9])"
ID_CONTEXT = re.compile(r"""(?x)(?:
      %(name)s(?:\(\))?\s*(?:===?|!==?|=|:|\()\s*["']?            # siteId === 797, siteId: 797, getSiteId(797
    | %(name)s["']\s*[:,]\s*                                       # "SiteId": 797, 'NOTIFICATION_SITE_ID', 116
    | (?<![\w.$])items\.[A-Z]\w*\(\s*                              # server script items.Get(797, …) — PascalCase API only
    | \$p\.api\w*\(\s*\{[^()]{0,60}?(?<![\w$])["']?id["']?\s*:\s*  # client $p.apiGet({ … id: 797, … })
    | /items/                                                      # /api/items/797/get
    | items/["']\s*\+\s*                                            # '/api/items/' + 797
    | \[\[                                                         # ChoicesText link [[797]]
    | (?:Class|Num|Date|Description|Check|Attachments)\w*~          # linked column ClassA~797
    )\Z""" % {"name": SITE_ID_NAME})
# Text right after the number: 797 === $p.siteId(), 797 == siteId
AFTER_CONTEXT = re.compile(r"""\A\s*(?:===?|!==?)\s*[\w$.]*?%s""" % SITE_ID_NAME)
CONTEXT_REACH = 80        # characters looked at around the number (line breaks included: `items.Get(\n  797`)


def in_id_context(s: str, start: int, end: int | None = None) -> bool:
    """True when the number at s[start:end] is written as a site id (text before it, or a comparison after it)."""
    if ID_CONTEXT.search(s[max(0, start - CONTEXT_REACH):start]):
        return True
    if end is None:
        m = re.match(r"\d+", s[start:])
        end = start + (m.end() if m else 0)
    return bool(AFTER_CONTEXT.match(s[end:end + CONTEXT_REACH]))


def _covered(spans: list[tuple[int, int]], m: re.Match) -> bool:
    return any(a <= m.start() and m.end() <= b for a, b in spans)


def replace_ids(s: str, ids: dict[str, str], literal: dict[str, list[str]] | None = None,
                reference: dict[str, list[str]] | None = None) -> str:
    """Replace site ids by ${site:x} where they are written as site ids: in an id context (ID_CONTEXT), or inside a
    context a person recorded as a reference. A context recorded as literal always keeps the number. Every other
    number stays as it is, so the deployed code is byte for byte the code that runs today (no rewriting of an
    existing app). One pass over the original string, so the result does not depend on the order of ids."""
    if not ids:
        return s
    literal, reference = literal or {}, reference or {}
    keep = {num: _spans(s, literal.get(num, [])) for num in ids}
    ref = {num: _spans(s, reference.get(num, [])) for num in ids}
    pat = re.compile("|".join(f"(?P<n{i}>{id_pattern(num)})" for i, num in enumerate(ids)))
    nums = list(ids)

    def sub(m: re.Match) -> str:
        num = nums[int(m.lastgroup[1:])]
        if _covered(keep[num], m) or not (in_id_context(s, m.start(), m.end()) or _covered(ref[num], m)):
            return m.group(0)
        return "${site:%s}" % ids[num]
    return pat.sub(sub, s)


def possible_ids(body: str, num: str) -> list[int]:
    """Positions of a raw number equal to a site id that is NOT in an id context: left as it is, listed by
    `pls refs` as POSSIBLE so a person can mark a real reference (`--ref`)."""
    return [m.start() for m in re.finditer(id_pattern(num), body) if not in_id_context(body, m.start(), m.end())]


def literal_left(body: str, num: str, literal: dict[str, list[str]] | None = None) -> list[int]:
    """Positions of a raw id in an id context that is NOT covered by a literal decision (lint L-REF-01): a site id
    written as a site id must be ${site:x}; numbers elsewhere are not ids unless a person says so."""
    spans = _spans(body, (literal or {}).get(num, []))
    return [m.start() for m in re.finditer(id_pattern(num), body)
            if in_id_context(body, m.start(), m.end()) and not _covered(spans, m)]


def unstable_refs(body: str, site: str | None) -> list[str]:
    """${site:x} tokens in a git body that the next unpack would turn back into numbers: outside an id context and
    not covered by a recorded reference (lint L-REF-03). Fix: write it in an id context, or `pls refs --ref`."""
    spans = _spans(body, reference_tokens(site))
    return [m.group(2) for m in REF_TOKEN.finditer(body) if m.group(1) == "site"
            and not in_id_context(body, m.start(), m.end()) and not _covered(spans, m)]


def numeric_context(body: str, start: int, end: int) -> bool:
    before = body[:start].rstrip(" ")[-1:]
    after = body[end:].lstrip(" ")[:1]
    return bool(re.match(r"[\d.,\-]", before or "")) or bool(re.match(r"[\d.]", after or ""))


def render(text: str, resolve: dict[str, str]) -> str:
    """Git text with ${site:x} shown as this environment's numbers (raw form, as a context is recorded)."""
    return REF_TOKEN.sub(lambda m: resolve.get(m.group(2), m.group(0)) if m.group(1) == "site" else m.group(0), text)


def site_refs(scripts: dict, resolve: dict[str, str]) -> list[dict]:
    """Every ${site:x} inside a git script body, with the raw text around it on the same line."""
    out = []
    for kind, items in scripts.items():
        for it in items or []:
            body = it.get("Body") or ""
            for m in REF_TOKEN.finditer(body):
                if m.group(1) != "site":
                    continue
                num = resolve.get(m.group(2), "?")
                line_start = body.rfind("\n", 0, m.start()) + 1
                line_end = body.find("\n", m.end())
                line_end = len(body) if line_end == -1 else line_end
                left = render(body[max(line_start, m.start() - 30):m.start()], resolve)
                right = render(body[m.end():min(line_end, m.end() + 30)], resolve)
                out.append({"kind": kind, "script": it.get("Name") or it.get("Title") or f"Id {it.get('Id')}",
                            "line": body.count("\n", 0, m.start()) + 1, "site": m.group(2), "number": num,
                            "context": (left + num + right).replace("\r", ""),
                            "suspicious": numeric_context(body, m.start(), m.end())})
    return out


def keep_literal(body: str, site: str, number: str, context: str, resolve: dict[str, str]) -> tuple[str, int]:
    """Turn the ${site:<site>} tokens that lie inside an occurrence of `context` (in the raw rendering of the body)
    back into the literal number. Returns (new body, occurrences changed)."""
    token = "${site:%s}" % site
    out, last, n = [], 0, 0
    for m in re.finditer(re.escape(token), body):
        lo, hi = max(0, m.start() - len(context) - 40), min(len(body), m.end() + len(context) + 40)
        left = render(body[lo:m.start()], resolve)
        window = left + number + render(body[m.end():hi], resolve)
        t0, t1 = len(left), len(left) + len(number)
        covered = any(a <= t0 and t1 <= a + len(context) for a in (k.start() for k in re.finditer(re.escape(context), window)))
        if covered:
            out.append(body[last:m.start()])
            out.append(number)
            last = m.end()
            n += 1
    out.append(body[last:])
    return "".join(out), n


# ---------------------------------------------------------------- syntax

NODE_CHECK = r"""
const vm = require('vm'); let data = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', c => data += c).on('end', () => {
  const out = [];
  for (const it of JSON.parse(data)) {
    const code = it.wrap ? '(function(){\n' + it.body + '\n})' : it.body;
    try { new vm.Script(code, {filename: 'script'}); }
    catch (e) {
      const m = /:(\d+)\s*$/.exec((e.stack || '').split('\n')[0] || '');
      const line = m ? +m[1] - (it.wrap ? 1 : 0) : null;
      out.push({label: it.label, line: line && line > 0 ? line : null, message: String(e.message)});
    }
  }
  process.stdout.write(JSON.stringify(out));
});
"""


def node_path() -> str | None:
    return shutil.which("node")


def node_available() -> bool:
    return node_path() is not None


def syntax_errors(items: list[tuple[str, str, bool]]) -> list[dict]:
    """Compile every body with node — nothing is executed. items: (label, body, wrap). Server scripts are wrapped in
    a function (a top-level `return` is allowed there; how Pleasanter wraps them is not in the KB), client scripts are
    compiled as they are, as a browser would. References are replaced by 0. Raises RuntimeError if node fails."""
    if not items:
        return []
    node = node_path()
    if not node:
        raise RuntimeError("node not found")
    payload = [{"label": label, "body": REF_TOKEN.sub("0", body), "wrap": wrap} for label, body, wrap in items]
    try:
        res = subprocess.run([node, "-e", NODE_CHECK], input=json.dumps(payload), capture_output=True, text=True,
                             encoding="utf-8", timeout=120)
    except (OSError, subprocess.SubprocessError) as ex:
        raise RuntimeError(str(ex)) from ex
    if res.returncode != 0:
        raise RuntimeError(f"node failed: {res.stderr.strip()[:300]}")
    return json.loads(res.stdout or "[]")


# ---------------------------------------------------------------- cross reference

COLUMN_RE = re.compile(r"\b((?:Class|Num|Date|Description|Check|Attachments)(?:[A-Z]|\d{3})|Title|Body|Status|Manager|Owner|"
                       r"StartTime|CompletionTime|WorkValue|ProgressRate|Comments)\b")


def xref(settings: dict, scripts: dict) -> dict:
    """Which script uses which column and which site (static text match; a name in a comment counts too)."""
    labels = {c["ColumnName"]: c.get("LabelText", "") for c in settings.get("Columns") or []}
    by_script, by_column = [], {}
    for kind, items in scripts.items():
        for it in items or []:
            body = it.get("Body") or ""
            name = it.get("Name") or it.get("Title") or f"Id {it.get('Id')}"
            cols = sorted(set(COLUMN_RE.findall(body)))
            sites = sorted({m.group(2) for m in REF_TOKEN.finditer(body) if m.group(1) == "site"})
            by_script.append({"kind": kind, "script": name, "columns": cols, "sites": sites})
            for c in cols:
                by_column.setdefault(c, {"label": labels.get(c, ""), "scripts": []})["scripts"].append(f"{kind}/{name}")
    return {"scripts": by_script, "columns": dict(sorted(by_column.items()))}


# ---------------------------------------------------------------- POSSIBLE numbers: grouping for display

# Display groups for numbers equal to a site id that stay as written. A group never changes the code or a decision:
# it only tells a person which lines need reading ("other") and which are almost certainly not site ids.
POSSIBLE_GROUPS = (
    ("comment", re.compile(r"^\s*(//|/\*|\*|<!--)")),
    ("log or message text", re.compile(r"(console\.\w+|pbWarn|pbLog|logTag|log\w*\(|warn\(|error\(|\[playboard\])", re.I)),
    ("status or code value", re.compile(r"STATUS|_CODE|CODES|Status\b|status\b|choice", re.I)),
    ("timing or retry", re.compile(r"setTimeout|setInterval|sleep|delay|interval|timeout|retry|attempt|\bms\b", re.I)),
    ("colour or layout", re.compile(r"rgba?\(|px\b|width|height|margin|padding|top|left|z-index|font", re.I)),
)


def possible_group(line: str) -> str:
    """Display group of a POSSIBLE number from the text of its line; 'other' when nothing matches."""
    for name, rx in POSSIBLE_GROUPS:
        if rx.search(line):
            return name
    return "other"
