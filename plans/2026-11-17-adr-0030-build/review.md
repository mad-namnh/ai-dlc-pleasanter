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

## Step 3 (patches, Status) — round 1 (pls-x-reviewer, opus, high, 2026-11-17)

**Accept with fixes**; 0 Critical / 1 High / 2 Medium / 4 Low. `git status` unchanged by the review.

| Finding | Severity | Disposition |
|---|---|---|
| F1: the selection brief points at `evals/<skill>/<case>/input.md` — the folder names the expected skill; baseline likewise names the withheld skill | High | Fixed: for baseline and selection the Orchestrator copies `input.md` into the run's scratch folder as `request.md`; the brief names no `evals/` path; selection may open only its scratch folder (brief patch, `evals/README.md`) |
| F2: runner definition "read `docs/agent-rules.md` and `CLAUDE.md`" contradicts the selection allow-list | Medium | Fixed: the runner reads them unless its brief says "You may open only" without naming them (keeps ADR-0030 Part 3's exact allow-list) |
| F3: `HANDOFF.md` describes earlier eval misses like `skills/README.md`; only the with-skill arm could read it | Medium | Fixed: `HANDOFF.md` added to the with-skill "must not open" list, the runner's never-open list and `evals/README.md` (strengthens blindness; ADR-0030 named only `skills/README.md`) — reported to Nam |
| F4: void rule undefined for the with-skill arm; `../_agent-scratch-held/` not named; missing opened-files list not covered | Low | Fixed: three void conditions in the brief's Orchestrator notes; held folder in both never-open lists |
| F5: stale "per case" wording (`docs/agent-rules.md` §2, runner title, `CLAUDE.md` agent-team line) | Low | Fixed (patches; `CLAUDE.md` non-Mandatory section edited directly) |
| F6: a baseline runner may think it cannot ask for `pls` commands | Low | Fixed: runner step 4 covers "when your brief names no skill, where the request needs you" |
| F7: `interviewee.md` missing from the brief's must-not list | Low | Fixed |

Verification after fixes: all four patches `git apply --check` OK on `770a4a8`; applied in temporary worktree `../_agent-scratch/wt-s3` with the step-3 files: Python 719 OK, node 16/16.

## Step 3 — round 2 (pls-x-reviewer, opus, high, 2026-11-17)

**Accept with fixes**; 0 Critical / 0 High / 3 Medium / 2 Low; all seven round-1 findings resolved. `git status` unchanged by the review. Review limit (2 rounds) reached; no Critical or High open.

| Finding | Severity | Disposition |
|---|---|---|
| M1: the held folder is named to the runner (must-not lists, `docs/agent-rules.md` §3, which the runner reads) while ADR-0030 Part 1 says "the runner is never told about it" — the ADR itself puts it into §3 (Consequences) | Medium | Fixed as the safer reading: the folder stays named only as a path not to open; every "never told" sentence now reads "never told what it holds or that other runs exist". **Differs from Part 1's wording — asked of Nam** before he applies the patches |
| M2: copying `input.md` word for word passes setup notes to baseline / selection runs (inputs that name the skill, point to another case's input or to `evals/results/`, say what the case measures) | Medium | Fixed: before a baseline or selection batch the Orchestrator reads each input; such inputs get a `request.md` with request and premises only, approved by Nam with the batch; selection inputs hold the request only (brief notes, `evals/README.md`). The same notes reach with-skill runs today — reported to Nam as follow-up (not changed here) |
| M3: Grep / Glob escape the opened-files list | Medium | Fixed: search roots are listed; a search whose root or results include a path counts as opening it; baseline / selection search only inside their allow-list (brief, runner, README) |
| L1: README interim rule omitted `HANDOFF.md` / `interviewee.md` / held folder and allowed k calls while §4 says one call per case | Low | Fixed: listed; k runs per case only once Nam approves the batch |
| L2: runner step 1 named only `input.md`; selection skill list unordered | Low | Fixed: "the case input your brief names (`input.md` or `request.md`)"; list in alphabetical order of name |

Verification: HEAD moved to `62a113f` (other session; no overlap with these files). Patches regenerated; all four applied in a fresh worktree at `62a113f` with the step-3 files: Python 723 OK (exit 0), node 16/16.
