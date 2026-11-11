# Brief for `pls-x-eval-case-runner`

One brief = one case. Fill every field. Never add the rubric, the review standard, an earlier result or a hint about what is being measured.

- **Skill under test:** `skills/<skill>/` (read its `SKILL.md` and references)
- **Case input:** `evals/<skill>/<case>/input.md` — read this file only from that case folder
- **Scratch folder:** `../_agent-scratch/<run-id>/` — the only place you may write (a copy of a `pls-demo-*` project without `.pls/`, or the files the input lists, is already there)
- **Dry run:** no `pls` command that contacts Pleasanter, no network
- **Local `pls` commands:** you have no shell; `pls` is run for you. End your turn with the command under `COMMAND TO RUN:` (`pls <command> …`) and its output comes back as the next message (local-only commands, as your agent definition lists)
- **You must not open:** any `expected.md`, `docs/review-criteria.md`, `evals/results/`
- **Return:** what you did step by step, the files you wrote in the scratch folder, every question you would ask the person, and where you stopped and why
