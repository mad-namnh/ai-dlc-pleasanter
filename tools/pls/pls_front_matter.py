"""Front matter of REQ / DES documents (ADR-0029 B1): a block between `---` lines at the top of the markdown file.

The format is a small subset of YAML, read without a YAML library (pls has no dependencies):

    ---
    id: REQ-001
    status: awaiting G1
    sources: [sources/2026-11-16-mail.md, sources/2026-11-16-interview.md — A3]
    acceptance: 3
    elements:
      - id: E1
        site: loans
        rung: 2
      - id: E2
        site: loans
        rung: 3
        reason: no standard setting can …
    ---

- `key: value` — a value is an integer, `true` / `false`, `null` / empty, a "double" or 'single' quoted string, or
  plain text up to the end of the line;
- `key: [a, b]` — a list of plain values (no commas inside an item; quote it otherwise);
- `key:` followed by lines `  - value` (a list of values) or `  - k: v` with further `    k: v` lines (a list of maps).
Anything else is an error that names the line, so a document never passes a check by being misread.
"""
from __future__ import annotations

import re

KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:\s+(.*))?$")


class FrontMatterError(ValueError):
    pass


def _scalar(text: str):
    t = text.strip()
    if t == "" or t in ("null", "~"):
        return None
    if t in ("true", "false"):
        return t == "true"
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'":
        return t[1:-1]
    return t


def _flow_list(text: str, line: int) -> list:
    inner = text.strip()[1:-1].strip()
    if not inner:
        return []
    out = []
    for part in re.findall(r'\s*("[^"]*"|\'[^\']*\'|[^,]+?)\s*(?:,|$)', inner):
        if part.strip():
            out.append(_scalar(part))
    if any(isinstance(x, str) and ("[" in x or "]" in x) for x in out):
        raise FrontMatterError(f"line {line}: nested lists are not supported")
    return out


def split(text: str) -> tuple[str | None, str]:
    """(front matter text or None, body). The block must start on the first line."""
    t = text.replace("\r\n", "\n")
    if not t.startswith("---\n"):
        return None, t
    end = t.find("\n---\n", 4)
    if end < 0:
        if t.endswith("\n---"):
            end = len(t) - 4
        else:
            raise FrontMatterError("front matter opened with --- but never closed")
    return t[4:end + 1], t[end + 5:]


def parse(block: str) -> dict:
    out: dict = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        n = i + 1
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith(" "):
            raise FrontMatterError(f"line {n}: indented line without a list key above it")
        m = KEY.match(raw)
        if not m:
            raise FrontMatterError(f"line {n}: expected `key: value`")
        key, val = m.group(1), m.group(2)
        if key in out:
            raise FrontMatterError(f"line {n}: key {key} appears twice")
        if val is not None and val.strip():
            v = val.strip()
            out[key] = _flow_list(v, n) if v.startswith("[") and v.endswith("]") else _scalar(v)
            continue
        items: list = []                                   # block list below the key, or an empty value
        while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
            row = lines[i]
            n = i + 1
            i += 1
            if not row.strip():
                continue
            m2 = re.match(r"^  - (.*)$", row)
            if not m2:
                raise FrontMatterError(f"line {n}: expected `  - item` under {key}")
            first = m2.group(1)
            km = KEY.match(first)
            if not km:
                items.append(_scalar(first))
                continue
            item = {km.group(1): _scalar(km.group(2) or "")}
            while i < len(lines) and lines[i].startswith("    ") and not lines[i].startswith("  - "):
                n = i + 1
                km2 = KEY.match(lines[i].strip())
                if not km2:
                    raise FrontMatterError(f"line {n}: expected `k: v` inside an item of {key}")
                if km2.group(1) in item:
                    raise FrontMatterError(f"line {n}: key {km2.group(1)} appears twice in an item of {key}")
                v2 = (km2.group(2) or "").strip()
                item[km2.group(1)] = _flow_list(v2, n) if v2.startswith("[") and v2.endswith("]") else _scalar(v2)
                i += 1
            items.append(item)
        out[key] = items if items else None
    return out


def read(text: str) -> tuple[dict | None, str]:
    """(front matter as a dict, or None when the document has none; body)."""
    block, body = split(text)
    return (parse(block) if block is not None else None), body
