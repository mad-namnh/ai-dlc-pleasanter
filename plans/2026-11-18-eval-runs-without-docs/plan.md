# Plan — no eval runner opens docs/; relays of local pls commands

Task (Nam, 2026-11-18), answers after the analysis: "Giữ sửa tại chỗ (Recommended)", "Cấm cả hai nhánh (Recommended)", "Giữ, ghi là giới hạn (Recommended)", "A trước, rồi B (Recommended)".
Tier: Critical (ADR text, runner definition) → review on opus, effort high.

## Acceptance criteria
1. ADR-0030 Part 2: no runner opens `docs/` in either arm, with Nam's words and why; framework `CLAUDE.md` recorded as a known limit; earlier with-skill results flagged; Status says the amendment stays in place.
2. Runner definition and brief (protected) as `proposed-eval-runner-and-brief-no-docs.patch` with a reason header, `git apply --check` clean: the runner no longer reads `docs/agent-rules.md`, never opens `docs/` nor follows pointers to it; a runner asked to hand back before a relayed output reports the command as not run; the Orchestrator resumes it with the output before grading.
3. `evals/README.md`: allow-list, lift line, relay step 6; no eval run before the patch is applied.
4. Both suites green on HEAD + this change + the patch.
5. Then (after Nam applies): batch A — scope cases (lifecycle k = 3, P6 and onboarding k = 1) and selection cases (k = 3): 17 runs.
