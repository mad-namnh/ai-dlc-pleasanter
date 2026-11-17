# Plan — ADR-0030: baseline allow-list without docs/, weakest model (item 5)

Task (Nam, 2026-11-18): "5. mo hinh yeu nhat cua claude di"; answers: "Haiku 5.5 (Recommended)", "Bỏ docs/ (Recommended)".
Tier: Critical (ADR text) → independent review on opus, effort high.

## Acceptance criteria
1. ADR-0030: baseline allow-list without `docs/` (Decision part 2), "what both arms share" corrected, open question on the weakest model closed with Nam's words and the earlier analysis (option D not recommended) noted, Part 5 step 4 names Haiku 5.5, Status says amended.
2. `evals/README.md` allow-list and step 4 match; `docs/adr/README.md` row 0030 says amended.
3. The brief form (protected) as `proposed-eval-case-brief-baseline-no-docs.patch`, `git apply --check` clean.
4. No other file names `docs/` in a baseline allow-list (grep).
5. Both suites green on HEAD + this change.
