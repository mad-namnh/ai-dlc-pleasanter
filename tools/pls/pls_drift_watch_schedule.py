"""Where the drift job runs (team rollout A1, N25): Windows Task Scheduler, the session-start hook, the notification.

- `install` writes `.pls/drift-watch/settings.json` (the environments named, the shared branch) and the task as XML,
  then registers it with `schtasks /create /xml` under the person's own account: Monday to Friday from 09:00, every
  2 hours for 10 hours, only while they are logged on, missed runs started when the machine is available, one at a
  time, 30 minutes at most, working directory = the project, `pythonw.exe` when present (no console window). XML,
  not `/tr`: `/tr` sets no working directory and is limited to 261 characters. `remove` deletes the task.
- `session_notes` is what the SessionStart hook prints: the last result and its age; when it is older than the
  interval and no run is going, a check is started in the background (it never blocks the session).
- `notify` shows a Windows balloon; its text goes in an environment variable, never in the command line, so a site
  name cannot become a command.

Registering the task and the balloon are not run by the test suite (they change the person's machine); the suite
checks the XML and the command lines.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable
from xml.sax.saxutils import escape

import pls_drift_watch as DW

TASK_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
NOTIFY_PS = ("Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; "
             "$n = New-Object System.Windows.Forms.NotifyIcon; $n.Icon = [System.Drawing.SystemIcons]::Information; "
             "$n.BalloonTipTitle = 'pls drift check'; $n.BalloonTipText = $env:PLS_DRIFT_MESSAGE; $n.Visible = $true; "
             "$n.ShowBalloonTip(15000); Start-Sleep -Seconds 15; $n.Dispose()")


def task_name(r: Path) -> str:
    """One task per project folder: its name and a hash of its full path (two clones of one project differ)."""
    base = re.sub(r"[^A-Za-z0-9._-]", "_", r.resolve().name)[:40] or "project"
    return f"pls drift-watch {base} {hashlib.sha1(str(r.resolve()).lower().encode('utf-8')).hexdigest()[:8]}"


def interpreter(python: str | None = None) -> str:
    """pythonw.exe next to the running Python when it exists (no console window every two hours)."""
    exe = Path(python or sys.executable)
    w = exe.with_name("pythonw.exe")
    return str(w if w.exists() else exe)


def task_xml(r: Path, python: str, launcher: Path, start_date: str) -> str:
    args = f'"{launcher}" drift-watch run --quiet'
    days = "".join(f"<{d} />" for d in ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"))
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="{TASK_NS}">
  <RegistrationInfo><Description>pls drift check of {escape(str(r.resolve()))} (read only)</Description></RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>{start_date}T09:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <Repetition><Interval>PT2H</Interval><Duration>PT10H</Duration><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
      <ScheduleByWeek><DaysOfWeek>{days}</DaysOfWeek><WeeksInterval>1</WeeksInterval></ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>{escape(python)}</Command><Arguments>{escape(args)}</Arguments><WorkingDirectory>{escape(str(r.resolve()))}</WorkingDirectory></Exec>
  </Actions>
</Task>
"""


def install(r: Path, envs: list[str], shared: str | None, *, run: Callable[[list[str]], tuple[int, str]],
            python: str | None = None, today: str | None = None, os_name: str | None = None) -> str:
    """Record the scope and register the task. `run(argv)` runs schtasks and returns (exit code, output)."""
    if (os_name or os.name) != "nt":
        raise DW.WatchError("the job is registered with Windows Task Scheduler; on this system run "
                            "`python pls.py drift-watch run --quiet` from cron (every 2 hours, Mon–Fri 9:00–19:00)")
    launcher = r / "pls.py"
    if not launcher.exists():
        raise DW.WatchError(f"{launcher} not found — the job runs the project's launcher (pls skills sync writes it)")
    d = DW.state_dir(r)
    d.mkdir(parents=True, exist_ok=True)
    (d / "settings.json").write_text(json.dumps({"envs": envs, "shared_branch": shared}, indent=2) + "\n",
                                     encoding="utf-8", newline="\n")
    xml = d / "task.xml"
    xml.write_text(task_xml(r, interpreter(python), launcher, today or datetime.now().date().isoformat()),
                   encoding="utf-16")              # schtasks /xml reads UTF-16 with its BOM
    name = task_name(r)
    code, out = run(["schtasks", "/create", "/tn", name, "/xml", str(xml), "/f"])
    if code != 0:
        raise DW.WatchError(f"schtasks could not register '{name}': {out.strip()[:300]}")
    return name


def remove(r: Path, *, run: Callable[[list[str]], tuple[int, str]]) -> str:
    name = task_name(r)
    code, out = run(["schtasks", "/delete", "/tn", name, "/f"])
    if code != 0:
        raise DW.WatchError(f"schtasks could not delete '{name}': {out.strip()[:300]}")
    return name


def run_command(argv: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as ex:
        return 1, str(ex)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def notify(message: str) -> None:
    """A Windows balloon; elsewhere nothing (the session-start hook still shows the result)."""
    if os.name != "nt":
        return
    try:
        subprocess.Popen(["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", NOTIFY_PS],
                         env=dict(os.environ, PLS_DRIFT_MESSAGE=message[:250]), creationflags=0x08000000,  # no window
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass


def start_background(r: Path) -> None:
    """Start `drift-watch run --quiet` detached from the session (it outlives the hook)."""
    launcher = r / "pls.py"
    argv = [interpreter(), str(launcher), "drift-watch", "run", "--quiet"]
    flags = 0x00000008 | 0x00000200 | 0x08000000 if os.name == "nt" else 0   # detached, new group, no window
    subprocess.Popen(argv, cwd=str(r), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=flags, start_new_session=os.name != "nt", close_fds=True)


def _age(checked_at: str, now: datetime):
    try:
        return now - datetime.fromisoformat(checked_at)
    except (TypeError, ValueError):
        return None


def session_notes(r: Path, targets: dict, *, start: Callable[[Path], None] = start_background,
                  now: datetime | None = None) -> list[str]:
    """Lines for the session-start hook. Silent for a project with nothing in scope on this machine."""
    if not targets:
        return []
    now = now or datetime.now().astimezone()
    last = DW.load(r)
    age = _age(last.get("checked_at"), now) if last else None
    notes = []
    if last:
        found = DW.problems(last)
        when = f"{last.get('checked_at')}" + (f", {int(age.total_seconds() // 3600)} h ago" if age is not None else "")
        notes.append(f"drift check ({when}): " + ("every site matches its last release" if not found else
                     f"{len(found)} item(s) — `python pls.py drift-watch show` prints the report and the two ways on"))
        notes += [f"  {x}" for x in found[:10]]
    if (age is None or age >= DW.STALE_AFTER) and not DW.running(r, now) and (r / "pls.py").exists():
        try:
            start(r)
            notes.append("drift check started in the background; its result shows at the next session start "
                         "(or `python pls.py drift-watch show`)")
        except OSError:
            pass
    return notes
