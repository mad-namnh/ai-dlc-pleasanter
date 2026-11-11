"""Run log (ADR-0013): one JSON line per `pls` command and per step marker, in the project repository.

What the framework does is visible to the whole team and readable by a future UI without parsing console text:
`ops/log/<YYYY-MM-DD>-<actor>.jsonl` (one file per day and person, so parallel branches rarely touch the same file).

Event schema v1 (every field always present; unknown values are null):
  v, ts (ISO, local offset), kind ("command" | "step"), run_id, actor, branch, head,
  cmd, args (the CLI words, nothing secret: pls never takes a key on the command line), env, site, release,
  result ("ok" | "refused" | "error"), exit_code, duration_ms, writes (true when the command may write to Pleasanter),
  metrics (small numbers a command reports: issues, changes, tests passed …; `written` = site ids a writing command
  sent a write to), message (first line of an error),
  phase / title (step markers only),
  session (the Claude Code session that ran the command — env CLAUDE_CODE_SESSION_ID, seen in Claude Code 2.1.322;
  null outside Claude Code): `pls usage collect` finds that session's transcript even when it was started in another
  folder.
A step marker opens a step; LLM token usage (`pls usage collect`) is attributed to the step open at that time.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

SCHEMA = 1
PHASES = ("onboarding", "P1", "P2", "P3", "P4", "P5", "P6", "G1", "G2", "G3", "G4", "other")
WRITING = {"apply", "migrate", "bootstrap", "test", "kb-verify", "principals", "test-users"}          # may write to Pleasanter (test_write_guards keeps this true)
METRICS: dict = {}                                            # filled by the running command (record_metric)
_DEPTH = [0]


def record_metric(**kw) -> None:
    """A command adds small numbers to its log line (issue counts, changes, tests passed, …)."""
    METRICS.update({k: v for k, v in kw.items() if v is not None})


def record_target(env: str | None = None, release: str | None = None, written: list | None = None) -> None:
    """A command that takes its environment from a plan (apply, bootstrap, migrate, mark-applied) says which
    environment and release it worked on and which site ids it wrote, so the event does not depend on --env."""
    for k, v in (("_env", env), ("_release", release)):
        if v:
            METRICS[k] = v
    if written is not None:
        METRICS["written"] = sorted({int(x) for x in written if str(x).isdigit()} | set(METRICS.get("written") or []))


def writable(root: Path) -> str | None:
    """Why today's log file cannot be appended to; None when it can. Nothing is written by the check."""
    f = log_file(root, actor(root), datetime.now().astimezone().date().isoformat())
    try:
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a", encoding="utf-8"):
            pass
        return None
    except OSError as ex:
        return f"{f.relative_to(root).as_posix()}: {ex.strerror or ex}"


def _git(root: Path, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=5)
        return (r.stdout.strip() or None) if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


_ACTOR: list = []


def _git_head(root: Path) -> tuple[str | None, str | None]:
    """(branch, short commit) read from .git directly — no git process per command (slow to start on Windows)."""
    g = root / ".git"
    try:
        if g.is_file():                                         # a worktree: "gitdir: <path>"
            g = Path(g.read_text(encoding="utf-8").split(":", 1)[1].strip())
        head = (g / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return None, head[:7]                               # detached
        ref = head[5:]
        branch = ref.rsplit("refs/heads/", 1)[-1]
        common = Path((g / "commondir").read_text(encoding="utf-8").strip()) if (g / "commondir").exists() else None
        for base in [g] + ([(g / common).resolve()] if common else []):
            if (base / ref).exists():
                return branch, (base / ref).read_text(encoding="utf-8").strip()[:7]
            packed = base / "packed-refs"
            if packed.exists():
                for line in packed.read_text(encoding="utf-8").splitlines():
                    if line.endswith(" " + ref):
                        return branch, line[:7]
        return branch, None                                     # a new repository without commits
    except (OSError, IndexError):
        return None, None


def _git_info(root: Path) -> tuple:
    """(actor, branch, head)."""
    return (actor(root), *_git_head(root))


def actor(root: Path) -> str:
    """Who runs pls: PLS_ACTOR, else git user.name (asked once per process), else the OS user. Used in the file name,
    so kept file-safe."""
    if not _ACTOR:
        name = os.environ.get("PLS_ACTOR") or _git(root, "config", "user.name") or os.environ.get("USERNAME") \
            or os.environ.get("USER") or "unknown"
        _ACTOR.append("".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:40] or "unknown")
    return _ACTOR[0]


def _option(argv: list[str], name: str) -> str | None:
    """Value of --name in argv (first one), or None."""
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return None


def _cmd(argv: list[str]) -> str | None:
    return next((a for a in argv if not a.startswith("-")), None)


