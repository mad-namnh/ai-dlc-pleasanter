# Hook contract notes (C0) — read 2026-11-16/17

Source: Claude Code documentation, https://code.claude.com/docs/en/hooks (docs.claude.com/en/docs/claude-code/hooks redirects there).

- Configuration: `.claude/settings.json` → `hooks` → event → `[{"matcher": "...", "hooks": [{"type": "command", "command": "...", "timeout": N}]}]`. A matcher of letters, digits, `_`, `|` is an exact name or a list (`Edit|Write`); `Stop` has no matcher.
- Input on stdin: common fields `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`; tool events add `tool_name`, `tool_input` (Edit / Write: `file_path`, always absolute; Bash: `command`), `tool_use_id`. Stop adds `stop_hook_active`, `last_assistant_message`.
- PreToolUse: exit 2 blocks (stderr is the reason); or exit 0 with `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}`. Exit 0 without output = no decision. A timeout does not block unless `"onFailure": "block"`.
- PostToolUse: the tool already ran; `{"decision": "block", "reason": "..."}` adds the reason next to the tool result; `hookSpecificOutput.additionalContext` also exists.
- Stop: exit 2 or `decision: "block"` keeps the turn going; `stop_hook_active` is true when already continuing because of a stop hook (8-continuation cap). `systemMessage` (common field) is shown to the user without continuing — used here, so the stop hook is advisory.
- `CLAUDE_PROJECT_DIR`: the project root where the session started, exported to hook processes. Default command timeout 600 s.
- Windows: commands run in Git Bash when installed, else PowerShell (`shell` field); in exec form `command` must be a real executable.
