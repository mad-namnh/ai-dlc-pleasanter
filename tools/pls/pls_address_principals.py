"""Principals inside mail addresses of notifications and reminders.

Pleasanter expands the address tokens `[Group<id>]`, `[User<id>]` and `[Dept<id>]` to the mail addresses of that
group's / department's members or of that user (`Libraries/Mails/Addresses.cs`, `ConvertedMailAddresses`; reminders
pass `To` through `Addresses.Get`, `Libraries/Settings/Reminder.cs`). The ids differ per environment, so git holds
`[${principal:<name>}]` (environments.json principals) and pack writes the token back for the target environment —
the same mapping as process access control (`acl_to_refs` / `acl_from_refs`, D20).

Every string field of every mail-sending element is mapped (`pls_side_effects.mail_elements`): the mapping is
lossless both ways, so no address field name has to be assumed. An id with no principal stays raw (lint L-PERM-01).
"""
from __future__ import annotations

import re
from typing import Any, Callable

import pls_side_effects as SE

TOKEN = re.compile(r"\[(Group|User|Dept)(\d+)\]")
REF = re.compile(r"\[\$\{principal:([A-Za-z0-9_.-]+)\}\]")


def _rewrite(v: Any, fn: Callable[[str], str]) -> Any:
    if isinstance(v, str):
        return fn(v)
    if isinstance(v, list):
        return [_rewrite(x, fn) for x in v]
    if isinstance(v, dict):
        return {k: _rewrite(x, fn) for k, x in v.items()}
    return v


def _each_element(settings: dict, fn: Callable[[str], str]) -> None:
    """Apply fn to every string of every mail element, in place (elements are the dicts inside settings)."""
    for el in SE.mail_elements(settings).values():
        if isinstance(el, dict):
            new = _rewrite(el, fn)
            el.clear()
            el.update(new)


def to_refs(settings: dict, principals: dict) -> None:
    """Export → git: `[Group379]` → `[${principal:manager}]` when environments.json maps `manager` to `Group,379`."""
    rev = {str(v): k for k, v in (principals or {}).items()}

    def fn(s: str) -> str:
        return TOKEN.sub(lambda m: "[${principal:%s}]" % rev[f"{m.group(1)},{m.group(2)}"]
                         if f"{m.group(1)},{m.group(2)}" in rev else m.group(0), s)
    _each_element(settings, fn)


def from_refs(settings: dict, principals: dict, site: str, fail: Callable[[str], Exception]) -> None:
    """Git → payload: `[${principal:manager}]` → `[Group379]`. Raises fail(...) for a name without a principal."""
    def fn(s: str) -> str:
        def one(m: re.Match) -> str:
            val = (principals or {}).get(m.group(1))
            if val is None:
                raise fail(f"unresolved reference ${{principal:{m.group(1)}}} in a mail address of {site} — "
                           "add it to environments.json principals")
            typ, _, pid = str(val).partition(",")
            pid = pid.split(",")[0]
            if typ not in ("Group", "User", "Dept") or not pid.isdigit():
                raise fail(f"{site}: principal '{m.group(1)}' is {val!r}, not a Group, User or Dept id")
            return f"[{typ}{pid}]"
        raw = TOKEN.search(s)
        if raw:                     # an id of the environment the export came from would mail other people elsewhere
            raise fail(f"{site}: a mail address uses the environment-specific id {raw.group(0)} (L-PERM-01) — "
                       "map the principal in environments.json principals")
        return REF.sub(one, s)
    _each_element(settings, fn)


def raw_tokens(settings: dict) -> list[tuple[str, str]]:
    """(element path, token) for every environment-specific id left in a mail element (lint L-PERM-01)."""
    out = []

    def walk(path: str, v: Any) -> None:
        if isinstance(v, str):
            out.extend((path, m.group(0)) for m in TOKEN.finditer(v))
        elif isinstance(v, list):
            for x in v:
                walk(path, x)
        elif isinstance(v, dict):
            for x in v.values():
                walk(path, x)
    for path, el in SE.mail_elements(settings).items():
        walk(path, el)
    return out
