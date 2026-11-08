"""Script tooling (plan BR7): syntax check, site ids inside script bodies, cross-reference index.

Site ids inside scripts become ${site:x} in git (D3), so a script keeps working in another environment. A number
that only looks like a site id (a coordinate, a constant inside a minified library) must stay literal: replacing it
would change the code wherever the site has another id. Decimals are never ids (`4.797`). For other cases a person
records the number in design/refs-literal.json — {"literal": [{"site", "number", "context", "reason", "by", "date"}]}.
A decision applies only to the **script bodies of that site** and only where the raw text contains the recorded
context (contexts, not line numbers, so the decision survives edits elsewhere in the script).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

# (site, number) → contexts that keep it literal; loaded once per pls run from design/refs-literal.json
LITERAL: dict[tuple[str, str], list[str]] = {}
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
    f = project / "design" / "refs-literal.json"
    if not f.exists():
        return
    try:
        entries = json.loads(f.read_text(encoding="utf-8-sig")).get("literal") or []
        for x in entries:
            site, num, ctx = str(x["site"]), str(x["number"]), x["context"]
            why = check_context(ctx, num)
            if why:
                raise ValueError(f"entry {num!r} for {site}: {why}")
            LITERAL.setdefault((site, num), []).append(ctx)
    except (ValueError, KeyError, TypeError, AttributeError) as ex:
        LITERAL.clear()
        raise ValueError(f"design/refs-literal.json: {ex}") from ex


def for_site(site: str | None) -> dict[str, list[str]]:
    """number → contexts recorded for one site (empty for settings, meta and unknown sites)."""
    return {num: ctx for (s, num), ctx in LITERAL.items() if s == site} if site else {}


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


def replace_ids(s: str, ids: dict[str, str], literal: dict[str, list[str]] | None = None) -> str:
    """Replace standalone site ids by ${site:x} in one pass over the original string, except inside contexts
    recorded as literal (computed on the original text, so the result does not depend on the order of ids)."""
    if not ids:
        return s
    literal = literal or {}
    spans = {num: _spans(s, literal.get(num, [])) for num in ids}
    pat = re.compile("|".join(f"(?P<n{i}>{id_pattern(num)})" for i, num in enumerate(ids)))
    nums = list(ids)

    def sub(m: re.Match) -> str:
        num = nums[int(m.lastgroup[1:])]
        if any(a <= m.start() and m.end() <= b for a, b in spans[num]):
            return m.group(0)
        return "${site:%s}" % ids[num]
    return pat.sub(sub, s)


def literal_left(body: str, num: str, literal: dict[str, list[str]] | None = None) -> list[int]:
    """Positions of a raw id that is NOT covered by a literal decision (for lint L-REF-01)."""
    spans = _spans(body, (literal or {}).get(num, []))
    return [m.start() for m in re.finditer(id_pattern(num), body)
            if not any(a <= m.start() and m.end() <= b for a, b in spans)]


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
