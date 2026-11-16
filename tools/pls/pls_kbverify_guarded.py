"""Guarded KB probes (ADR-0025): a probe with a server script, or with steps run under a test user's key.

A probe file may carry, beyond the shape of pls_kbverify:

    "site": {"SiteSettings": {"ServerScripts": [{"Id": 1, "Name": "…", "BeforeUpdate": true, "Body": "…"}], …}},
    "roles": {"<role>": <site permission value 1–511 for the role's group>},     # e.g. 1 = read (KB D19)
    "tests": [{"id": "…", "steps": [{"op": "create", …}, {"op": "exec", "as_key": "<role>", …}]}],
    "teardown": {"SiteSettings": {…}}                                          # required; never a server script

Guards, all checked by pls (Nam's decision of 2026-11-12, "Both, guarded"):
- kb-verify itself runs only on a dev environment that is not a sandbox, under the probe folder (ADR-0009);
- the environment's `side_effects.mail` is `sink` or `disabled`: a script that sends mail reaches nobody;
- a script body names none of `items`, `notifications`, `httpClient` (other sites, mail, the network) and none of a
  list of common ways around a name (escapes, `globalThis`, `this`, `eval`, `Function`, `constructor`, `prototype`,
  `Reflect`, `Proxy`, `fromCharCode`, computed access other than `[0]` / `['literal']`). This refuses the obvious
  routes, it is not a sandbox: a script runs with the administrator's rights when the administrator's key saves a
  record, so the review of the probe file is the control against a script that reaches another site or the network;
  the mail guard holds for mail only;
- a role is bound to a group on the environment (`pls principals`), and its key reference is the test user's own key
  file that `pls test-users` writes (never an operator's or a person's key);
- after the run pls saves the teardown settings without any server script and, for a probe with roles, sets the
  site's permissions back to the administrator alone — also when the probe failed or stopped on an unexpected
  error. A probe without roles never changes the site's permissions;
- then pls deletes the probe site (`/api/items/<id>/deletesite`, route read in the source at tag
  Pleasanter_1.5.2.0 — not yet observed on a server) and believes it only when `getsite` no longer finds the site.
  It deletes only a site that `getsite` shows to be this probe's own just before (folder, title, type, not an app
  site). A site that is not gone stays harmless (previous point) and the probe is `error`; the next run reuses it.
- a guarded probe with further probe sites (`sites`, ADR-0026) declares a teardown for each; every one of its sites
  gets the roles' grant while it runs and the same end (teardown without script, grant removed, deleted);
  `$group_<role>` in step data is the group id of a declared, bound role.
"""
from __future__ import annotations

import re
from pathlib import Path

import pls_http as H
import pls_side_effects as SE
import pls_test_users as TU

SCRIPT_FORBIDDEN = re.compile(
    r"\b(?:items|notifications|httpClient|globalThis|this|eval|Function|require|import|constructor|prototype"
    r"|__proto__|Reflect|Proxy|fromCharCode|fromCodePoint)\b"         # host objects, and common ways to reach them
    r"|\\[ux]"                                                          # escaped identifiers
    r"|[\w\)\]]\s*\[\s*(?!\d+\s*\])(?!(['\"])[^'\"]*\1\s*\])")         # computed access other than [0] or ['literal']
ROLE_NAME = re.compile(r"^[a-z0-9_]+$")
ADMIN_ALL = 511                                     # all rights (KB api.md, site permissions)


def scripts(p: dict) -> list:
    return list(((p.get("site") or {}).get("SiteSettings") or {}).get("ServerScripts") or [])


def _has_notices(o) -> bool:
    if isinstance(o, dict):
        return any((str(k).casefold() in ("notifications", "reminders") and v) or _has_notices(v) for k, v in o.items())
    if isinstance(o, list):
        return any(_has_notices(x) for x in o)
    return False


def notices(p: dict) -> bool:
    """Disabled notifications or reminders in a probe site's settings or a settings step (ADR-0027): such a probe runs
    only where mail goes to a sink or is disabled, and its sites end like any guarded probe's (teardown, deleted)."""
    steps = [st for spec in p.get("tests") or [] for st in spec.get("steps") or []
             if st.get("op") in ("settings", "settings_partial")]
    return _has_notices([(p.get("site") or {}).get("SiteSettings"),
                         [(s or {}).get("SiteSettings") for s in (p.get("sites") or {}).values() if isinstance(s, dict)],
                         [st.get("SiteSettings") or st.get("body") for st in steps]])


def is_guarded(p: dict) -> bool:
    return bool(scripts(p) or p.get("roles") or notices(p))


def _as_keys(p: dict) -> set[str]:
    out = set()
    for spec in (p.get("tests") or []) + ([{"steps": p["cleanup"]}] if p.get("cleanup") else []):
        out |= {str(spec["as_key"])} if "as_key" in spec else set()
        out |= {str(st["as_key"]) for st in spec.get("steps") or [] if "as_key" in st}
    return out


