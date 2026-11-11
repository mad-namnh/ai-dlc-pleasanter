# Brief for `pls-x-eval-case-runner`

One brief = one case. Fill every field. Never add the rubric, the review standard, an earlier result or a hint about what is being measured.

- **Skill under test:** `skills/<skill>/` (read its `SKILL.md` and references)
- **Case input:** `evals/<skill>/<case>/input.md` — read this file only from that case folder
- **Scratch folder:** `../_agent-scratch/<run-id>/` — the only place you may write (a copy of a `pls-demo-*` project without `.pls/`, or the files the input lists, is already there; for a fictional project, build it at the root of that folder — `pls` finds the project by its `environments.json`). A file you cannot write (e.g. under `.pls/`) stays a premise of the input
- **Dry run:** no `pls` command that contacts Pleasanter, no network
- **Local `pls` commands:** you have no shell; `pls` is run for you (local-only commands, as your agent definition lists). A turn ends in exactly one of two ways: (a) you need a command — end with `COMMAND TO RUN:` and the command (`pls <command> …`), nothing after it; you are resumed with its output word for word; (b) you need no more command — end with your report, whose last part is the message to the person. Never both in one turn
- **You must not open:** any `expected.md`, `docs/review-criteria.md`, `evals/results/`, the framework's `plans/` folder
- **Return** (ending b): what you did step by step, the files you wrote in the scratch folder, the commands you asked for and their output, every question you would ask the person, where you stopped and why, and last the complete message to the person under a line `MESSAGE TO <name>:`
