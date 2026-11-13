# Proposed wording for Nam — ADR-0021 Status line and Decision sentence (stop point 1: only Nam edits them)

TD-34 is built (2026-11-13). Two sentences of ADR-0021 still say it is open:

1. Status line, now: `Accepted (2026-11-12, Nam) — option B; the opt-in part is built (roadmap P3-7), the `file:` limit is open`
   Proposed: `Accepted (2026-11-12, Nam) — option B; built: the opt-in (roadmap P3-7, 2026-11-12) and the `file:` limit (TD-34, 2026-11-13)`

2. Decision section, now: `**Not built yet:** the limit of `file:` key paths to `.pls/` and the profile folder (TD line).`
   Proposed: `**Built 2026-11-13 (TD-34):** `file:` key paths are read only inside the project's `.pls/` or the profile folder (a connection file named by `PLS_CONNECTIONS` does not widen this).`

The As-built section, the environment table and the Consequences line were updated in the same commit (not Decision or Status).
