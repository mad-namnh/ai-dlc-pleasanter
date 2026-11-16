# Review — ADR-0029 Part A

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes
- **F1 Medium:** LK-LOOKUP-SCREEN / LK-FORMULA-OVER-LOOKUP restated uncommitted D40 (C) text (screen save after every deploy; 自動ポストバック on operands) → texts now restate only the committed D40 / D41a rows; the (C) observations reach the designer when TD-51's KB rows are committed (staleness test).
- **F2 Medium:** the worktree base (904927f) had the old D47 advice under a rule that already said "set on the screen" → work moved onto 09de5d2 (worktree wt-r2) and regenerated from the committed KB only.
- **F3 Medium:** design conditions in Python instead of `probes/index.json` (option text) → stated as a deviation with its reason in ADR-0029 "As built" and in the module docstring.
- **F4 Low:** unmarked behaviour in CL-DEFAULT-INPUT, CL-LOOKUP-CHANGED, CL-FORMULAS, LK-LOOKUP-SCREEN → "not known / no KB row, not verified", "source-derived, not verified", the imports-and-migrations caveat restored.
- **F5 Low:** stdout mode failed on cp932 → `sys.stdout.reconfigure(encoding="utf-8")`.
- **F6 Low:** a branch skipping `hit()` unnoticed → sample test asserts one rule per message.
- **F7 Low:** new site's first release kept data rule ids → rules carry their class; `first_release_of_new_site` drops data rules with data items; test.
- **F8 Low:** ADR header "not built yet" → "Part A built"; SE-SCOPE trigger widened to any settings change.

## Round 2 (same reviewer) — accept with fixes, Low only
- R2-1: the one-rule-per-message check runs on samples only → test also refuses a direct `data/perm/cfg.append(` in classify.
- R2-2: LK-LOOKUP-SCREEN said imports are not covered; D40 covers imports → "API clients and imports write the value (D40; migrations: not covered…)".
- R2-3: round-2 fixes were unstaged → staged before the commit; staleness test run on the committed tree.

## Part B, round 1 (pls-x-reviewer, opus, high) — accept with fixes; F1 High
- **F1 High:** an `--item` with no document (missing, misnamed, unknown id; a DES outside `decisions/`) was approved unread → `PC.for_gate`: a finding for every item without a document and for every misnamed REQ / DES file; tests.
- **F2 Medium:** "every in-scope REQ has an element" not checked → each REQ in `reqs` must be named by an element; test.
- **F3 Medium:** coverage findings could not block G2 (item = REQ id) → G2 also refuses on G1-approved REQs without a DES (Nam's decision "Blocking" applied as written); test.
- **F4 Low:** weak sources → under `requirements/sources/` only; `derived from` another existing REQ; `P2 accepted` / `drift accepted` exact; tests.
- **F5 Low:** broken gate record gave a traceback → `Fail`; test.
- **F6 Low:** P1 / P2 skill text now say never to write the approver's reason.
- **F7 Low:** EARS keyword per type; question ids matched as table cells; `acceptance` must be an int; `--accept-findings` refused on G3 / G4; template `acceptance: 3`; architecture §4 names the coupling. Not changed: `--accept-findings` accepts all findings of the items (all recorded in the gate record).
- **EV-02:** judged not a relaxation by the reviewer.

## Part B, round 2 (same reviewer) — accept with fixes; no Critical/High
- R2-1 Medium: as-is records (DES-000-as-is-<site>.md) read as designs → left out of p2 (they are reviewed through `pls review as-is`); test.
- R2-2 Low: a G1-approved REQ whose file is gone escaped G2 coverage → candidates are files ∪ G1-approved items; test.
- R2-3 Low: misnamed-file rule matched any REQ… / DES… name → only `REQ-` / `DES-` prefixes; test.
