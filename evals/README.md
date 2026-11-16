# Evals

Each skill has cases built from real work (slices). A case is:

- `input.md` — what the skill receives (request, current configuration summary, approved inputs)
- `expected.md` — a **rubric**: must-have properties (pass/fail) and anti-patterns (fail if present). Not a golden text — wording may differ.

## Running (v0.1, manual)

1. Create a scratch project repository (copy of `pls-demo-inquiry` at the stated baseline, or the files listed in `input.md`).
2. Invoke the skill with the input.
3. Grade the output against `expected.md`: every **Must** item passes and no **Must not** item appears → case passes.
4. Record the result in `results/<skill>/<date>.md` with the model and skill version used, and — under ADR-0030 — each run's arm, grade and cost and the count `x / k` (template below).

Steps 2–3 are repeated k times per case in each arm that is run (section "Repeats, the no-skill baseline, scope and selection cases, cost").

### Cases with a person in the loop (interview)

A case folder that holds an `interviewee.md` needs someone to answer the skill's questions. The answers come from a second subagent that plays the person:

1. The agent under test gets `input.md` only, as always. It must not open `interviewee.md`, `expected.md` or the `plans/` folder, where a proposed rubric may lie (name them in its brief).
2. The person-role subagent gets `interviewee.md` only — not the skill, not `input.md`, not the rubric.
3. Whoever runs the case relays: each message of the agent under test that ends with questions goes to the person-role subagent **unchanged**, and its reply goes back **unchanged**. The relay adds nothing, answers nothing and corrects nothing.
   When the agent under test is a subagent, its turn ends with a report to whoever runs the case, not with a chat message: its brief tells it to put the complete message for the person at the end, under a line `MESSAGE TO <name>:`, and only that part is relayed. Its next message is the person's reply.
   Check every reply of the person-role subagent against `interviewee.md` before passing it on. A reply that leaves the script (a fact given away before it is asked for, an invented fact) is not delivered: tell the role-player which part of the script it broke, take its new reply, and record both replies and the correction in the transcript and the result.
4. Keep the full transcript (both sides, in order) with the result; the rubric is graded against the files **and** the transcript.
5. The result file records both models.

### Local `pls` commands during a run

