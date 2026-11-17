# Plan — eval case inputs hold only what the runner may read

- **Date:** 2026-11-17. **Asked by:** Nam ("ok tiếp tục", after the ADR-0030 build). **Tier:** Critical (evaluation contract; protected paths as patches).
- **Nam's choices (AskUserQuestion, 2026-11-17, verbatim):** split "input.md + setup.md (Recommended)"; test "Có (Recommended)"; scope / selection cases "Để sau (Recommended)"; ADR-0030 Status "partly built, patches applied (Recommended)".

## Problem

The runner brief says "read `evals/<skill>/<case>/input.md`", and the inputs mix the request and its premises with notes for whoever builds the scratch state: reference answers (P3 001, P4 001: `pls-demo-equipment/...` after the release), run history ("run 1 left it out"), what the case measures (P2 002, with a path into `evals/results/`), a list of what the agent must find (P1 002), another case's input path (P2 001), names of real sibling repositories whose later state holds the answer, and headings naming the EV behaviour under test.

## Change

1. Every case folder: `input.md` = what the runner may read (neutral heading `# Input`, premises, request); new `setup.md` = for the Orchestrator only (descriptive title, how the scratch state is built, files copied into it, reference answer, history, what the case measures, what the agent must find). Premise wording kept; only notes moved. Where a request lived in a sibling repository, the Orchestrator copies it into the scratch folder (`customer-mail.md`) and `input.md` names that file. P2 001 gets the current configuration inline. The fictional folder `pls-demo-purchase` becomes `purchase`.
2. Test `tools/pls/tests/test_eval_inputs_do_not_reveal_the_answer.py`: every case folder has `input.md`; it names no `evals/` path, `expected.md`, `setup.md`, rubric, reference answer, run number, "must find", what is measured, EV id, case number, slice, commit, `git archive`, or a sibling project repository (`pls-demo-…`, `pls-trial-…`, `pls-onboard-…`, `pls-adopt-…`, `demo-equipment`). `setup.md` joins the eval file names the `skills/` test refuses.
3. `evals/README.md`: case = `input.md` + `setup.md` (+ `expected.md`, `interviewee.md`).
4. Patches (protected): brief form and runner — `setup.md` and other project repositories next to the framework are never opened.
5. ADR-0030 Status (Nam's choice) and its README row.

## Acceptance criteria

1. No `input.md` holds a note from the list above; nothing removed from an input is lost (it is in `setup.md`).
2. The new test fails on the parent commit naming the leaking inputs, passes after; both suites green.
3. Patches `git apply --check` on the current commit; nothing weakens blindness or the relays.
4. Earlier results stay valid as records: the change is stated in `evals/README.md` (inputs before 2026-11-17 carried setup notes).
5. English only (Japanese requests verbatim); only this task's paths committed.