def log_file(root: Path, who: str, day: str) -> Path:
    return root / "ops" / "log" / f"{day}-{who}.jsonl"


def append(root: Path, event: dict) -> Path:
    """Append one event (schema v1). Never raises: logging must not break a command."""
    try:
        now = datetime.now().astimezone()
        who, branch, head = _git_info(root)
        who = event.get("actor") or who
        base = {"v": SCHEMA, "ts": now.isoformat(timespec="milliseconds"), "kind": None, "run_id": None, "actor": who,
                "branch": branch, "head": head,
                "cmd": None, "args": None, "env": None, "site": None, "release": None, "result": None,
                "exit_code": None, "duration_ms": None, "writes": None, "metrics": None, "message": None,
                "phase": None, "title": None, "session": os.environ.get("CLAUDE_CODE_SESSION_ID") or None}
        base.update({k: v for k, v in event.items() if k in base})
        f = log_file(root, who, now.date().isoformat())
        f.parent.mkdir(parents=True, exist_ok=True)
        with open(f, "a", encoding="utf-8", newline="\n") as h:
            h.write(json.dumps(base, ensure_ascii=False) + "\n")
        return f
    except Exception:                       # noqa: BLE001 — a log line is never worth a failed command
        return Path()


def run(root_fn, argv: list[str], body) -> int:
    """Run one command (`body()` returns the exit code) and log it. Nested commands (apply → mark-applied) are
    logged too, with the same run_id."""
    try:
        root = root_fn()
    except Exception:                       # noqa: BLE001 — not inside a project: nothing to log
        return body()
    if _DEPTH[0] == 0:
        run.current = uuid.uuid4().hex[:12]
    outer = dict(METRICS)                   # each command logs only its own metrics (nested runs do not mix)
    METRICS.clear()
    cmd = _cmd(argv)
    if cmd in WRITING and "-h" not in argv and "--help" not in argv:
        # A command that may write to Pleasanter leaves a line in the run log or does not run (ADR-0013): checked
        # before anything is sent. Commands that only read still run and warn below.
        why = writable(root)
        if why:
            print(f"pls {cmd}: REFUSED — the run log cannot be written ({why}). A command that may write to Pleasanter "
                  "always leaves a log line (ADR-0013): repair ops/log/ and run it again. Nothing was sent.", file=sys.stderr)
            return 2
    _DEPTH[0] += 1
    t0, result, code, message = time.monotonic(), "error", None, None
    try:
        code = body()
        result = "ok" if code == 0 else "refused"
        return code
    except SystemExit as ex:                # argparse errors and --help: exit code as the shell sees it
        code = ex.code if isinstance(ex.code, int) else (0 if ex.code is None else 2)
        result = "ok" if code == 0 else "error"
        raise
    except Exception as ex:                 # Fail, TransportError, … — logged, then raised as before
        message = str(ex).splitlines()[0][:300] if str(ex) else type(ex).__name__
        raise
    finally:
        _DEPTH[0] -= 1
        mine = dict(METRICS)
        METRICS.clear()
        METRICS.update(outer)
        env, release = mine.pop("_env", None), mine.pop("_release", None)
        if cmd != "step":                   # a step marker writes its own event
            f = append(root, {"kind": "command", "run_id": run.current, "cmd": cmd, "args": argv,
                              "env": env or _option(argv, "--env"), "site": _option(argv, "--site"),
                              "release": release or _option(argv, "--release")
                              or (argv[1] if cmd in ("apply", "bootstrap", "mark-applied", "migrate") and len(argv) > 1 else None),
                              "result": result, "exit_code": code, "duration_ms": int((time.monotonic() - t0) * 1000),
                              "writes": cmd in WRITING, "metrics": mine or None, "message": message})
            if f == Path():                 # only reading commands get here without a log; they still say so
                print(f"pls {cmd}: warning — the run log could not be written (ops/log/); this command left no log line",
                      file=sys.stderr)


run.current = None


def step(root: Path, phase: str, title: str) -> Path:
    """Open a step: what the agent (or a person) starts now. Token usage until the next step belongs to it."""
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {', '.join(PHASES)}")
    if not title.strip():
        raise ValueError("a step needs a title")
    return append(root, {"kind": "step", "run_id": uuid.uuid4().hex[:12], "cmd": "step", "phase": phase,
                         "title": title.strip(), "result": "ok"})


def read(root: Path) -> list[dict]:
    """Every event of the project, oldest first."""
    out = []
    for f in sorted((root / "ops" / "log").glob("*.jsonl")) if (root / "ops" / "log").exists() else []:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    return sorted(out, key=lambda e: e.get("ts") or "")
