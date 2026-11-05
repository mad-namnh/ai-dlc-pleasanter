"""Semantic 3-way merge of config/<site>/site.json (ADR-0011, plan BR6).

Git merges JSON as text: two developers adding two different columns conflict on list positions although the
changes are independent. This merge works on the data:
- lists of objects with a stable key (Columns by ColumnName, Processes by Name, Views by Id, …) merge element by
  element; an element changed on both sides in different ways is a conflict, everything else merges;
- lists of names (GridColumns, EditorColumnHash.General, …) take the additions and removals of both sides;
- objects merge key by key; a scalar changed differently on both sides is a conflict.
A conflict keeps "ours" in the result and is reported; the caller exits non-zero so git marks the file conflicted.
Used as a git merge driver: `pls merge-site %O %A %B` (installed by `pls merge-install`).
"""
from __future__ import annotations

from typing import Any

STABLE_KEYS = {"Columns": "ColumnName", "Processes": "Name", "Views": "Id", "Notifications": "Id", "Reminders": "Id",
               "Summaries": "Id", "Links": "ColumnName", "Aggregations": "Id", "DashboardParts": "Id",
               "Tabs": "Id", "Sections": "Id", "StatusControls": "Id", "DataChanges": "Id"}
MISSING = object()


def _keyed(items: list, key: str) -> dict | None:
    out = {}
    for it in items:
        if not isinstance(it, dict) or key not in it or str(it[key]) in out:
            return None                                   # not mergeable by key (missing or duplicate keys)
        out[str(it[key])] = it
    return out


UNIQUE_ID_LISTS = ("Processes", "Views", "StatusControls", "Notifications", "Reminders", "Sections", "Tabs", "Summaries")


def _names(o: list, a: list, b: list) -> list | None:
    """3-way merge of lists of scalars: keep the order of the side that reordered (None when both reordered
    differently), apply the other side's removals and insert its additions after the nearest preceding element."""
    common = [x for x in o if x in a and x in b]
    ord_a, ord_b = [x for x in a if x in common], [x for x in b if x in common]
    if ord_a != common and ord_b != common and ord_a != ord_b:
        return None
    if ord_b != common and ord_a == common:
        a, b = b, a                                       # theirs reordered: start from theirs
    removed_b = [x for x in o if x not in b]
    result = [x for x in a if x not in removed_b]
    for i, x in enumerate(b):
        if x in o or x in result:
            continue
        prev = next((b[j] for j in range(i - 1, -1, -1) if b[j] in result), None)
        at = result.index(prev) + 1 if prev is not None else 0
        while at < len(result) and result[at] not in o:          # after ours' own additions at that place
            at += 1
        result.insert(at, x)
    return result


def merge(o: Any, a: Any, b: Any, path: str = "", conflicts: list | None = None) -> Any:
    """Merge theirs (b) into ours (a) with base o. Conflicts are appended to `conflicts` (ours is kept)."""
    conflicts = [] if conflicts is None else conflicts
    if a == b:
        return a
    if a == o:
        return b
    if b == o:
        return a
    if o is None and isinstance(a, (dict, list)) and isinstance(b, (dict, list)):
        conflicts.append(f"{path or '(root)'}: added differently on both sides (ours kept)")
        return a
    if isinstance(a, dict) and isinstance(b, dict):
        base = o if isinstance(o, dict) else {}
        out = {}
        for k in list(a) + [k for k in b if k not in a]:
            va, vb, vo = a.get(k, MISSING), b.get(k, MISSING), base.get(k, MISSING)
            p = f"{path}.{k}" if path else k
            if va is MISSING or vb is MISSING:
                present = vb if va is MISSING else va
                if vo is MISSING:
                    out[k] = present                          # added on one side
                elif present == vo:
                    continue                                  # removed on the other side, unchanged here
                else:
                    conflicts.append(f"{p}: removed on one side, changed on the other (changed version kept)")
                    out[k] = present
                continue
            out[k] = merge(vo if vo is not MISSING else None, va, vb, p, conflicts)
        return out
    if isinstance(a, list) and isinstance(b, list):
        base = o if isinstance(o, list) else []
        key = STABLE_KEYS.get(path.rsplit(".", 1)[-1].split("[")[0])
        if key:
            ka, kb, ko = _keyed(a, key), _keyed(b, key), _keyed(base, key) if base else {}
            if ka is not None and kb is not None and ko is not None:
                merged = {}
                order = list(ka) + [k for k in kb if k not in ka]
                for k in order:
                    ea, eb, eo = ka.get(k, MISSING), kb.get(k, MISSING), ko.get(k, MISSING)
                    p = f"{path}[{k}]"
                    if ea is MISSING or eb is MISSING:
                        present = eb if ea is MISSING else ea
                        if eo is MISSING:
                            merged[k] = present
                        elif present != eo:
                            conflicts.append(f"{p}: removed on one side, changed on the other (changed version kept)")
                            merged[k] = present
                        continue
                    merged[k] = merge(eo if eo is not MISSING else None, ea, eb, p, conflicts)
                out = list(merged.values())
                name = path.rsplit(".", 1)[-1]
                if name in UNIQUE_ID_LISTS:
                    ids = [str(x.get("Id")) for x in out if isinstance(x, dict) and "Id" in x]
                    dup = sorted({i for i in ids if ids.count(i) > 1})
                    if dup:
                        conflicts.append(f"{path}: Id {', '.join(dup)} used twice after the merge — renumber one side")
                return out
        if all(not isinstance(x, (dict, list)) for x in a + b + base):
            names = _names(base, a, b)
            if names is not None:
                return names
    conflicts.append(f"{path or '(root)'}: changed on both sides (ours kept)")
    return a
