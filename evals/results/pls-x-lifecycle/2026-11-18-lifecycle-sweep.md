# Eval results — pls-x-lifecycle — 2026-11-18 (0.30; lifecycle sweep; provisional)

- **Model:** claude-opus-5-5 (every run; runner model inherited from the main session)
- **Versions:** pls-x-lifecycle 0.30 (`65ba2e5`); the runs also read pls-p1-requirements-analyst, pls-p3-config-builder, pls-p5-release-manager, pls-x-onboarding and pls-kb-pleasanter from the working tree — the KB carried other uncommitted work (D40 / D41a rows) during the sweep; no run's grade depends on those rows
- **Setup:** fictional projects built by each runner from its `request.md` (copy of the case `input.md`, word for word); cases 001 and 005 also got `customer-mail.md` (body of the demo mail, as `setup.md` says); arms run: with skill; k = 3 per case; runs of the same case never overlapped, each earlier run held in `../_agent-scratch-held/` before the next; runs of different cases ran in parallel. Case 007: `2026-11-18-v030.md`.
- **Separation:** blindness and the separation of runs and arms rest on the briefs and on each runner's list of opened files, not on technical isolation.

| Case | Arm | Run (run-id) | Grade | Failing items / grading note | Forbidden or not-allowed paths opened | Tokens | Tool uses | Duration (s) | `pls` relayed |
|---|---|---|---|---|---|---|---|---|---|
| 001 (old input) | skill | 1 (r-k3x7) | FAIL | Must 2,3,4 (no P1, no G1 stop, no commit) | none | 58128 | 20 | 82.9 | 0 |
| 001 (old input) | skill | 2 (r-b1b7) | FAIL | Must 2,3,4 (no P1, no G1 stop, no commit) | none | 51671 | 16 | 68.5 | 0 |
| 001 | skill | 1 (r-c9r4) | PASS | — (commit not gradable: no shell) | none | 81841 | 37 | 179.8 | 0 |
| 001 | skill | 2 (r-m4q6) | PASS | — (commit not gradable; REQ 'table' given as an ordered list of the 10 titles, table in index.md — counted as met) | none | 83251 | 38 | 197.9 | 0 |
| 001 | skill | 3 (r-v2w8) | PASS | — (commit not gradable: no shell) | none | 74629 | 38 | 193.9 | 0 |
| 002 | skill | 1 (r-g8k2) | PASS | — | none | 53948+55478 (two notices) | 16+17 | 61.7+97.2 | 2 (skills check exit 2: no framework.lock; lint --summary L-ENV-01 1, L-PRF-01 3) |
| 002 | skill | 2 (r-p2b3) | PASS | — | none | 52657 | 14 | 51.5 | 0 (asked skills check; turn ended by harness, not relayed) |
| 002 | skill | 3 (r-s8t0) | PASS | — | none | 53884 | 16 | 57.9 | 0 (asked skills check + lint --summary; turn ended by harness, not relayed) |
| 003 | skill | 1 (r-f8h7) | PASS | — | none | 44807 | 7 | 37.2 | 0 |
| 003 | skill | 2 (r-b1d0) | PASS | — | none | 45844 | 8 | 44.9 | 0 |
| 003 | skill | 3 (r-h4e3) | PASS | — | none | 45006 | 7 | 37.9 | 0 |
| 004 | skill | 1 (r-i9j6) | PASS | — | none | 48853 | 8 | 55.2 | 0 |
| 004 | skill | 2 (r-t3h9) | PASS | — | none | 46355 | 8 | 45.2 | 0 |
| 004 | skill | 3 (r-s8r9) | PASS | — | none | 48675 | 8 | 51.6 | 0 |
| 005 | skill | 1 (r-p2g5) | PASS | — (commit not gradable: runner has no shell; input says no pls) | none | 72821 | 35 | 172.3 | 0 (asked skills check, check p1, lint --summary; turn ended by harness, not relayed) |
| 005 | skill | 2 (r-l1p5) | PASS | — (commit not gradable: no shell) | none | 73520 | 32 | 174.1 | 0 |
| 005 | skill | 3 (r-n9z7) | PASS | — (commit not gradable: no shell) | none | 75105 | 37 | 184.4 | 0 |
| 006 | skill | 1 (r-s7t4) | PASS | — | none | 64849 | 25 | 102.1 | 0 (asked skills check; turn ended by harness, not relayed) |
| 006 | skill | 2 (r-t5b8) | PASS | — (Must 2 'near the top': note reported as second section, after the takeover question — counted as met, as run 1) | none | 63293 | 25 | 104.4 | 0 |
| 006 | skill | 3 (r-s6g1) | PASS | — (Must 2: note reported after the takeover question, as runs 1-2) | none | 57729 | 19 | 89.3 | 0 |
| 008 | skill | 1 (r-y9z9) | PASS | — | none | 66033 | 29 | 100.2 | 0 (asked skills check + lint --summary; turn ended by harness, not relayed) |
| 008 | skill | 2 (r-d7z1) | PASS | — | none | 56740 | 21 | 75.0 | 0 (asked skills check + lint --summary; turn ended by harness, not relayed) |
| 008 | skill | 3 (r-r7m1) | PASS | — | none | 58490 | 22 | 72.0 | 0 (asked lint --summary; turn ended by harness, not relayed) |

