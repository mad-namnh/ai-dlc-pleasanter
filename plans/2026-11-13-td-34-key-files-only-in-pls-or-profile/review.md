# Review — TD-34 key files only in .pls/ or the profile folder (Critical)

## Round 1 — accept with fixes (0 Critical, 0 High, 2 Medium, 4 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `ff5d27a`; `git status` and a hash of the diff equal before and after.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | ADR-0021 As-built, env table, Status line, Decision sentence and the ADR index still said the limit was open | As-built, env table, Consequences and index fixed; Status line and Decision sentence are stop point 1 → wording proposed to Nam in `proposed-adr-0021-status-and-decision-wording.md` |
| F2 | Medium | With `PLS_CONNECTIONS` the allowed folder became that file's folder (wider than option B; e.g. a shared folder) | Fixed as option B says: the project's `.pls/` (`_pls_home` from `load_connection`) and the profile folder, whatever `PLS_CONNECTIONS` names; test with a connection file elsewhere |
| F3 | Low | `docs/setup.md` rows for `PLS_CONNECTIONS` / `PLS_PROFILE_DIR` | Fixed |
| F4 | Low | `resolve_key` docstring stale | Fixed |
| F5 | Low | `file:`, `file:.`, a NUL byte → raw exceptions | Fixed: resolve and read wrapped, `is_file()`; tests (malformed, unreadable) |
| F6 | Info | `resolve()` touches a UNC path before the refusal (not new) | Noted, no change |

## Round 2 (final) — accept with fixes (0 Critical, 0 High, 0 Medium, 4 Low)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| R2-1 | Low | `PLS_PROFILE_DIR` set to a drive root or `.` switches the limit off; TB-11 read as unbypassable | TB-11 "Not covered" clause added (operator's environment, TB-9) |
| R2-2 | Low | plan.md still described the round-1 design | Fixed ("changed after review round 1") |
| R2-3 | Low | Test module docstring stale | Fixed |
| R2-4 | Info | ADR-0021 Status / Decision still say open (stop point, wording proposed); HANDOFF | Left for Nam (proposal file); HANDOFF updated at the end of this batch |

Round-1 fixes confirmed by the reviewer.
