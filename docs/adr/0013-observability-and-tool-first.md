# ADR-0013 — Observability (run log, token usage) and tool-first work

- **Status:** Proposed (2026-11-08)
- **Context owner:** Nam
- **Related:** I3 (deterministic tool), I4 (gates), ADR-0008 (HTTP transport); PLAY BOARD trial 2026-11-08

## Context

The PLAY BOARD trial (onboarding of an existing app with 23 sites, then one change request dev → stg on copies) showed:

1. **Where tokens go.** Claude Code transcripts of that day: the main session ~172 M tokens, 88 % of them cache reads of an ever-growing context; one as-is specification (1 site) ~4.4 M; each review or eval subagent 1.6–5.2 M. A change request itself (two lines, plan, two tests, report) was small. The cost sits in onboarding work done by the LLM that a tool can do, and in long sessions.
2. **Nobody could see what the framework did** except by reading the chat: which command ran, on which environment, what it refused, which step took how many tokens.
3. Nam plans a UI on top of the framework; it needs machine-readable state, not console text.

Decision by Nam (2026-11-08): what can be done by a tool is done by a tool, not by the LLM, without lowering quality; every step is logged and token use is monitored in one consistent way for the team.

## Decision

### Run log
Every `pls` command appends one JSON line (schema v1) to `ops/log/<YYYY-MM-DD>-<actor>.jsonl` in the project repository: time, run id, actor, branch, commit, command and its words, env, site, release, result (`ok` / `refused` / `error`), exit code, duration, whether it may write to Pleasanter, small metrics (issues, changes, tests passed, gate decision, …), first line of an error, and the Claude Code session that ran it (`session`, env `CLAUDE_CODE_SESSION_ID` as observed in Claude Code 2.1.322; null outside Claude Code; added 2026-11-11, AU6 — an added field, readers of schema v1 ignore unknown fields). Logging never breaks a command. One file per day and person keeps merges of parallel branches trivial. `pls step <phase> "<title>"` marks the start of a step (onboarding, P1–P6, G1–G4, other).

**When the run log cannot be written (decided by Nam, 2026-11-10; design review D6).** A command that may write to Pleasanter (`apply`, `bootstrap`, `migrate`, `test`, `kb-verify`) checks that today's log file can be appended to before it does anything else, and is refused when it cannot ("repair `ops/log/` and run it again"): a protected write always leaves a log line. A command that only reads still runs and prints a warning that it left no log line. If the log becomes unwritable while a writing command runs, the command finishes and prints the same warning; the release folder (`apply-log.json`, `plan.json`) still records what was written.

**What a writing command records (design review D4).** `apply`, `bootstrap`, `migrate` and `mark-applied` take their environment from the plan, so they put it into the event themselves (`env`, `release`), and `metrics.written` lists the site ids a write was sent to (touched sites of an apply, created sites of a bootstrap, the site of a migration). `writes` stays "may write".

### Token usage
`pls usage collect` reads the Claude Code transcripts of the project (numbers only — model, timestamp, input / cache write / cache read / output tokens; no conversation text), counts each model request once, and attributes it to the step open at that time. It writes `ops/usage/<session>.json` (idempotent, one file per session). A session opened in another folder (e.g. the framework repository) keeps its transcript under that folder: `collect` finds it through the run log's `session` (only ids of `[A-Za-z0-9-]+` are looked up) and counts only its requests from the first step it opened in this project to its last event logged here. Limits: one span per session, so work done elsewhere between two visits is counted; the last reply after the last command is missed; a session that never ran `pls step` here is not collected. A session whose transcript is in the project's own folder is counted whole. `pls usage report --by phase|step|agent|model [--json]` prints totals. Cost in money is not computed (prices change; a UI can apply its own table).

### Tool-first
Mechanical work moves from the LLM to `pls`:

| Was done by the LLM | Now |
|---|---|
| Adopting each site, naming, ordering, re-mapping | `pls adopt-package --env <e> --package <pkg> [--names <file>]` (names stay the person's decision) |
| Reading 200–450 lines of lint / refs output | `pls lint --summary`, `pls refs --summary` (POSSIBLE numbers grouped; only the group "other" listed) |
| Writing every table of an as-is 画面設計書 | `pls spec-skeleton --site <s>`; the LLM writes only the marked overview, script summaries and questions |
| Technical part of the release report | `release-plan` writes `diff-report.operator.md`; the LLM writes only the Japanese summary |

Working rules in the skills: as-is specifications only for sites a change request touches; one Claude Code session per change request (state is in the repository); gates of one release asked together; smaller models only for mechanical filling that a tool verifies afterwards.

## Consequences

- The team (and a future UI) reads `ops/log/`, `ops/usage/`, `gates/`, `releases/*/plan.json` instead of chat history.
- Quality checks are not reduced: gates, drift, round trip, independent review of framework changes stay.
- Token usage depends on the transcript format of Claude Code; `pls usage` reads only documented-by-observation fields (`requestId`, `timestamp`, `message.model`, `message.usage`) and ignores everything else. If the format changes, `collect` reports 0 sessions rather than wrong numbers.
- Logs and usage files are committed with the phase commits; they contain no secrets and no business data.
