"""The framework version a project is pinned to (ADR-0022, ADR-0014 TB-6; team rollout phase 4, Nam 2026-11-18 "1a 2a 3a").

`pls skills sync` records in `.claude/framework.lock` the framework commit, its release tag and whether the shipped parts
had uncommitted changes. Every later run compares the framework checkout the launcher found with that pin:

- the checkout is another commit, or `tools/`, `skills/` or `templates/` hold uncommitted changes, or the lock was
  synced from such a tree → the code running is not the version the project pinned;
- writes outside dev (apply, bootstrap, migrate, tests that change records) are refused then; on dev they are
  allowed with a warning (the developer may be trying a fix);
- a newer `v*` release tag in the framework is reported (session-start hook); `pls http-check` shows the pin too.

A project whose lock has no commit (not synced yet) is not checked: `pls init` and `pls skills sync` always write one.
Git is the only source: a framework that is not a git checkout cannot be confirmed and counts as not pinned.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

SHIPPED = ("tools", "skills", "templates")          # what projects run or copy from the framework


def _git(fw: Path, *args: str) -> str | None:
    try:
        p = subprocess.run(["git", "-C", str(fw), *args], capture_output=True, text=True, encoding="utf-8", timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def state(fw: Path) -> dict:
    """The framework checkout: commit (short), release tag on it, uncommitted changes in the shipped parts, latest tag."""
    commit = _git(fw, "rev-parse", "HEAD")
    porcelain = _git(fw, "status", "--porcelain", "--untracked-files=all", "--", *SHIPPED)
    tags = _git(fw, "tag", "--list", "v*", "--sort=-v:refname") or ""
    return {"commit": commit or None,
            "tag": _git(fw, "describe", "--tags", "--exact-match", "--match", "v*", "HEAD") or None,
            "dirty": None if porcelain is None else bool(porcelain),
            "latest_tag": next((t for t in tags.splitlines() if re.fullmatch(r"v\d+(\.\d+)*", t.strip())), None)}


def _lock(project: Path) -> dict:
    p = project / ".claude" / "framework.lock"
    try:
        lock = json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}
    except (OSError, ValueError):
        return {}
    return lock if isinstance(lock, dict) else {}


def _tag(lock: dict) -> str | None:
    t = lock.get("tag")
    return t if isinstance(t, str) and t else None


def valid_commit(c) -> bool:
    """A commit id the pin can rely on: 7 to 40 lowercase hex digits."""
    return isinstance(c, str) and re.fullmatch(r"[0-9a-f]{7,40}", c) is not None


def _same(a: str | None, b: str | None) -> bool:
    """Two commit ids name the same commit: full or abbreviated, never shorter than 7 hex digits."""
    ok = lambda x: bool(x) and re.fullmatch(r"[0-9a-f]{7,40}", x) is not None      # noqa: E731
    return ok(a) and ok(b) and (a.startswith(b) or b.startswith(a))


def _short(c: str | None) -> str:
    return (c or "?")[:10]


def problem(project: Path, fw: Path, now: dict | None = None) -> str | None:
    """Why the framework running is not the version the project pinned, or None when it is. A project without a lock
    file (not made by `pls init`) is not checked; a lock that cannot say what it pinned — no commit, an unknown commit,
    or no record of uncommitted changes — counts as not pinned (fail closed)."""
    if not (project / ".claude" / "framework.lock").exists():
        return None
    lock = _lock(project)
    pinned = lock.get("commit")
    if not valid_commit(pinned) or not (lock.get("tag") is None or isinstance(lock.get("tag"), str)):
        return ("the project's framework.lock names no framework commit (git could not read the framework when it was "
                "synced, or the lock was edited) — run pls skills sync from a release tag")
    if lock.get("dirty") is not False:
        return ("the project's framework.lock does not record a clean framework (synced by an older pls, or git could not "
                "read the framework, or it had uncommitted changes) — run pls skills sync from a release tag")
    now = now or state(fw)
    pin = f"{_short(pinned)}{' (' + _tag(lock) + ')' if _tag(lock) else ''}"
    if not now.get("commit") or now.get("dirty") is None:
        return f"the framework at {fw} cannot be read with git — its version cannot be confirmed against the pin {pin}"
    if now["dirty"]:
        return (f"the framework has uncommitted changes in {', '.join(SHIPPED)} — not the version this project pinned "
                f"({pin})")
    if not _same(pinned, now["commit"]):
        here = f"{_short(now['commit'])}{' (' + now['tag'] + ')' if now.get('tag') else ''}"
        return (f"the framework checkout is {here}, the project pinned {pin} — check out the pinned version in the "
                f"framework, or upgrade the project (read CHANGELOG.md, then pls skills sync and commit the lock)")
    return None


def newer_release(project: Path, now: dict, fw: Path | None = None) -> str | None:
    """A note when the framework has a release tag that comes after the commit the project pinned (a pin ahead of
    the latest tag — a framework developer's project — is not told to go back)."""
    lock, latest = _lock(project), now.get("latest_tag")
    if not latest or not valid_commit(lock.get("commit")) or _tag(lock) == latest:
        return None
    if fw is not None:
        tagged = _git(fw, "rev-list", "-n", "1", latest)
        if _same(lock["commit"], tagged):
            return None
        try:
            ahead = subprocess.run(["git", "-C", str(fw), "merge-base", "--is-ancestor", lock["commit"], latest],
                                   capture_output=True, timeout=15).returncode == 0
        except (OSError, subprocess.SubprocessError):
            ahead = False
        if not ahead:
            return None
    return (f"framework release {latest} is available (this project pinned "
            f"{_tag(lock) or 'commit ' + _short(lock.get('commit'))}) — read CHANGELOG.md before upgrading")


def session_notes(project: Path, fw: Path) -> list[str]:
    """What the session-start hook tells the agent and the person: advisory only, never blocking."""
    now = state(fw)
    return [n for n in (problem(project, fw, now), newer_release(project, now, fw)) if n]
