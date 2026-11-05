"""Pleasanter version of an environment (ADR-0009, part 1: the label).

Probe on MADLAB dev, 1.5.2 (2026-11-05, read-only, KB api.md "Version"):
- API responses carry no application version (`ApiVersion` 1.1 is only the request protocol echoed back);
- the page `/versions` shows it, but only to a logged-in session, so an API key cannot read it;
- the login page, readable without login, links its stylesheet as `style.min.css?v=<token>`. The token is tied to
  the installed build; how it maps to a version number is not known, so it is used only to detect that the build
  changed;
- every exported site has `SiteSettings.Version` (e.g. 1.017), the version of the settings schema.

So `pls version` detects the build and the schema automatically, and the application version (e.g. 1.5.2.0) is the
label a person reads on /versions and records with --app. When the build token changes, the recorded label is
reset to "unknown" until a person records the new one.

Stored in environments.json: envs.<env>.pleasanter = {"app", "build", "schema", "checked"}.
"""
from __future__ import annotations

import http.client
import re
import urllib.error
import urllib.request
from typing import Any, Callable

BUILD_RE = re.compile(r"style\.min\.css\?v=([A-Za-z0-9._\-]+)")
UNKNOWN = "unknown"


class PageError(OSError):
    """The login page could not be read (network, HTTP status, protocol or URL error)."""


def fetch_login_page(base_url: str, timeout: float = 15, opener: Callable = urllib.request.urlopen) -> str:
    """GET <url>/users/login without credentials (read-only). Every failure becomes PageError."""
    try:
        req = urllib.request.Request(base_url.rstrip("/") + "/users/login", headers={"User-Agent": "pls"})
        with opener(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except (OSError, http.client.HTTPException, ValueError) as ex:
        raise PageError(str(ex)) from ex


def build_token(html: str) -> str | None:
    m = BUILD_RE.search(html or "")
    return m.group(1) if m else None


def schema_version(site: dict) -> Any:
    """SiteSettings.Version of an exported site (getsite Response.Data)."""
    return (site.get("SiteSettings") or {}).get("Version")


def update_record(old: dict | None, build: str | None, schema: Any, app: str | None, today: str) -> tuple[dict, list[str]]:
    """New envs.<env>.pleasanter value and messages for the person.
    The app label is kept only while the build token is unchanged; a person sets it with `app`."""
    old = old or {}
    msgs = []
    build_changed = bool(old.get("build") and build and old["build"] != build)
    schema_changed = old.get("schema") is not None and schema is not None and old["schema"] != schema
    if build_changed:
        msgs.append(f"build changed {old['build']} → {build}: the server was upgraded or reinstalled")
    if schema_changed:
        msgs.append(f"settings schema changed {old['schema']} → {schema}: the application was upgraded")
    if not build:
        msgs.append("build token not found on the login page (page changed, proxy or SSO in front?) — the version cannot be confirmed")
    if schema is None:
        msgs.append("settings schema not read (no readable site and no parent_id)")
    confirmed = bool(build) and old.get("build") == build and not schema_changed
    if app:
        label = app
    elif old.get("app") and old.get("app") != UNKNOWN and confirmed:
        label = old["app"]
    else:
        label = UNKNOWN
    new = {"app": label, "build": build, "schema": schema, "checked": today}
    if label == UNKNOWN:
        msgs.append("application version unknown: open <url>/versions in a browser (logged in) and record it with "
                    "`pls version --env <env> --app <version>`")
    return new, msgs


def compare(target: dict | None, tested: dict | None, target_env: str, tested_env: str) -> list[str]:
    """Differences between the environment a release goes to and the one it was tested on (for G4)."""
    if not target or not tested:
        missing = [e for e, v in ((target_env, target), (tested_env, tested)) if not v]
        return [f"version of {', '.join(missing)} not recorded — run `pls version --env <env>` (ADR-0009)"]
    out = []
    for k, what in (("app", "application"), ("build", "build"), ("schema", "settings schema")):
        a, b = target.get(k), tested.get(k)
        if a in (None, UNKNOWN) or b in (None, UNKNOWN):
            out.append(f"{what} version not known for {target_env if a in (None, UNKNOWN) else tested_env}")
        elif a != b:
            out.append(f"{what}: {target_env} {a} ≠ {tested_env} {b} — behaviour the release relies on was verified on {tested_env} only")
    return out
