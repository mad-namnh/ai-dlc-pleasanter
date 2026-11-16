"""Claude Code hooks of a project repository (ADR-0029 C1): rules applied by the machine, not remembered by the model.

`pls init` writes them into `<project>/.claude/settings.json`; `pls hook install` adds them to an existing one. Each
hook runs `python "$CLAUDE_PROJECT_DIR/pls.py" hook <pre|post|stop>` with the event's JSON on stdin (contract read in
the Claude Code documentation, code.claude.com/docs/en/hooks, 2026-11-16 — see the plan folder of ADR-0029):

- pre (PreToolUse, Read|Edit|Write|NotebookEdit|MultiEdit|Bash): denies a file edit under the paths only `pls` writes
  (`releases/`, `gates/`, `ops/log/`, `.pls/`), an edit of the hooks' own settings (`.claude/settings*.json`) and of
  the launcher `pls.py`, and a Read under `.pls/` (agents never read keys, CLAUDE.md); for a Bash command that runs
  `pls` with `--yes` (or an abbreviation argparse accepts: `--y`, `--ye`) it answers `"ask"`, so Claude Code asks the
  person, who allows it only when they told the agent to use `--yes` for that target (CLAUDE.md Mandatory 1);
- post (PostToolUse, Edit|Write): after an edit under `config/<site>/`, runs `pls lint` and returns the issues of that
  site next to the tool result (`decision: "block"` + `reason`; the edit itself stays);
- stop (Stop): runs `pls check p1` and `p2` and shows the findings to the person (`systemMessage`); it never keeps the
  agent going (advisory, ADR-0029; the gates decide).

A hook that cannot decide (unreadable input, an error inside pls, the launcher missing, python not found, the
variable not set) allows and stays silent — it fails open: the command ends in `|| true`, so it never exits 2, which
would block every tool call or keep a Stop going. These are guardrails inside Claude Code; writes to Pleasanter, gates
and secrets are enforced by `pls` itself (agent-rules, ADR-0014). Limits: the command needs bash (Git Bash on
Windows); a shell command can still write the protected paths (Bash is matched only for `pls … --yes`, by its text);
a person's own `!` command is not seen by these hooks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PLS_ONLY = ("releases/", "gates/", "ops/log/", ".pls/")
SELF = (".claude/settings.json", ".claude/settings.local.json", "pls.py")      # the hooks and their launcher
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit", "MultiEdit")
RUNS_PLS = re.compile(r"(?:^|[\s;&|(/\\])(?:pls\.py|pls)(?=$|[\s\"'])")
YES = re.compile(r"""(?:^|\s)["']?--y(?:e|es)?["']?(?=$|[\s;&|)])""")
HOOK_CMD = 'python "${CLAUDE_PROJECT_DIR}/pls.py" hook '

SETTINGS = {
    "PreToolUse": [{"matcher": "Read|Edit|Write|NotebookEdit|MultiEdit|Bash",
                    "hooks": [{"type": "command", "command": HOOK_CMD + "pre || true", "timeout": 30}]}],
    "PostToolUse": [{"matcher": "Edit|Write|MultiEdit",
                     "hooks": [{"type": "command", "command": HOOK_CMD + "post || true", "timeout": 120}]}],
    "Stop": [{"hooks": [{"type": "command", "command": HOOK_CMD + "stop || true", "timeout": 120}]}],
}


def _rel(root: Path, file_path: str) -> str | None:
    try:
        return Path(file_path).resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def pre(root: Path, event: dict) -> dict | None:
    tool, inp = event.get("tool_name"), event.get("tool_input") or {}
    if tool in EDIT_TOOLS or tool == "Read":
        rel = _rel(root, str(inp.get("file_path") or inp.get("notebook_path") or ""))
        rel = rel.casefold() if rel else rel     # Windows and macOS file systems ignore case: so does the guard
        if rel and tool == "Read" and (rel == ".pls" or rel.startswith(".pls/")):
            return _answer("deny", ".pls/ holds keys and connections: agents never read it (CLAUDE.md, Mandatory 1)")
        if rel and tool != "Read" and any(rel == p.rstrip("/") or rel.startswith(p) for p in PLS_ONLY):
            return _answer("deny", f"{rel} is written only by pls (releases, gate records, run log, local keys): run "
                           "the pls command that owns it instead (ADR-0029)")
        if rel and tool != "Read" and rel in SELF:
            return _answer("deny", f"{rel} carries this project's hooks or their launcher: the person changes it "
                           "(pls hook install, pls init), not the agent (ADR-0029)")
    if tool == "Bash":
        cmd = str(inp.get("command") or "")
        if RUNS_PLS.search(cmd) and YES.search(cmd):
            if event.get("permission_mode") in ("bypassPermissions", "dontAsk"):   # nobody would be asked
                return _answer("deny", "pls with --yes while permissions are bypassed: nobody can confirm it — ask the "
                               "person to run it themselves (CLAUDE.md, Mandatory 1)")
            return _answer("ask","pls with --yes skips its typed confirmation: allow only if you told the agent to "
                           "use --yes for this target (CLAUDE.md, Mandatory 1); otherwise deny and run it yourself")
    return None


def _answer(decision: str, reason: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                   "permissionDecisionReason": reason}}


