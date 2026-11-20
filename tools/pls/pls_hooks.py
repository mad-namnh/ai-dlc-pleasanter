"""Claude Code hooks of a project repository (ADR-0029 C1): rules applied by the machine, not remembered by the model.

`pls init` writes them into `<project>/.claude/settings.json`; `pls hook install` adds them to an existing one. Each
hook runs `python "$CLAUDE_PROJECT_DIR/pls.py" hook <pre|post|stop|start|model>` with the event's JSON on stdin (contract read in
the Claude Code documentation, code.claude.com/docs/en/hooks, 2026-11-16 — see the plan folder of ADR-0029):

- pre (PreToolUse, Read|Edit|Write|NotebookEdit|MultiEdit|Bash): denies a file edit under the paths only `pls` writes
  (`releases/`, `gates/`, `ops/log/`, `.pls/`), an edit of the hooks' own settings (`.claude/settings*.json`) and of
  the launcher `pls.py`, and a Read under `.pls/` (agents never read keys, CLAUDE.md); for a Bash command that runs
  `pls` with `--yes` (or an abbreviation argparse accepts: `--y`, `--ye`) it answers `"ask"`, so Claude Code asks the
  person, who allows it only when they told the agent to use `--yes` for that target (CLAUDE.md Mandatory 1);
- post (PostToolUse, Edit|Write): after an edit under `config/<site>/`, runs `pls lint` and returns the issues of that
  site next to the tool result (`decision: "block"` + `reason`; the edit itself stays);
- stop (Stop): runs `pls check p1` and `p2` and shows the findings to the person (`systemMessage`); it never keeps the
  agent going (advisory, ADR-0029; the gates decide);
- model (PreModelSwitch): denies a switch to a model other than the project's `model` setting (ADR-0031; contract read
  in the Claude Code documentation, code.claude.com/docs/en/hooks, 2026-11-18: `to_model` is the target model ID, a
  `permissionDecision: "deny"` cancels the switch and its reason is shown to the person; a timeout blocks the switch;
  automatic fallbacks and a session resume do not fire it);
- start (SessionStart, startup|resume): prints, as plain text that Claude Code adds to the session's context, when the
  framework running is not the version the project pinned or a newer release tag exists (ADR-0022; contract read in
  the Claude Code documentation, code.claude.com/docs/en/hooks, 2026-11-18). Advisory: writes outside dev are refused
  by `pls` itself.

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
    "SessionStart": [{"matcher": "startup|resume",
                      "hooks": [{"type": "command", "command": HOOK_CMD + "start || true", "timeout": 60}]}],
    "PreModelSwitch": [{"hooks": [{"type": "command", "command": HOOK_CMD + "model || true", "timeout": 30}]}],
}
DEFAULT_MODEL = "opus"          # every phase of a project runs on the model its skills were evaluated on (ADR-0031)


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


def project_model(root: Path) -> str | None:
    """The model the project's committed settings name (`.claude/settings.json` → `model`), or None."""
    try:
        data = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    m = data.get("model") if isinstance(data, dict) else None
    return m.strip() if isinstance(m, str) and m.strip() else None


FAMILIES = ("opus", "sonnet", "haiku", "fable")       # aliases the check understands (ADR-0031)
_SUFFIX = re.compile(r"\[[^\]]*\]$")                   # a context-window suffix such as [1m]
_MODEL_ID = re.compile(r"claude-[a-z]+(?:-[0-9]+)+")


def _same_model(configured: str, to_model: str) -> bool | None:
    """Whether `to_model` is the configured model: a family alias (`opus`, also `opus[1m]`) matches every model ID of
    that family; a model ID (`claude-opus-5-5`, also with `[1m]` or a date suffix) matches only itself. None when the
    setting has another form (e.g. `opusplan`, a gateway name): the check does not apply, it never locks a project."""
    c, t = _SUFFIX.sub("", configured.strip().casefold()), _SUFFIX.sub("", to_model.strip().casefold())
    if c in FAMILIES:
        return re.search(rf"(^|[-_.]){re.escape(c)}([-_.]|$)", t) is not None
    if _MODEL_ID.fullmatch(c):
        return t == c or re.fullmatch(rf"{re.escape(c)}-\d{{8}}", t) is not None
    return None


def model_switch(root: Path, event: dict) -> dict | None:
    """PreModelSwitch (ADR-0031): a switch to a model other than the project's is denied — the model is the project's
    decision, made by a commit to `.claude/settings.json`, not the developer's. Nothing configured, or an event
    without a target model: no answer (the switch goes ahead)."""
    configured, to_model = project_model(root), event.get("to_model")
    if not configured or not isinstance(to_model, str) or not to_model.strip():
        return None
    if _same_model(configured, to_model) is not False:          # the same model, or a setting the check cannot read
        return None
    return {"hookSpecificOutput": {"hookEventName": "PreModelSwitch", "permissionDecision": "deny",
                                   "permissionDecisionReason":
                                       f"This project runs every phase on '{configured}' (.claude/settings.json `model`; "
                                       f"its skills are evaluated on it, ADR-0031). '{to_model}' is not used here; the "
                                       "model is changed by a commit to the project settings, decided by the G4 owner."}}


def install(settings_file: Path) -> list[str]:
    """Add or update the hooks of this module in a settings file, and the project's model when it names none; returns
    the events written (and "model" when the model was set). Entries of other hooks
    are kept as they are; this module's own entries (a command that runs `pls.py" hook`) are replaced by the current
    ones when they differ, so a later change of the hook command reaches projects that already have hooks."""
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
        def own(h) -> bool:
            return isinstance(h, dict) and "pls.py\" hook" in str(h.get("command", ""))
        kept = []                                    # every group without this module's hooks; a mixed group keeps
        for g in have:                               # the person's hooks, an emptied group goes
            if isinstance(g, dict) and isinstance(g.get("hooks"), list) and any(own(h) for h in g["hooks"]):
                rest = [h for h in g["hooks"] if not own(h)]
                if rest:
                    kept.append(dict(g, hooks=rest))
            else:
                kept.append(g)
        new = kept + json.loads(json.dumps(groups))
        if new == have:
            continue                                 # already current
        have[:] = new
        added.append(event)
    m = data.get("model")
    if not (isinstance(m, str) and m.strip()):        # the project's model; a value the person set is kept (ADR-0031)
        data["model"] = DEFAULT_MODEL
        added.append("model")
    if added:                                        # nothing to add: the person's file is left as it is
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return added
