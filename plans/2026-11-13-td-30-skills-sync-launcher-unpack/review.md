# Review — TD-30 skills sync/check, launcher message, unpack over uncommitted edits (Standard)

## Round 1 — accept with fixes (0 Critical, 0 High, 0 Medium, 4 Low)

Reviewer: `pls-x-reviewer`, model `sonnet`, effort `medium`; working tree against `6b1e889`; tree equal before and after (hash of `git diff`, the plan folder and the new test file). The reviewer confirmed the 3.12 suite (567 OK); 3.10, node and the parent check it left to the Orchestrator (log: 567 OK skipped=2, node 15, 9 new tests fail on `6b1e889`).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R1 | Low | an orphan skill folder is deleted by sync even when its project copy was edited; check does not say so | fixed: the `no longer in the framework` line adds "its project copy was edited: the sync deletes that edit too"; tested |
| R2 | Low | template changes are reported once (check before sync, and by sync), then forgotten; a lock without template hashes reports nothing until the first sync | no change: by design (acceptance 3), stated in setup.md and the architecture row |
| R3 | Low | removal does not guard against a symlink or junction under `.claude/skills` | fixed: `_remove_skill_dir` refuses a link, or anything resolving outside `.claude/skills`, before deleting anything (also for the re-install of a current skill); tested with a junction on Windows (symlink elsewhere) |
| R4 | Low | `HANDOFF.md` says "TD-30 committed" before the commit | no change: committed in the same commit as that text |

## Round 2 (last) — accept (0 Critical, 0 High, 0 Medium, 3 Low)

Reviewer: `pls-x-reviewer`, model `sonnet`, effort `medium`; tree equal before and after. R1, R3 fixed; R2, R4 dispositions reasonable. 3.12 suite 569 OK and node 15 run by the reviewer; full 3.10 and the parent check by the Orchestrator (569 OK skipped=2; 11 new tests fail on `6b1e889`: 8 FAIL, 3 ERROR).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L1 | Low | `unpack` cannot see edits to git-ignored files under `config/<site>`; a git failing inside a repository reads as "not a git repository" | recorded: TD-43 |
| L2 | Low | a person's own folder whose name the framework later takes is replaced by sync (behaviour from before this change) | recorded: TD-43 |
| L3 | Low | `skills check` exits 1 for as long as a foreign folder exists | no change: intended (reported, never removed); the lifecycle skill says to tell the person |
