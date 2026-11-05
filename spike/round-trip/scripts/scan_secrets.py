"""Scan exported files for values that may be secrets / sensitive information.

Prints only the PATH and the detection type, never the value (safe to share the log).

  python scripts/scan_secrets.py data/local/original
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from common import read_json

PATTERNS = {
    "url": re.compile(r"https?://[^\s\"']+"),
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "token-like": re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),
    "keyword": re.compile(r"(?i)(password|passwd|secret|token|apikey|api_key|bearer|webhook)"),
}


def walk(obj, path="$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    folder = Path(sys.argv[1])
    hits = []
    for f in sorted(folder.glob("*.normalized.json")):
        for path, val in walk(read_json(f)):
            for name, rx in PATTERNS.items():
                if rx.search(val):
                    hits.append((f.name, path, name))
    for fname, path, name in hits:
        print(f"{name:11} {fname}  {path}")
    print("\nSummary by type:", dict(Counter(h[2] for h in hits)))
    generic = Counter(re.sub(r"\[\d+\]", "[]", h[1]) for h in hits).most_common(15)
    print("Most frequent paths (input for ADR-0005):")
    for p, n in generic:
        print(f"  {n:4}  {p}")


if __name__ == "__main__":
    main()
