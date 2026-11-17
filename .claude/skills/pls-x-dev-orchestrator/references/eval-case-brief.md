# Brief for `pls-x-eval-case-runner`

One brief = one run of one case. Fill every field of the arm being run. Never add the rubric, the review standard, an earlier result or a hint about what is being measured — not even which arm this is or that other runs exist.

## Arm "with skill" (every eval)

- **Skill under test:** `skills/<skill>/` (read its `SKILL.md` and references)
- **Case input:** `evals/<skill>/<case>/input.md` — read this file only from that case folder
- **Scratch folder:** `../_agent-scratch/<run-id>/` — the only place you may write (a copy of a `pls-demo-*` project without `.pls/`, or the files the input lists, is already there; for a fictional project, build it at the root of that folder — `pls` finds the project by its `environments.json`). A file you cannot write (e.g. under `.pls/`) stays a premise of the input
- **Dry run:** no `pls` command that contacts Pleasanter, no network
- **Local `pls` commands:** you have no shell; `pls` is run for you (local-only commands, as your agent definition lists). A turn ends in exactly one of two ways: (a) you need a command — end with `COMMAND TO RUN:` and the command (`pls <command> …`), nothing after it; you are resumed with its output word for word; (b) you need no more command — end with your report, whose last part is the message to the person. Never both in one turn
- **You must not open:** any `expected.md` or `interviewee.md`, `docs/review-criteria.md`, `evals/results/`, the framework's `plans/` folder, `skills/README.md`, `HANDOFF.md`, any folder under `../_agent-scratch/` other than your scratch folder, anything under `../_agent-scratch-held/`
- **Return** (ending b): what you did step by step, the files you wrote in the scratch folder, the commands you asked for and their output, every question you would ask the person, where you stopped and why, **every file you opened (full path, one per line) and the root of every Grep or Glob search** — a search whose root or results include a path counts as opening it, and last the complete message to the person under a line `MESSAGE TO <name>:`

## Arm "baseline" (no skill; only when Nam approved the batch)

Same fields as above, except:

- **Skill under test:** none. Do the request with what the project and the framework rules give you.
- **Case input:** `../_agent-scratch/<run-id>/request.md` (the Orchestrator copies the case `input.md` there word for word; the brief names no `evals/` path)
- **You may open only:** your scratch folder; in the framework `skills/pls-kb-pleasanter/`, `CLAUDE.md`, `docs/` except `docs/review-criteria.md`, and `templates/`. Search only inside these. Nothing else — in particular no other folder under `skills/`, no `skills/README.md`, no `HANDOFF.md`, no `evals/`, no skill copy in another project folder
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
- After the run, record from each completion notice of the runner: `subagent_tokens`, `tool_uses`, `duration_ms` (sum over resumes), the number of `pls` commands relayed; the person-role subagent on its own line. Not reported → "not reported".
- A run is **void** (rerun it) when its list of opened files: includes a path under `../_agent-scratch/` other than its own folder, or under `../_agent-scratch-held/`; includes a "must not open" path (with skill) or a path outside "You may open only" (baseline, selection); or is missing.
