"""Side effects of configuration outside production: mail and scheduled jobs (ADR-0010).

Notifications and reminders are configuration that *runs*: a notification fires when a record changes,
a reminder fires on a schedule. On a non-production environment they can mail real people. Each
environment therefore declares what its side effects do, and `pls` refuses risky actions until a
person has stated that the environment is safe.

environments.json:
    envs.<env>.side_effects = {"mail": "unknown|sink|disabled|live", "jobs": "unknown|disabled|live"}
Missing values mean "unknown". Only a person sets them; agents never change them to get past a refusal.

Pure functions only (stdlib); pls.py wires them into lint, release-plan, apply, test and http-check.
"""
from __future__ import annotations

import json
import re
from typing import Any

MAIL_STATES = ("unknown", "sink", "disabled", "live")
JOB_STATES = ("unknown", "disabled", "live")
MAIL_SAFE = ("sink", "disabled")          # a test or release may fire mail only into these

# A literal address; Pleasanter placeholders such as [Manager] and pls references ${env:x} are not matched.
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+\-${])[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+")

# Sections of SiteSettings whose elements send mail (process notifications are nested in Processes).
SITE_SECTIONS = ("Notifications", "Reminders")


def effects(env_conf: dict) -> dict:
    """The declared side effects of one environment, with defaults. Raises ValueError on an unknown value."""
    se = env_conf.get("side_effects") or {}
    if not isinstance(se, dict):
        raise ValueError(f"side_effects = {se!r}; expected an object such as {{'mail': 'unknown', 'jobs': 'unknown'}}")
    mail, jobs = se.get("mail", "unknown"), se.get("jobs", "unknown")
    if mail not in MAIL_STATES:
        raise ValueError(f"side_effects.mail = {mail!r}; expected one of {', '.join(MAIL_STATES)}")
    if jobs not in JOB_STATES:
        raise ValueError(f"side_effects.jobs = {jobs!r}; expected one of {', '.join(JOB_STATES)}")
    return {"mail": mail, "jobs": jobs}


def _keys(items: list | None) -> list[tuple[str, dict]]:
    """(key, item) for the dict items of a list. Key = Id (stable in Pleasanter), prefixed by the Name when there is
    one (processes), else the list position. Names are not unique in Pleasanter, so a clash gets '#<index>'."""
    out, seen = [], set()
    for i, it in enumerate(items or []):
        if not isinstance(it, dict):
            continue
        k = str(it["Id"]) if "Id" in it else f"#{i}"
        if it.get("Name"):
            k = f"{it['Name']}:{k}"
        if k in seen:
            k = f"{k}#{i}"
        seen.add(k)
        out.append((k, it))
    return out


def mail_elements(settings: dict) -> dict[str, Any]:
    """Every element of a site that can send mail, keyed by a stable path such as
    'Notifications[1]', 'Reminders[2]' or 'Processes[return:1].Notifications[1]'.
    Disabled elements and non-mail notification types are included on purpose: the guard errs on the safe side."""
    out: dict[str, Any] = {}
    for sec in SITE_SECTIONS:
        for k, it in _keys(settings.get(sec)):
            out[f"{sec}[{k}]"] = it
    for pk, p in _keys(settings.get("Processes")):
        for nk, n in _keys(p.get("Notifications")):
            out[f"Processes[{pk}].Notifications[{nk}]"] = n
    return out


def changed_mail_elements(before: dict, after: dict) -> list[str]:
    """Mail-sending elements added, removed or changed between two SiteSettings (live → git)."""
    a, b = mail_elements(before), mail_elements(after)
    canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True)   # noqa: E731
    out = []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            out.append(f"{k} added")
        elif k not in b:
            out.append(f"{k} removed")
        elif canon(a[k]) != canon(b[k]):
            out.append(f"{k} changed")
    return out


