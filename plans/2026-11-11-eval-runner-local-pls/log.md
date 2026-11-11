# Log
- claude-code-guide (docs sub-agents.md, permissions.md): tools field = bare names; settings deny applies to subagents but is not a security boundary; hard allowlist = PreToolUse hook (TD-21). Chose relay instead of Bash.
- patch generated from HEAD blobs; git apply --check OK.
- local-only list verified: HTTP imports only in adopt_package, sandbox_refresh, setup_profile, _client/http_cmd, principals (pls.py:1534,1986,2329,2429,2459,3275); lint/xref/canon/pack/coverage/refs/skills check are file commands.
- review round 1 (1 High F1 etc.) and round 2 (N1–N3) fixed; review.md saved.