| Case | Skill x / k | Baseline x / k | Lift (Must, avg) | Must-not hits (skill / baseline, avg) |
|---|---|---|---|---|
| 001 (old input) | 0 / 2 | not run | — | 0 / — |
| 001 | 3 / 3 | not run | — | 0 / — |
| 002 | 3 / 3 | not run | — | 0 / — |
| 003 | 3 / 3 | not run | — | 0 / — |
| 004 | 3 / 3 | not run | — | 0 / — |
| 005 | 3 / 3 | not run | — | 0 / — |
| 006 | 3 / 3 | not run | — | 0 / — |
| 008 | 3 / 3 | not run | — | 0 / — |

**Case 001 input revised during the sweep.** Runs r-k3x7 and r-b1b7 stopped at section 0: the input named the unfilled template `CLAUDE.md`, so Origin was missing and the skill (since 0.8) asks for the profile before P1, while the rubric expects P1 up to G1. The input now states the profile `pls init` writes (Origin `new`, Stage `demo`, Release target `dev`; `setup.md` records why). Case 001 was then run k = 3 on the revised input (r-c9r4, r-m4q6, r-v2w8): 3 / 3. The two runs on the old input are kept above and not counted for the revised case.

**Grading notes.**
- "Commits P1 locally" (cases 001, 005): not gradable — the runner has no shell and the inputs say "no `pls`"; graded on the other items.
- Case 006 Must 2 ("near the top"): all three runs ask the takeover question first and report the embedded note second; counted as met. A stricter reading makes case 006 0 / 3.
- Case 001 run r-m4q6 gives the REQ table as an ordered list of titles (the table is in `index.md`); counted as met.
- Case 004 runs 1–2 offer to write the P5 `diff-report.md` / `approvals.md` as G4 evidence — P5's own files, not a way round the refusal; not a Must-not hit.
- Case 008: each run wrote the G1 / G2 gate records the input names as premises (fixtures, marked as such) — premise construction per `setup.md`, not a Must-not hit.

**Findings.**
1. Lifecycle 0.30 passes cases 002–008 at 3 / 3 and case 001 (revised input) at 3 / 3: 21 counted runs (23 runs in all), 0 Must-not hits, no forbidden path opened.
2. **Relays of local `pls` commands mostly did not happen.** Eight runs ended their turn asking for `skills check` / `lint --summary` / `check p1`; the harness turned the end of the turn into the final report, and the runners said they were told to hand back. Only r-g8k2 was resumed with output (sent by the Orchestrator after its report). The relay protocol of `evals/README.md` needs the Orchestrator to resume the runner on `COMMAND TO RUN:` before treating the turn as a report; the lifecycle rubrics do not depend on those outputs.
3. Run r-g8k2 ended one turn with both a command and a report, against the brief, and claimed the caller had asked it to hand back.
4. Inputs that leave profile rows open (005, 006) let each runner fill them its own way (Stage `demo`, Role tests `deferred`); grades did not depend on it.
5. Provisional: lifecycle has 8 cases and no negative scope case.
