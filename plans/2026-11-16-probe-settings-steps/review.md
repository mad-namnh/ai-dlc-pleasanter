# Review — ADR-0027 build

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes; F1 High
- **F1 High:** a disabled notification could name any non-mail target (an HttpClient URL to any host; bare names) → recipient fields hold only `…@example.invalid` or [Owner] / [Manager] / [Creator] / [Updator]; no field of an item holds a URL; tests (Type 9 URL, bare token, body URL; a webhook type with an empty target is accepted for its shape).
- **F2 Medium:** key checks case-sensitive → `_mail_parts`, `notice_problems`, `KG._has_notices` compare without case; keys equal under case folding refused; tests.
- **F3 Medium:** `settings_partial` body sent as written, JSON strings not read → body only `{"SiteSettings": {…}}`; strings holding JSON are read as content by the script / notice check; tests.
- **F4 Medium:** literal principal placeholders → refused with F1 (`[Group n]`, `[User n]`, `[Dept n]`); tests.
- **F5 Low:** unknown `${probe_site:…}` in a step not refused by the file check → steps scanned; test.
- **F6 Low:** a refused own-site proof reported `fail` → a spec `error` makes the probe `error` (not evidence, I9); test.
- **F7 Low:** TD-45 now names settings steps too.
- **F8 Low:** adr README "enforced by tool", architecture kb-verify row, kb-gaps.md probe-format row, ADR-0026 line, KG message updated. The Status-line edit ("built 2026-11-16") is reported to Nam (agent-rules stop point 1 lists Status changes; the decision is unchanged).
- **F9 Low:** "must be a list of objects" untested → test.

## Round 2 (same reviewer) — accept with fixes; no Critical/High
- R2-1 Medium: credential fields read by exact case → item keys mapped to Pleasanter's spelling (Token, Headers, Type, ReminderType, Address, To, Disabled) before `secret_fields`; tests (lower-case kind, `token`, `headers`).
- R2-2 Low: numeric recipient → checked as text; test.
- R2-3 Low: error mapping broader than documented → ADR-0027 As built and ADR-0009 note state it (any spec `error` → probe `error`).
- R2-4 Low (information): invented recipient field names and double-encoded JSON → ADR-0027 open question (source read).
