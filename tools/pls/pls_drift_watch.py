"""Scheduled drift check on the task owner's machine (team rollout A1, N19, N20): read-only.

Each run exports the sites of the environments in scope with the person's own key and compares them with the last
applied release (`pls drift`), so a UI edit is reported to the person without them asking. The report says what
changed, how `classify` sees reverting it, and the two ways on: take the change into git as a change request, or
revert it in the next release. Only the person's decision goes into the repository (`ops/drift/`); the results of the
job stay on the machine in `.pls/drift-watch/` (gitignored with the rest of `.pls/`).

Scope of a machine: the environments its `.pls/connections.json` names directly, role dev or stg, not sandboxes —
a developer's machine has no stg connection (N12), so stg is checked only where its key is — plus the environments
the person named with `pls drift-watch install --env` (their own sandbox `dev-<name>`). prod is never read here.

The baseline must be current: an environment is not reported while the shared branch holds an applied release of it
that this folder lacks or holds in another state (another person's release would look like a UI edit). The modules
take the functions that reach Pleasanter and git as arguments, so they are tested without a server.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

STATE = Path(".pls") / "drift-watch"
STALE_AFTER = timedelta(hours=2)            # the job's interval (N25): an older result is refreshed at session start
LOCK_ABANDONED = timedelta(minutes=30)      # the job's time limit: a lock older than this was left by a dead run
APPLIED = ("applied", "applied-differs")
READ_ROLES = ("dev", "stg")


class WatchError(Exception):
    """A refusal of the drift job: the message names what to do."""


def state_dir(r: Path) -> Path:
    return r / STATE


def settings(r: Path) -> dict:
    try:
        s = json.loads((state_dir(r) / "settings.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return s if isinstance(s, dict) else {}


def _connections(r: Path) -> dict:
    p = Path(os.environ["PLS_CONNECTIONS"]) if os.environ.get("PLS_CONNECTIONS") else r / ".pls" / "connections.json"
    try:
        c = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return c if isinstance(c, dict) else {}


def scope(r: Path, envs: dict, named: list[str] | None = None) -> dict[str, list[str]]:
    """Environment → sites to check. `named` replaces the default scope (D1); a named prod or unknown environment is
    a refusal. Sites: those with an id; of a sandbox only its own copies (the shared ones belong to the base)."""
    named = named if named else settings(r).get("envs") or []
    if named:
        for env in named:
            e = envs.get(env)
            if not isinstance(e, dict):
                raise WatchError(f"unknown environment '{env}' — name one of {sorted(envs)}")
            if e.get("role") not in READ_ROLES:
                raise WatchError(f"{env}: role {e.get('role')!r} — the drift job reads dev and stg environments only "
                                 "(customer environments have their own mechanism, team rollout N16)")
        chosen = list(dict.fromkeys(named))
    else:
        conns = _connections(r)
        chosen = [env for env, e in envs.items() if isinstance(e, dict) and isinstance(conns.get(env), dict)
                  and e.get("role") in READ_ROLES and not e.get("sandbox_of")]
    out = {}
    for env in chosen:
        e, sites = envs[env], []
        for site, v in sorted((envs[env].get("sites") or {}).items()):
            if isinstance(v, dict) and v.get("id") and (v.get("sandbox") or not e.get("sandbox_of")):
                sites.append(site)
        out[env] = sites
    return out


# ---------------------------------------------------------------- baseline currency (D3)

def _applied_state(plan) -> tuple | None:
    if not isinstance(plan, dict) or plan.get("status") not in APPLIED:
        return None
    return plan.get("status"), plan.get("applied_at")


def behind(r: Path, git: Callable[[list[str]], tuple[int, str]], shared: str | None) -> tuple[dict[str, list[str]], str]:
    """Environments whose applied releases on the shared branch this folder lacks, and a note on what was compared.
    `git(args)` returns (exit code, stdout). Raises WatchError when the shared branch cannot be read: no environment
    with a shared baseline may then be reported."""
    code, remotes = git(["remote"])
    if code != 0 or not remotes.strip():
        return {}, "no git remote: the baseline is this folder's releases/ (not compared with a shared branch)"
    code, _ = git(["fetch", "--quiet"])
    if code != 0:
        raise WatchError("git fetch failed — the shared branch could not be read, so another person's release could "
                         "look like a UI edit; nothing reported for the shared environments (check the network / VPN)")
    if not shared:
        code, out = git(["rev-parse", "--abbrev-ref", "origin/HEAD"])
        shared = out.strip() if code == 0 and out.strip() and out.strip() != "origin/HEAD" else None
    if not shared:
        raise WatchError("the shared branch is not known (origin/HEAD is not set) — name it once: "
                         "pls drift-watch install --shared-branch origin/<branch>")
    code, out = git(["diff", "--name-only", shared, "--", "releases/"])
    if code != 0:
        raise WatchError(f"git diff against {shared} failed — is the branch name right? (pls drift-watch install "
                         "--shared-branch origin/<branch>)")
    late: dict[str, list[str]] = {}
    for path in sorted({p.strip() for p in out.splitlines() if p.strip().endswith("/plan.json")}):
        code, text = git(["show", f"{shared}:{path}"])
        try:
            theirs = json.loads(text) if code == 0 else None
        except ValueError:
            theirs = None
        if not _applied_state(theirs):
            continue                                   # not applied there (or not there): not a baseline we miss
        try:
            mine = json.loads((r / path).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError):
            mine = None
        if _applied_state(mine) != _applied_state(theirs):
            late.setdefault(str(theirs.get("env")), []).append(str(theirs.get("release") or Path(path).parent.name))
    return late, f"baseline compared with {shared}"


# ---------------------------------------------------------------- one run

def run(r: Path, envs: dict, targets: dict[str, list[str]], *, export: Callable[[str, int], dict],
        compare: Callable[[str, dict, str, dict], dict], git: Callable[[list[str]], tuple[int, str]],
        now: datetime | None = None) -> dict:
    """Check every site of `targets`. `export(env, site_id)` reads a site; `compare(env, e, site, export)` returns
    {"differences", "classification", "rules", "baseline", "text"}. Nothing is written to Pleasanter."""
    now = now or datetime.now().astimezone()
    result = {"checked_at": now.isoformat(timespec="seconds"), "envs": {}}
    shared_envs = [env for env in targets if not envs[env].get("sandbox_of")]
    late, refusal = {}, None
    if shared_envs:
        try:
            late, result["baseline"] = behind(r, git, settings(r).get("shared_branch"))
        except WatchError as ex:
            refusal = str(ex)
    for env, sites in targets.items():
        e = envs[env]
        if env in shared_envs and (refusal or late.get(env)):
            result["envs"][env] = {"state": "not checked", "reason": refusal or (
                f"this folder lacks the applied release(s) {', '.join(late[env])} of the shared branch — pull it "
                "first (git pull), then run pls drift-watch run")}
            continue
        out = {"state": "checked", "sites": {}}
        for site in sites:
            try:
                live = export(env, e["sites"][site]["id"])
                exp_file = state_dir(r) / "exports" / f"{env}-{site}.json"
                exp_file.parent.mkdir(parents=True, exist_ok=True)
                exp_file.write_text(json.dumps(live, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
                c = compare(env, e, site, live)
                out["sites"][site] = {"state": "drift" if c["differences"] else "clean", **c}
            except Exception as ex:                    # noqa: BLE001 — one site's failure is reported, the rest go on
                out["sites"][site] = {"state": "error", "error": f"{type(ex).__name__}: {ex}"[:300]}
        result["envs"][env] = out
    result["signature"] = signature(result)
    return result


def failed(message: str, now: datetime | None = None) -> dict:
    """A run that stopped before reading any site: kept as the last result, so the session start shows the reason
    (and waits the interval) instead of starting the same failing run at every session."""
    result = {"checked_at": (now or datetime.now().astimezone()).isoformat(timespec="seconds"), "envs": {},
              "error": message}
    result["signature"] = signature(result)
    return result


def signature(result: dict) -> str:
    """What the person was last told: the sites not clean and their differences (D5). Empty when all is clean."""
    items = [["", "", "error", result["error"]]] if result.get("error") else []
    for env, v in sorted(result.get("envs", {}).items()):
        if v.get("state") != "checked":
            items.append([env, "", "not checked", v.get("reason", "")])
        for site, s in sorted((v.get("sites") or {}).items()):
            if s.get("state") != "clean":
                items.append([env, site, s.get("state"), s.get("text") or s.get("error", "")])
    return hashlib.sha256(json.dumps(items, ensure_ascii=False).encode("utf-8")).hexdigest()[:16] if items else ""


def problems(result: dict) -> list[str]:
    """One line per environment not checked and per site not clean (or the reason the run stopped)."""
    out = [f"the check stopped: {result['error']}"] if result.get("error") else []
    for env, v in sorted(result.get("envs", {}).items()):
        if v.get("state") != "checked":
            out.append(f"{env}: not checked — {v.get('reason')}")
            continue
        for site, s in sorted((v.get("sites") or {}).items()):
            if s["state"] == "drift":
                out.append(f"{env}/{site}: {s['differences']} difference(s) from the last release — reverting would be "
                           f"{s.get('classification')}")
            elif s["state"] == "error":
                out.append(f"{env}/{site}: not read — {s.get('error')}")
    return out


def report(result: dict) -> str:
    """The Markdown report: the summary, then per drifted site its differences and the two ways on."""
    lines = [f"# Drift check {result.get('checked_at')}", ""]
    if result.get("baseline"):
        lines += [result["baseline"], ""]
    found = problems(result)
    lines += [f"- {x}" for x in found] if found else ["Every site checked matches its last release."]
    for env, v in sorted(result.get("envs", {}).items()):
        for site, s in sorted((v.get("sites") or {}).items()):
            if s.get("state") != "drift":
                continue
            rules = ", ".join(sorted({x.get("id", "") for x in s.get("rules") or []})) or "none"
            lines += ["", f"## {env}/{site}", "", s.get("text", "").strip(), "", f"Rules of `classify`: {rules}.", "",
                      "Two ways on — decide, then record the decision in `ops/drift/<date>-" + env + "-" + site + ".md`:",
                      f"1. Keep the UI change: `pls harvest --env {env} --site {site}`, then a change request through "
                      "the gates (REQ → G1 …).",
                      f"2. Revert it: the next release to {env} restores the git configuration; plan it with "
                      f"`--accept-drift ops/drift/<that record>` (the release has its own gate)."]
    return "\n".join(lines) + "\n"


def save(r: Path, result: dict) -> tuple[bool, str]:
    """Write last.json / last.md. Returns (the person should be told: the signature changed and is not empty, the
    previous signature)."""
    d = state_dir(r)
    d.mkdir(parents=True, exist_ok=True)
    prev = load(r) or {}
    (d / "last.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    (d / "last.md").write_text(report(result), encoding="utf-8", newline="\n")
    return bool(result["signature"]) and result["signature"] != prev.get("signature"), prev.get("signature", "")


def load(r: Path) -> dict | None:
    try:
        v = json.loads((state_dir(r) / "last.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    return v if isinstance(v, dict) else None


# ---------------------------------------------------------------- one run at a time (D7)

def _lock_age(r: Path, now: datetime) -> timedelta | None:
    """Age of the lock, or None when there is none or it cannot be read (a damaged lock counts as abandoned)."""
    p = state_dir(r) / "running.json"
    if not p.exists():
        return None
    try:
        return now - datetime.fromisoformat(json.loads(p.read_text(encoding="utf-8"))["started"])
    except (OSError, ValueError, KeyError, TypeError):
        return LOCK_ABANDONED


def take_lock(r: Path, now: datetime | None = None) -> bool:
    now = now or datetime.now().astimezone()
    p = state_dir(r) / "running.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            with open(p, "x", encoding="utf-8") as f:
                json.dump({"pid": os.getpid(), "started": now.isoformat(timespec="seconds")}, f)
            return True
        except FileExistsError:
            age = _lock_age(r, now)
            if age is not None and age < LOCK_ABANDONED:
                return False
            p.unlink(missing_ok=True)                  # left by a run that died
    return False


def drop_lock(r: Path) -> None:
    (state_dir(r) / "running.json").unlink(missing_ok=True)


def running(r: Path, now: datetime | None = None) -> bool:
    age = _lock_age(r, now or datetime.now().astimezone())
    return age is not None and age < LOCK_ABANDONED
