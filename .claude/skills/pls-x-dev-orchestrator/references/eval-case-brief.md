# Brief for `pls-x-eval-case-runner`

One brief = one run of one case. Fill every field of the arm being run. Never add the rubric, the review standard, an earlier result or a hint about what is being measured — not even which arm this is or that other runs exist.

## Arm "with skill" (every eval)

- **Skill under test:** `skills/<skill>/` (read its `SKILL.md` and references)
- **Case input:** `../_agent-scratch/<run-id>/request.md` (the Orchestrator copies the case `input.md` there word for word; the brief names no `evals/` path — case folder names describe what the case tests)
- **Scratch folder:** `../_agent-scratch/<run-id>/` — the only place you may write (a copy of a `pls-demo-*` project without `.pls/`, or the files the input lists, is already there; for a fictional project, build it at the root of that folder — `pls` finds the project by its `environments.json`). A file you cannot write (e.g. under `.pls/`) stays a premise of the input
- **Dry run:** no `pls` command that contacts Pleasanter, no network
- **Local `pls` commands:** you have no shell; `pls` is run for you (local-only commands, as your agent definition lists). A turn ends in exactly one of two ways: (a) you need a command — end with `COMMAND TO RUN:` and the command (`pls <command> …`), nothing after it; you are resumed with its output word for word; (b) you need no more command — end with your report, whose last part is the message to the person. Never both in one turn — except when you are asked to hand back while a command is pending: then your report ends with that `COMMAND TO RUN:` block
- **You must not open:** anything under the framework's `docs/` (where `CLAUDE.md` or a template points to a file there, do not follow it) or `evals/` (case folders with their `input.md`, `setup.md`, `interviewee.md` and `expected.md`; results), any `expected.md` or `interviewee.md` wherever it lies, the framework's `plans/` folder, `skills/README.md`, `HANDOFF.md`, any folder under `../_agent-scratch/` other than your scratch folder, anything under `../_agent-scratch-held/`, any other project repository next to the framework (e.g. `../pls-demo-*`)
- **Return** (ending b): what you did step by step, the files you wrote in the scratch folder, the commands you asked for and their output, every question you would ask the person, where you stopped and why, **every file you opened (full path, one per line) and the root of every Grep or Glob search** — a search whose root or results include a path counts as opening it, and last the complete message to the person under a line `MESSAGE TO <name>:`

## Arm "baseline" (no skill; only when Nam approved the batch)

Same fields as above, except:

- **Skill under test:** none. Do the request with what the project and the framework rules give you.
- **Case input:** `../_agent-scratch/<run-id>/request.md` (the Orchestrator copies the case `input.md` there word for word; the brief names no `evals/` path)
- **You may open only:** your scratch folder; in the framework `skills/pls-kb-pleasanter/`, `CLAUDE.md` and `templates/`. Search only inside these. Nothing else — in particular no `docs/` (where `CLAUDE.md` or a template points to a file under `docs/`, do not follow it), no other folder under `skills/`, no `skills/README.md`, no `HANDOFF.md`, no `evals/`, no skill copy in another project folder
- (Orchestrator, before the run: in a scratch copy of a project, remove every folder under `.claude/skills/` other than `pls-kb-pleasanter`, and record it in the result. Not part of the brief text.)

## Arm "selection"

- **Request:** `../_agent-scratch/<run-id>/request.md` (the Orchestrator copies the case `input.md` there word for word; the brief names no `evals/` path, whose folder would give the answer away)
- **Skills available:** <the `name` and `description` of every folder under `skills/`, copied here verbatim, in alphabetical order of name, nothing else>
- **Scratch folder:** `../_agent-scratch/<run-id>/` — you may write your answer there
- **You may open only:** your scratch folder (search only inside it). No skill body, no `CLAUDE.md`, no other framework file
- **Return:** the one skill you would use for this request, or "none"; why, in at most five sentences; every file you opened

## Orchestrator notes (not part of the brief)

- One brief = one runner call (resumed only for the relays of that run). k runs per case: P1, P2, lifecycle k = 3; other skills k = 1 (`evals/README.md`).
- `<run-id>`: neutral and unique across skills — it names neither the skill, the arm nor the run number; keep the mapping in the result file.
- Baseline and selection batches are asked of Nam with their k and number of runs. Before such a batch, read each case `input.md`: one that names the skill under test, points to a path outside the arm's "You may open only", or carries setup notes, earlier results or what the case measures gets a `request.md` with the request and its premises only (files it relies on copied into the scratch folder); Nam approves those variants with the batch. A selection case's `input.md` holds the request only.
- Before the next run of the same case, move the earlier runs' folders (both arms) to `../_agent-scratch-held/`; move them back after grading. The runner is never told what it holds or that other runs exist; it sees the folder only as a path not to open.
- A runner turn that ends with `COMMAND TO RUN:` often comes back as its report (the harness ends the turn and asks it to hand back). When a report ends with a `COMMAND TO RUN:` block, run the allowed commands as `evals/README.md` says and resume the runner with their outputs and refusal lines (SendMessage) before grading; the run's report is the one after the last relay, and its list of opened files covers the whole run (check every report's list for the void rule).
- After the run, record from each completion notice of the runner: `subagent_tokens`, `tool_uses`, `duration_ms` (sum over resumes), the number of `pls` commands relayed; the person-role subagent on its own line. Not reported → "not reported".
- A run is **void** (rerun it) when its list of opened files: includes a path under `../_agent-scratch/` other than its own folder, or under `../_agent-scratch-held/`; includes a "must not open" path (with skill) or a path outside "You may open only" (baseline, selection); or is missing.
