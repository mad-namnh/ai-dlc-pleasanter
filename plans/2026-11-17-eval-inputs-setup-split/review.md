# Review — eval-inputs-setup-split

## Round 1 (pls-x-reviewer, opus, high, 2026-11-17)

**Accept with fixes**; 0 Critical / 1 High / 2 Medium / 5 Low. `git status` unchanged by the review.

| Finding | Severity | Disposition |
|---|---|---|
| F1: the with-skill runner is given `evals/<skill>/<case>/input.md`, and case folder names state the behaviour under test (`case-007-ev-10-yes-without-target`) — pre-existing | High | Fixed: in every arm the Orchestrator copies `input.md` into the run's scratch folder as `request.md`; the brief names no `evals/` path; the runner never opens anything under `evals/` (brief and runner patches, `evals/README.md`) |
| F2: "any `setup.md`" also forbids the framework doc `docs/setup.md` that `pls` output points to | Medium | Fixed: the patches forbid "anything under the framework's `evals/`" instead of a bare file name |
| F3: the test missed relative paths (`../case-001-…`, `results/…`) and `case-001`; `\bmeasur` flagged a plain premise | Medium | Fixed: patterns widened, `measur` only near case / run / eval or "to measure"; samples added (incl. a clean "Measurement devices are lent") |
| F4: lifecycle 006 `setup.md` "as case 001" would add case 001's `customer-mail.md` | Low | Fixed: "the project of lifecycle case 001, without its `customer-mail.md`" |
| F5: `evals/README.md` interview list lacked `setup.md`; "the runner never opens it" stated before the patches are applied | Low | Fixed: listed; the sentence names the pending patches |
| F6: `pls-demo-purchase` → `purchase` not recorded | Low | Fixed: a line in both `setup.md`; `expected.md` files checked by the Orchestrator — none uses the old name |
| F7: P1 001 / 002 `setup.md` keep build steps earlier runs found unworkable (`.pls/` export; `b510417^`) | Low | Fixed: "Known deviation" lines with the sources the 2026-11-11 runs used (from that result file) |
| F8: P3 001 points the runner to `../fw`, outside its own scratch folder | Low | Pre-existing; not changed — reported to Nam (the P3 case needs its framework copy placed inside the run's folder before its next run) |

Verification after fixes: patches `git apply --check` OK on `a9deff5`; worktree `../_agent-scratch/wt-split` (a9deff5 + all changes + both patches applied): Python 726 OK (exit 0), node 16/16.

## Round 2 (pls-x-reviewer, opus, high, 2026-11-17)

**Accept with fixes**; 0 Critical / 0 High / 0 Medium / 6 Low. F1–F7 resolved (F1 effective once Nam applies the patches); F8 open → R2-5. `git status` unchanged by the review. Review limit reached.

| Finding | Severity | Disposition |
|---|---|---|
| R2-1: the patches dropped the name-based ban on `expected.md` / `interviewee.md` outside `evals/`; runner definition lacks `plans/` | Low | Fixed: "any `expected.md` or `interviewee.md` wherever it lies" in both; `plans/` in the runner |
| R2-2: `evals/README.md` lines on request copies, interview inputs, pending ADR-0030 patches and the never-open list were stale or inconsistent | Low | Fixed: copy is word for word or the approved variant; interview step names `request.md` and `evals/`; ADR-0030 patches stated as applied (`a9deff5`); never-open list matches the brief |
| R2-3: test pattern gaps (plurals, "slice 2", "second run", "case tests", "graders") | Low | Fixed: patterns widened, six samples added |
| R2-4: test docstring said the runner reads `evals/…/input.md` and cited ADR-0030 for `setup.md` | Low | Fixed |
| R2-5 (= F8): P3 001 points the runner to `../fw` (outside its scratch folder; `pls` copy in scratch) | Low | Fixed: the input names the skills in `.claude/skills/` and says `pls` is run for the runner; `setup.md` records the change |
| R2-6: lifecycle 001 / 005 deliver the mail as a file | Low | Checked by the Orchestrator: the rubrics require "source saved verbatim", met by copying `customer-mail.md` into `requirements/sources/`; noted in both `setup.md` |
| Info: `setup.md` refused by name under `skills/` | — | Comment added in the test |

Verification: patches `git apply --check` OK on `a9deff5`; fresh worktree with all changes and both patches applied: Python 726 OK (exit 0), node 16/16.