The eval runner has no shell (on purpose: a shell could reach Pleasanter with the operator's credentials, and no hook enforces an allowlist yet — TD-21). When the skill under test needs a `pls` command that works on local files, the runner ends its turn with it under `COMMAND TO RUN:`, written as `pls <command> …` (runner definition and brief form: patch `plans/2026-11-11-eval-runner-local-pls/proposed-eval-runner-local-pls.patch`, in force once Nam applies it). Whoever runs the case:

1. Runs it only if it is on the local-only list — `lint`, `xref`, `canon`, `pack`, `coverage`, `refs` without `--keep` / `--ref`, `skills check` (never `skills sync`) — with no other command chained to it (`&&`, `;`, `|`, redirection), with every path argument (`--out`, a file) resolving inside the scratch folder, and `--site` a single name (no `/`, `\` or `..`).
2. Runs the **framework's own** tool, never a file from the scratch folder: `python -I "<framework>/tools/pls/pls.py" <command> …` with the scratch folder as the working directory — and only when that folder itself holds `environments.json`: `pls` walks up from the working directory to the first `environments.json`, so without one it would act on whatever project lies above. The runner can write in the scratch folder, so a `pls.py`, a copy of `tools/pls` or a `*.py` there is code it may have written; the scratch project therefore gets no copy of `pls` and no launcher. (`lint` hands script bodies to `node` only to compile them — `vm.Script`, nothing is executed.)
3. Returns stdout and stderr **word for word**, with the exit code, as the next message. Nothing added, nothing explained.
4. Refuses anything else (a command that contacts Pleasanter, `gate`, `profile`, `review`, a decision through `refs`, `skills sync`) with one line naming the reason; the runner goes on without it.
5. Records every command and its result in the transcript.

## Repeats, the no-skill baseline, scope and selection cases, cost (ADR-0030)

Rules in [ADR-0030](../docs/adr/0030-eval-repeats-no-skill-baseline-and-activation-cases.md); this section says how they are run. The files the Orchestrator and the runner obey — `.claude/skills/pls-x-dev-orchestrator/SKILL.md` and `references/eval-case-brief.md`, `.claude/agents/pls-x-eval-case-runner.md`, `docs/agent-rules.md` §3–§5 — carry these rules only once Nam applies the patches proposed in `plans/2026-11-17-adr-0030-build/`. Until then: with-skill runs may be run at k runs per case, and the person running the case adds to each brief the extra paths not to open (`skills/README.md`, other run folders) and the request for the list of opened files; **baseline and selection runs wait** until the patches are applied (the runner's definition still tells it to read a skill).

### Repeated runs (k)

- `pls-p1-requirements-analyst`, `pls-p2-solution-designer`, `pls-x-lifecycle`: every case **k = 3** runs. Other skills: k = 1, more on Nam's request.
- One run = one runner call in a fresh scratch folder `../_agent-scratch/<run-id>/` — a neutral id, unique across skills, that names neither the arm nor the run number (the mapping to skill, case, arm and run is kept in the result file) — resumed only for relayed commands and messages of that run. A case at k = 3 is three calls.
- **Runs do not see each other.** Before the next run of the same case starts, move the folders of its earlier runs (both arms) to `../_agent-scratch-held/`; move them back after grading. Never tell the runner about the holding place.
- A case **passes** on a skill version only with **k / k** passing runs. A failed run is a finding: name the failing rubric items and change the skill, the case input or the rubric through the usual path before the version is called passed.
- Interview cases run k times like any other, each run with its own person-role subagent and transcript.

### No-skill baseline arm

- **When:** (a) once per skill, to establish its lift on its current cases; (b) before trimming or removing skill text (below); (c) on Nam's request. Never on every eval. Each batch of baseline runs is asked of Nam with its k and number of runs (ADR-0029's eval approval does not cover it). Interview cases get a baseline only when Nam asks.
- **Setup:** the same case input, model and scratch setup as the with-skill arm, except the skill: the brief names no skill, and in a scratch copy of a project every folder under `.claude/skills/` other than `pls-kb-pleasanter` is removed before the run. Same k as the with-skill arm.
- **Allow-list:** the runner may open only its own scratch folder, its case `input.md`, and in the framework `skills/pls-kb-pleasanter/`, `CLAUDE.md`, `docs/` (not `docs/review-criteria.md`) and `templates/`. Anything else — another run's folder, `skills/README.md`, any other skill, a skill copy in a sibling project — **voids** the run; rerun it.
- **In both arms** the runner lists every file it opened, and never opens `skills/README.md` (its rows say what earlier runs missed) or another run's folder. A run in either arm that opened one of them, or (baseline) anything outside its allow-list, is **void**: rerun it. The result states that the separation rests on the brief and that list.
- **Lift** per case = Must items passed with the skill − Must items passed without it, each averaged over the k runs; report it with the Must-not hits of each arm, averaged the same way. The arms differ by the skill and everything it references (other skills' references, generated references such as P2's `impact-rules.md`); the KB and the framework rule files are in both.

### Scope and selection cases

- **Scope cases** run like a normal case, with the skill loaded. *Negative:* a request outside the skill's scope — the rubric expects the skill not to act and to say where the request belongs. *Edge:* a request at the boundary — the expected stop, refusal or route is written in the rubric before any run. They do not show whether the harness would pick the skill.
- **Selection cases:** the brief gives the request and only the `name` and `description` of every framework skill (copied into the brief), no skill body; the runner answers which skill it would use, or none, and why. It may open only its own scratch folder and its case `input.md`; any other path voids the run. The rubric names the expected skill or "none". This tests whether the descriptions separate the skills; it is not Claude Code's own choice. Like baseline runs, each batch of selection runs is asked of Nam with its k and number of runs (not covered by ADR-0029's eval approval).
- A new rubric (`expected.md`) is a protected path: proposed as a patch, applied by Nam. First targets: lifecycle (routing), P6, onboarding.

### Cost per run

Record for every run, in both arms: `subagent_tokens`, `tool_uses` and `duration_ms` from the Agent tool's completion notice (a resumed run sums all its notices), and the number of `pls` commands relayed. The person-role subagent of an interview case is recorded on its own line. A value the harness does not report is written "not reported", never estimated.

### When the baseline does as well as the skill

"Does as well": on every case, averaged over k, the baseline passes as many Must items **and** has no more Must-not hits. Then, in order:

1. **Check the evidence.** Do the cases exercise what the skill protects (gate stops, refusals, EV-01…EV-10)? If not, add scope cases that do and run again. With fewer than 3 cases or a 1-item difference, record "no measured difference", not "no lift".
2. **Keep guard text** (gate stops, refusals, safety rules) even with zero lift, until a deterministic check holds it (ADR-0029: `pls check`, hooks).
3. **Trim what the model does by itself:** generic text with no lift on any case; evaluate the trimmed version in both arms. Generated references are never trimmed here (only through their generator).
4. **Remove a whole skill** only when all hold: no guard text; no lift and no more Must-not hits in the baseline over at least 3 cases at k = 3; the same on the weakest model the framework is meant to support (open: Nam names it); the baseline does not cost more (tokens, tool calls, relayed commands). Removal is Nam's decision.

### Results stay evidence

No pass count, lift or cost figure blocks a commit, a gate or a release (I6). A result with fewer than 10 cases for the skill, or with no negative scope case, is labelled **provisional**. No eval dataset, rubric or expected output is placed inside `skills/` (`tools/pls/tests/test_skills_hold_no_eval_data.py`).

### Result file

`results/<skill>/<date>[-<label>].md`:

```markdown
# Eval results — <skill> — <date> (<skill version>[; provisional])

- **Model:** <model id> (every run and both arms); person-role: <model id> (interview cases)
- **Versions:** <skill> <version>, pls-kb-pleasanter <version>, other skills the case loads
- **Setup:** <scratch project / fictional>; arms run: with skill[, baseline (folders removed under .claude/skills/: …)][, selection]; k = <k>
- **Separation:** blindness and the separation of runs and arms rest on the briefs and on each runner's list of opened files, not on technical isolation.

| Case | Arm | Run (run-id) | Grade | Failing items | Forbidden or not-allowed paths opened | Tokens | Tool uses | Duration (s) | `pls` relayed |
|---|---|---|---|---|---|---|---|---|---|
| 001 | skill | 1 (r-7f3a) | PASS | — | none | … | … | … | … |

| Case | Skill x / k | Baseline x / k | Lift (Must, avg) | Must-not hits (skill / baseline, avg) |
|---|---|---|---|---|

**Findings:** …
```

Automated grading is future work (tech debt). Add a case whenever a slice or an incident reveals a behaviour the skill must keep (I9).
