# Plan — multiple selection changes are data-impacting (settings coverage WS2.3)

- **Date / branch / parent commit:** 2026-11-16 / `brownfield-adr` / `5554586`
- **Objective:** `classify` puts a `Columns[x].MultipleSelections` change in the data-impacting class; `ChoicesControlType` stays config-only.
- **Tier:** Critical (change classification, ADR-0004 gates).
- **Source (Pleasanter_1.5.2.0, read-only):** `Libraries/Extensions/ToExportExtensions.cs` l.23–39 (multi-select value deserialised as `List<string>`, empty → `[]`), `ToDisplayExtensions.cs` l.35–45, `MatchExtensions.cs` l.151; `ChoicesControlType` only in `HtmlFields.cs` l.236, 1039–1081 (rendering) and site-setting plumbing.
- **Plan said:** data-impacting with "not verified" until WS3b; the source settles the storage form well enough to keep it data-impacting and to leave `ChoicesControlType` config-only.
- **Stop points:** none — ADR-0004 gets an "As built" Consequences line, as for WS2.1 / 2.2 (Decision text unchanged).
- **Acceptance criteria:**
  1. Added / changed / removed `MultipleSelections` → data-impacting with a migration note naming the JSON-array form.
  2. `ChoicesControlType` change → config-only; a new column with `MultipleSelections` → config-only.
  3. New test fails on the parent; suites green (3.12, 3.10, node).
  4. Review: no open Critical / High.
- **Subagents:** `pls-x-reviewer` (opus, high).
- **Documents:** ADR-0004 as-built line; HANDOFF line.
