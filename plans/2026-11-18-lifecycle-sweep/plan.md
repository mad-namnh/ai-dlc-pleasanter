# Plan — lifecycle sweep on 0.30 (item 2)

Task (Nam, 2026-11-18): "ok lam theo thu tu"; batch approved: "Duyệt cả 21 (Recommended)" — the 7 other lifecycle cases, k = 3, on 0.30.
Tier: Standard (eval run and grading; one case input revised). No review subagent: the runs are the evidence and the rubric grading is the Orchestrator's (skill workflow step 9).

## Acceptance criteria
1. Cases 001–006 and 008 run k = 3 each, blind, runs of a case never overlapping; every opened-file list checked.
2. Each run graded against its `expected.md`; result `evals/results/pls-x-lifecycle/2026-11-18-lifecycle-sweep.md` per the template.
3. A case input that cannot reach its rubric under the current skill is fixed (input only, never the rubric) and the case rerun k = 3.
4. `skills/README.md` lifecycle row records the outcome.
5. Both suites green on HEAD + this change.
