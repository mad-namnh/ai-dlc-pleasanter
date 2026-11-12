# Review — P3-5 parts 2 and 3

- **Reviewer:** `pls-x-reviewer`, model `sonnet`, effort `medium`; round 1 of 2; working tree against `015a5a9`.
- **Verdict:** accept with fixes — 0 Critical, 0 High, 2 Medium, 3 Low. No behaviour defect; Python 468 OK, node 15 pass.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | The `gate` warning had no test | Fixed: the edited-copy test also runs `pls gate G3`: exit 0, WARNING, gate recorded |
| M2 | Medium | "A check that cannot run never blocks" untested | Fixed: `test_a_skills_check_that_cannot_run_never_blocks_step_or_gate` (no lock; `skills_check` raising) |
| L3 | Low | "step event does not carry `skills_edited`" undocumented | Docstring of `edited_skill_warning` says it |
| L4 | Low | A usage row without `first` sorted as earliest | Fixed: rows without a time are skipped; test case added |
| L5 | Low | Unknown version → "same version" wording | No change: never says older/newer (criterion 2) |
| — | style | Review label "I3" in a code comment | Removed (comments state the reason, not the origin) |