def check(p: dict) -> None:
    """Raise ValueError when a guarded probe breaks a rule that the file alone decides."""
    for i, s in enumerate(scripts(p)):
        if not isinstance(s, dict) or not isinstance(s.get("Body"), str):
            raise ValueError(f"ServerScripts[{i}] must be an object with a Body")
        bad = sorted({m.group(0).strip() for m in SCRIPT_FORBIDDEN.finditer(s["Body"])})
        if bad:
            raise ValueError(f"ServerScripts[{i}] uses {bad}: a probe script stays on its own record (no other sites, "
                             "mail or network, and no way around a name)")
    roles = p.get("roles")
    if roles is not None:
        if not isinstance(roles, dict) or not roles:
            raise ValueError("roles must be an object {role: permission value}")
        for role, v in roles.items():
            if not ROLE_NAME.match(str(role)) or type(v) is not int or not 1 <= v <= ADMIN_ALL:
                raise ValueError(f"roles.{role}: a role name of a-z, 0-9, _ and a permission value 1–{ADMIN_ALL}")
    undeclared = sorted(_as_keys(p) - set(roles or {}))
    if undeclared:
        raise ValueError(f"as_key {undeclared} not declared in roles (only a test user's key, ADR-0025)")
    if is_guarded(p):
        td = (p.get("teardown") or {}).get("SiteSettings")
        if not isinstance(td, dict):
            raise ValueError("a probe with a server script, roles or notifications needs a teardown that leaves the "
                             "site harmless")
        if "ServerScripts" in td:
            raise ValueError("the teardown must not contain ServerScripts")
        for key, s in (p.get("sites") or {}).items():          # every further site ends like the main one (ADR-0026)
            td = ((s.get("teardown") if isinstance(s, dict) else None) or {}).get("SiteSettings")
            if not isinstance(td, dict):
                raise ValueError(f"sites.{key}: a probe with a server script, roles or notifications needs a teardown "
                                 "for every site")
            if "ServerScripts" in td:
                raise ValueError(f"sites.{key}: the teardown must not contain ServerScripts")


def not_runnable(p: dict, env: str, env_conf: dict, conn: dict, conn_dir: Path) -> str | None:
    """Why a guarded probe cannot run on this environment, or None. Decided before anything is written for it."""
    try:
        mail = SE.effects(env_conf)["mail"]
    except ValueError as ex:
        return str(ex)
    if mail not in SE.MAIL_SAFE:
        return (f"side_effects.mail of {env} is {mail!r}: a probe with a server script, a test user or a (disabled) "
                f"notification runs only where "
                f"mail goes to a sink or is disabled ({', '.join(SE.MAIL_SAFE)})")
    keys = conn.get("keys") or {}
    for role in sorted(p.get("roles") or {}):
        if not re.fullmatch(r"Group,\d+", str((env_conf.get("principals") or {}).get(role) or "")):
            return f"role {role} is not bound to a group on {env} — pls principals --env {env}"
        _, key_file, ref = TU.files(conn_dir, env, role)
        if keys.get(role) != ref or not key_file.exists():
            return (f"role {role}: its key is not the test user's key file ({ref}) — pls test-users --env {env}; a "
                    "probe never runs under an operator's or a person's key")
        try:
            same = H.resolve_key(conn, role) == H.resolve_key(conn, None)
        except H.TransportError as ex:
            return f"role {role}: {ex}"
        if same:                                     # the file holds the operator's own key: the role would be the admin
            return (f"role {role}: its key file holds the same key as the operator's default key — the steps would "
                    f"run as the administrator; pls test-users --env {env} issues the test user's own key")
    return None


def permissions(p: dict, admin_uid: str, principals: dict) -> list[str]:
    """Site permissions while the probe runs: the administrator, and each declared role's group."""
    out = [f"User,{admin_uid},{ADMIN_ALL}"]
    for role, v in sorted((p.get("roles") or {}).items()):
        out.append(f"Group,{str(principals[role]).split(',')[1]},{v}")
    return out


def delete_probe_site(client, site_id: int, is_own) -> tuple[bool, str | None]:
    """Delete one probe site after its teardown. (True, None) when `getsite` no longer finds it; (False, reason)
    otherwise. `is_own(site data)` must hold just before the delete, or nothing is sent."""
    try:
        code, js, _ = client.call(f"/api/items/{site_id}/getsite")
        if code != 200 or not is_own(((js or {}).get("Response") or {}).get("Data") or {}):
            return False, f"site {site_id} not deleted: getsite → HTTP {code} or not this probe's site — kept as it is"
        code, _, _ = client.call(f"/api/items/{site_id}/deletesite", {})
        if code != 200:
            return False, f"site {site_id} not deleted: deletesite → HTTP {code} — kept without script or grant"
        code, js, _ = client.call(f"/api/items/{site_id}/getsite")
    except H.TransportError as ex:
        return False, f"site {site_id} not deleted: {ex} — kept without script or grant"
    if code == 200:
        return False, (f"site {site_id} not deleted: deletesite answered 200 but getsite still finds it — kept "
                       "without script or grant; a person deletes it in Pleasanter")
    if code != 404:                                  # 5xx, 401, 429 …: unknown, never believed as gone
        return False, (f"site {site_id} not believed deleted: deletesite answered 200, then getsite → HTTP {code} "
                       "(only 404 counts) — kept in the state file; the next run checks it again")
    return True, None
