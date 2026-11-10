# Plan — <task title>

- **Date / branch / parent commit:** <YYYY-MM-DD> / `brownfield-adr` / `<hash>`
- **Objective:** <one or two sentences>
- **Tier:** Light | Standard | Critical (`CLAUDE.md` "Adaptive Model Routing") — <why>
- **Scope:** <what changes>
- **Out of scope:** <what does not>
- **Files:** <paths expected to change>
- **Invariants and ADRs touched:** <I1–I9, ADR numbers, or "none">
- **Stop points expected:** <items of `docs/agent-rules.md` section 1, or "none">
- **Acceptance criteria:**
  1. <checkable statement>
- **Tests:** <new tests and what each must show; which suites run>
- **Subagents planned:** <reviewer / eval cases / KB curator, with the model and the reason; or "none">
- **Documents to update in the same commit:** <list>

# Log (`log.md`, same folder)

One line per event, oldest first:

`<time> | <decision, command with result, subagent call with model, stop point, commit hash>`

Keep a running count: subagent calls (not eval cases) n/6, review rounds n/2, fix attempts for the same test n/3.
The last entry of a finished task is `REPORT SENT`. A log without it is an open task (resume check).
