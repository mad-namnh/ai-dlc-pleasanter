# Review — adr-0030-build

## Step 1 (test) — round 1 (pls-x-reviewer, sonnet, medium, 2026-11-17)

**Accept**; 0 Critical / 0 High / 0 Medium / 2 Low. `git status` unchanged by the review.

| Finding | Severity | Disposition |
|---|---|---|
| Low-1: any `.md` under `skills/` with both `## Must` and `## Must not` headings counts as a rubric; a future skill file with those headings would fail | Low | Intended: that pair is the rubric shape; the message names the file. No change |
| Low-2: `interviewee.md` and `eval.md` go beyond the names Part 6 lists | Low | Intended: both are case data. No change |

Reviewer's full Python run in the shared tree: 1 failure, `test_impact_rules` (other work's uncommitted KB edit), not this change; Orchestrator's run on `a854dec` + the test: 719 OK (log.md).

## Step 2 (eval contract) — round 1 (pls-x-reviewer, opus, high, 2026-11-17)

**Accept with fixes**; 0 Critical / 0 High / 2 Medium / 3 Low. `git status` unchanged by the review.

| Finding | Severity | Disposition |
|---|---|---|
| F1: README puts the new run rules in force while `docs/agent-rules.md` §3/§4, the orchestrator skill step 9 ("one runner per case") and the runner definition ("read the skill under test") still say otherwise | Medium | Fixed: README says which files carry the rules only after Nam applies the step-3 patches; until then only with-skill runs (extra exclusions added to the brief by hand), baseline and selection runs wait. Orchestrator `SKILL.md` step 9 added to the step-3 patch list (plan.md) |
| F2: a with-skill or selection run that opens a forbidden path is not voided (ADR-0030 Part 1 "applies to every run", Part 3 "voids the run") | Medium | Fixed: void in either arm; selection "any other path voids the run"; template column "Forbidden or not-allowed paths opened" |
| F3: selection batches not marked as asked of Nam (ADR-0029 amendment) | Low | Fixed in README selection bullet and HANDOFF line |
| F4: scratch folder name `<case>-<arm>-r<n>` reveals arm / run number and collides across skills | Low | Fixed: neutral `<run-id>`, unique across skills; mapping in the result file |
| F5: HANDOFF drops "no negative scope case"; "once per arm" ambiguous; template lacks the separation statement | Low | Fixed (all three) |
| Observation: the baseline allow-list includes all of `docs/`; `docs/plan.md` and `docs/slices/*` describe skill procedures and eval outcomes, weakening the arm separation | — | ADR-0030's own decision (Part 2), not changed here; reported to Nam as a candidate open question (an Accepted ADR is changed only through a new ADR) |

No round 2: the fixes are text within the reviewed scope; F1's patch side is reviewed in step 3.