def edited_site(root: Path, event: dict) -> str | None:
    """The config site an edit touched (config/<site>/…, scripts included), else None."""
    rel = _rel(root, str((event.get("tool_input") or {}).get("file_path") or ""))
    if not rel:
        return None
    m = re.match(r"^config/([^/]+)/", rel)
    return m.group(1) if m else None


def post(issues: list[dict], site: str) -> dict | None:
    mine = [i for i in issues if i.get("site") in (site, "_tenant")]
    if not mine:
        return None
    lines = [f"{i['rule']}  {i['site']}  {i['msg']}" for i in mine[:20]]
    more = f"\n… {len(mine) - 20} more (pls lint)" if len(mine) > 20 else ""
    return {"decision": "block", "reason": f"pls lint after this edit ({len(mine)} issue(s)):\n" + "\n".join(lines) + more}


def stop(event: dict, findings: list[dict]) -> dict | None:
    if event.get("stop_hook_active") or not findings:
        return None
    by_phase: dict[str, int] = {}
    for x in findings:
        by_phase[x["phase"]] = by_phase.get(x["phase"], 0) + 1
    counts = ", ".join(f"{p} {n}" for p, n in sorted(by_phase.items()))
    return {"systemMessage": f"pls check: {counts} finding(s) — run `pls check p1` / `pls check p2` before G1 / G2 "
                             "(the gates refuse on findings)"}


def install(settings_file: Path) -> list[str]:
    """Add the hooks of this module to a settings file; returns the events added. Existing entries are kept; an event
    that already runs `pls.py" hook` is left as it is."""
    try:
        data = json.loads(settings_file.read_text(encoding="utf-8-sig")) if settings_file.exists() else {}
    except ValueError as ex:
        raise ValueError(f"{settings_file}: not readable JSON ({ex}) — fix it, then run pls hook install again")
    if not isinstance(data, dict) or not isinstance(data.get("hooks", {}), dict):
        raise ValueError(f"{settings_file}: not a JSON object with an object `hooks` — fix it, then run pls hook install")
    hooks = data.setdefault("hooks", {})
    added = []
    for event, groups in SETTINGS.items():
        have = hooks.setdefault(event, [])
        if not isinstance(have, list):
            raise ValueError(f"{settings_file}: hooks.{event} is not a list")
        if any("pls.py\" hook" in str(h.get("command", "")) for g in have if isinstance(g, dict)
               for h in (g.get("hooks") or []) if isinstance(h, dict)):
            continue
        have.extend(json.loads(json.dumps(groups)))
        added.append(event)
    if added:                                        # nothing to add: the person's file is left as it is
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return added
