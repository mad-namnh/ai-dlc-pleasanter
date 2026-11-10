# ADR-0016 — An agent team for developing the framework

- **Status:** Proposed (2026-11-11) — Nam decides. The trial described below is not acceptance.
- **Context owner:** Nam
- **Related:** I4 (humans approve; AI never approves its own work), I6, I9; ADR-0013 (tool-first work), ADR-0014 (trust boundaries, TB-2, TB-5); review of the setup prompt `plans/reports/2026-11-11-agent-team-prompt-review.md`

## Context

Framework development (the design-review remediation, 2026-11-10/11) ran as one long Claude Code session that Nam steered step by step: inspect, implement, run both suites, show new tests failing on the parent commit, update the documents in the same commit, commit locally, report. It worked, but three things depended on the session remembering them: an independent look at each change, evals run blind, and never editing the knowledge base without evidence.

Nam wants to give one task and get a verified, reviewed, locally committed result with a report, stopping only where a person must decide.

A first design (seven specialist subagents, a self-written PreToolUse hook, the skill under `skills/`) was reviewed and found not ready: the skill would have been installed into customer projects, the hook's failure behaviour was unverified and probably fail-open, the team could edit its own guardrails, and one eval agent would have seen the rubric.

## Options

### Option A — One session, no team (as before)
- Pros: nothing to maintain; no extra cost.
- Cons: review, blind evals and KB discipline stay habits of one session.

### Option B — Seven specialist subagents under an orchestrator
- Pros: clear roles on paper.
- Cons: most tasks touch `tools/pls` and the documents that must change in the same commit, so roles split one commit across agents; many briefs and hand-offs; ownership cannot be enforced by tool lists; high cost.

### Option C — The Orchestrator implements; three subagents for what must be separate
- Pros: separation exactly where independence matters (review, eval runs, KB edits); few briefs; one integrator per commit.
- Cons: the Orchestrator still reviews its own plan; independence rests on briefs.

### Option D — Claude Code experimental Agent Teams
- Not considered further: experimental, multi-session, more than this repository needs.

## Decision (proposed)

Option C.

1. **Orchestrator** = the main session, driven by the skill `pls-x-dev-orchestrator`. It inspects, plans (`plans/<date>-<slug>/plan.md`, `log.md`), implements, verifies, has the change reviewed, commits locally on `brownfield-adr` and reports to Nam in Vietnamese.
2. **Three subagents** in `.claude/agents/`: `pls-x-reviewer` (read-only review), `pls-x-eval-case-runner` (one blind eval case per call), `pls-kb-curator` (KB edits from supplied evidence). Their frontmatter sets `model: inherit`; the Orchestrator passes the model per call.
3. **Where the assets live:** `.claude/agents/` and `.claude/skills/pls-x-dev-orchestrator/`. Never under `skills/`: every folder there with a `SKILL.md` is installed into project repositories by `pls skills sync`. They are not listed in `skills/README.md`.
4. **Rules by reference:** stop points, ownership, scratch space, subagent briefs and the budget are in `docs/agent-rules.md`. Model routing is `CLAUDE.md` "Adaptive Model Routing"; commit rules are `HANDOFF.md` "How we work". Nothing is restated here (review criterion A4).
5. **Nam's global rules** (`~/.claude/rules`) stay in force; `CLAUDE.md` maps their `planner`, `tester` and `code-reviewer` to this repository's plan file, framework suites and `pls-x-reviewer`.
6. **Controls:** Claude Code permission `deny` rules in `.claude/settings.json` for `git push`, the team's own configuration and instructions, `.pls/**`, the rules file, the review standard, eval rubrics and the project template's hard rules. No self-written hook in this version.
7. **Scratch space:** `../_agent-scratch/` for temporary worktrees, copies of `pls-demo-*` projects (without `.pls/`) and eval case folders.

## What was verified about Claude Code (2.1.322, official documentation, 2026-11-11)

Details and quotations: `plans/2026-11-11-agent-team-setup/log.md`.

- Project subagents are read from `.claude/agents/`; the frontmatter fields used (`name`, `description`, `tools`, `model`) are supported; the model can be set per call with an alias (`haiku`, `sonnet`, `opus`, `fable`).
- Project skills are read from `.claude/skills/`.
- `deny` rules win over `allow` from every settings file, so the allow list in Nam's `.claude/settings.local.json` cannot override them. They apply to subagents too. An `Edit(...)` rule covers every built-in tool that edits files; Read and Edit rules also cover the file commands Claude Code recognises in Bash (`cat`, `sed`, `tee`, …).
- A changed settings file is applied to the running session.

## Limits (stated, not solved)

- **The rules are guardrails, not a sandbox.** `Bash(git push *)` does not match a push written another way (`git -C . push`); a Python or Node script that opens a file itself is not covered by Read / Edit rules; a person outside Claude Code is not affected. Writes to Pleasanter are enforced by `pls` (role, `allow_write`, gate records, confirmation at a terminal, run-log check), not by these rules.
- **Reviewer independence and eval blindness are by brief, not by technical isolation.** The reviewer has Bash and could change files; the case-runner could open `expected.md`; a subagent can start another subagent (nesting is on by default). Only their instructions and the Orchestrator's `git status` check before and after stand against it.
- **Not expressible as a rule:** the Mandatory section inside `CLAUDE.md` (a rule matches files, not sections) — a stop point by rule only.
- **Paths outside the project:** `../…` rule syntax is not documented; the rules for `.pls/**` use the documented absolute form (`//**/.pls/**`). Whether they fire for a sibling project is checked in a new session.
- **Interception is not yet shown.** The checks in `plans/2026-11-11-agent-team-setup/permission-checks.md` run in a new session before the trial.
- **No hook.** A PreToolUse hook needs its failure behaviour checked against the documentation first (what blocks, what happens when the hook cannot start or times out), and an implementation that survives this machine's path with a space and non-ASCII folder names — `docs/tech-debt.md` TD-21.
- **Platform:** verified on Windows only. Nothing is claimed for macOS or Linux (`python` vs `python3` in the skill's commands, path forms in the rules).
- **Python 3.10** for the suite currently lives in a temporary folder; when it is gone, a task reports "3.10 not verified".

## Open questions (for Nam)

1. Is a review required for every Standard change, or only for changes under `tools/` and `skills/`?
2. Budget: 6 subagent calls, 2 review rounds, 3 fix attempts per task — right size?
3. Should the Orchestrator be allowed to fast-forward `main` after a task, or does that stay Nam's (today: Nam's, stop point 4)?
4. Should nesting be switched off for this repository (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`), so that "no subagent starts a subagent" is enforced rather than instructed?

## Trial

One small task in a **new** session (chosen by Nam: a test that keeps `docs/architecture.md` §7.1 / §7.2 in line with the commands and lint rules `pls` really has — roadmap P3-1). It shows whether a cold-start session finds and uses the team and whether the permission rules fire. It is operational evidence only: it does not accept this ADR.

## Consequences (if accepted)

- Easier: one task in, one reviewed local commit and a report out; evals and KB edits follow one path.
- Harder / costs: a review per Standard or Critical change (tokens and time); protected paths need Nam for every change, including improvements to the team itself; the briefs must be kept honest.
- Follow-up: TD-21 (hook); decide the open questions after the trial.
