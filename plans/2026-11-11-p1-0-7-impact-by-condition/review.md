# Review — P1 0.7 skill text (round 1)

- **Reviewer:** `pls-x-reviewer`, claude-sonnet-5-5, effort medium; working tree against `7eb41d7`. Changed nothing (git status before/after: the two skill files and the plan folder only).
- **Verdict:** accept with fixes.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | Medium | Step 2 asserted "a reminder has a `Condition` field — read it against the site's view ids"; the KB has no reminder-condition entry (criterion 2, CLAUDE.md rule 5) | Fixed: "a reminder may carry a condition too — its field and meaning are not in the KB, so read the exported `site.json`, compare it with the site's views, and record what you find as unverified". The probe stays an open question of the plan |
| 2 | Low | README row repeated the claim ("condition view" for reminders) | Fixed: the row says a reminder's condition is read from the exported settings, not in the KB, recorded as unverified |

- Reviewer could not read the suite summaries (its filter dropped them); the Orchestrator ran both suites before commit (log).
- **Consequence for the eval:** the case 001 run started on the pre-fix text was stopped (finding 1 touches the item under test) and restarted on the final text.
