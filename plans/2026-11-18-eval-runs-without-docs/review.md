# Review

## Round 1 — pls-x-reviewer, opus, effort high (Critical: ADR, runner definition)
Verdict: accept with fixes; no Critical / High. git status before / after: unchanged.

| # | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | Open question 1 (does the harness load `CLAUDE.md`?) contradicted the amendment | Closed with the evidence of the 2026-11-18 sweep (every runner reported it in context); definition keeps a fallback (read it if missing, except in selection). |
| F2 | Medium | Void rule for opening `docs/` only in the brief | Added to `evals/README.md` (both-arms never-open list) and ADR Part 2 ("a run in either arm that opened a path under `docs/` is void"). |
| F3 | Medium | Selection runs also get the framework `CLAUDE.md`; not recorded | Known limit added to ADR Part 3 and the README selection line. |
| F4 | Low | Hand-back report vs final report unclear; refusals; opened files across resumes | Definition: hand-back report ends with the pending `COMMAND TO RUN:` block (named as the one exception in the brief); resume with outputs and refusal lines; final list covers the whole run; README step 6 and brief note: check every report's list. |
| F5 | Low | Stale or inexact statements | ADR names the pending patch (Status, Part 2); "brief and runner definition"; boundary dated by the commit that applies the patch; `docs/adr/README.md` row; README "all 8 runs … asked for a command" with the result file; redundant `docs/review-criteria.md` dropped from the definition's list. |
