# Plan — AU6: `pls usage collect` finds a session started in another folder

- **Task (Nam, 2026-11-11):** Step 4d first; AU6 first (small).
- **Tier:** Standard (pls code, run-log schema field added). Independent review.
- **Change:** run-log events carry `session` = env `CLAUDE_CODE_SESSION_ID` (observed in Claude Code 2.1.322, the transcript file name); `usage collect` also reads the transcripts of sessions named in the run log that live under another folder of the Claude Code config, counting only requests between that session's first step and its last event in this project.

## Acceptance criteria
1. Every run-log event has the field `session` (null outside Claude Code); the schema test lists it.
2. A session started in another folder is collected without `--transcripts`; requests before its first step here and after its last event here are not counted.
3. A session whose transcript is in the project's own folder is counted as before (whole).
4. No transcripts anywhere → a clear refusal (tested).
5. Only numbers are written (no conversation text); a session id is used as a file name only if it is `[A-Za-z0-9-]+`.
6. New tests fail on the parent commit; suites green on 3.12 and 3.10; node green.