def literal_addresses(settings: dict) -> list[tuple[str, str]]:
    """(element path, address) for every literal mail address inside a mail-sending element (lint L-MAIL-01).
    Every string field is scanned, so reminder address fields are covered without relying on their names."""
    found = []

    def walk(path: str, v: Any) -> None:
        if isinstance(v, dict):
            for k, x in v.items():
                walk(path, x)
        elif isinstance(v, list):
            for x in v:
                walk(path, x)
        elif isinstance(v, str):
            for m in EMAIL_RE.findall(v):
                found.append((path, m))
    for path, el in mail_elements(settings).items():
        walk(path, el)
    return found


def test_writes(spec: dict) -> bool:
    """True when a test spec changes data or executes a process (which fires notifications)."""
    return any(st.get("op") in ("create", "update", "delete", "exec") for st in spec.get("steps") or [])


def test_sites(spec: dict, default_site: Any, all_sites: set) -> set[str]:
    """Site ids a spec writes to, as pls_http.run_tests sends the requests:
    - create -> its `site`, else the command's site (never `run_on`, which only selects the configuration read);
    - update / delete / exec on a record created earlier in the spec -> that create's site;
    - update / delete / exec on any other record (a --var fixture) -> its site is unknown, so every site of the env."""
    sites, created = set(), {}
    for st in spec.get("steps") or []:
        op = st.get("op")
        if op == "create":
            site = str(st.get("site") or default_site)
            sites.add(site)
            if st.get("save"):
                created[st["save"]] = site
        elif op in ("update", "delete", "exec"):
            var = str(st.get("record") or "").lstrip("$")
            if var in created:
                sites.add(created[var])
            else:
                sites |= {str(x) for x in all_sites} | {str(default_site)}
    return sites


def test_refusal(env: str, eff: dict, mailing_sites: dict[str, list[str]]) -> str | None:
    """Reason to refuse a test run, or None. mailing_sites: site id → its mail-sending elements (live)."""
    if eff["mail"] in MAIL_SAFE or not mailing_sites:
        return None
    detail = "; ".join(f"site {s}: {', '.join(els[:3])}{' …' if len(els) > 3 else ''}" for s, els in sorted(mailing_sites.items()))
    return (f"REFUSED (ADR-0010): these tests change records on sites that send mail ({detail}), and envs.{env}.side_effects.mail "
            f"is {eff['mail']!r}. Every notification and reminder counts, also disabled ones (safe side), and a record given by --var "
            "counts for every site of the env. A person checks the environment's SMTP and sets mail to 'sink' or 'disabled' first.")


def apply_refusal(env: str, eff: dict, changed: dict[str, list[str] | None]) -> tuple[str | None, str | None]:
    """(refusal, warning) for applying a release whose mail-sending elements changed. changed: site -> items, or None
    when the plan was made before this guard existed (its mail changes are unknown)."""
    unplanned = sorted(s for s, v in changed.items() if v is None)
    if unplanned and eff["mail"] not in MAIL_SAFE:
        return (f"REFUSED (ADR-0010): the plan does not record mail-sending changes for {', '.join(unplanned)} (planned before "
                f"this check) and envs.{env}.side_effects.mail is {eff['mail']!r}. Run pls release-plan again with a new release id."), None
    changed = {s: v for s, v in changed.items() if v}
    if not changed:
        return None, None
    detail = "; ".join(f"{s}: {', '.join(v)}" for s, v in sorted(changed.items()) if v)
    if eff["mail"] == "unknown":
        return (f"REFUSED (ADR-0010): the release changes mail-sending elements ({detail}) and envs.{env}.side_effects.mail is "
                "'unknown'. A person checks the environment's SMTP and records mail as sink, disabled or live."), None
    if eff["mail"] == "live":
        return None, f"WARNING (ADR-0010): {env} sends real mail; this release changes {detail}"
    return None, None


def describe(env: str, eff: dict) -> str:
    """One line for http-check."""
    tail = ("tests that change records on sites with notifications or reminders are refused"
            if eff["mail"] not in MAIL_SAFE else "tests may fire mail into the declared " + eff["mail"])
    return f"side effects: mail {eff['mail']}, jobs {eff['jobs']} — {tail} (ADR-0010)"
