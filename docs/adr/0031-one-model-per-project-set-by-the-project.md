# ADR-0031: One model per project, set by the project, not by the developer

- **Status:** Accepted (2026-11-18, Nam: "1a, 3a" and "a" for the model) — team rollout decision N13, phase 5
- **Date:** 2026-11-18
- **Deciders:** Nam
- **Related:** team rollout plan `plans/2026-11-18-team-rollout-after-freeze/plan.md` (N13, phase 5); ADR-0029 C (project hooks); ADR-0030 (evals); `CLAUDE.md` "Adaptive Model Routing" (the framework repository's own work, not project sessions)

## Context

The skills a project runs (P1 … P6, lifecycle, onboarding, spec-recovery) were evaluated on one model, `claude-opus-5-5` (every result in `evals/results/` names it). With a team, each developer could run a phase on whatever model they pick (`/model`), and the output of a phase on an unevaluated model is not known to meet the rubric — the opposite of consistent output. The decision is the project's, not the developer's.

What Claude Code offers (official documentation, code.claude.com/docs, read 2026-11-18 by two `claude-code-guide` lookups, plan log of phase 5):
- skill frontmatter `model:` applies only to the rest of the current turn; the session model comes back with the next prompt;
- `model` in a project's `.claude/settings.json` is the default model of every session in that project; `/model` can still change it for a session;
- a `PreModelSwitch` hook (Claude Code v2.1.251 or later) runs before `/model`, the model picker, `/config` and an SDK `set_model`; `permissionDecision: "deny"` cancels the switch and shows the reason to the person; a timeout blocks the switch; automatic fallbacks and a session resume do not fire it; `to_model` is the target model ID;
- subagent definitions take their own `model`.

## Open questions

- [ ] Whether a phase may move to a cheaper model (e.g. onboarding, P4 on `sonnet`): decided after the team trial (phase 10) from `pls usage` numbers per phase, with that phase's evals run again on the new model; it needs phases run as subagents (option B). — *Nam, after phase 10*
- [ ] Whether `claude --model` at launch fires `PreModelSwitch`: not documented; observed in the trial (phase 10).

## Options

### Option A — The project's settings name the model; a PreModelSwitch hook denies any other
- Pros: one setting per project, written by `pls init` / `pls hook install`; the developer cannot switch by accident; small.
- Cons: one model for every phase (no per-phase choice); the hook is a guardrail inside Claude Code (a person can still edit the settings file or run without hooks).

### Option B — Each phase runs as a subagent whose definition names its model
- Pros: a model per phase.
- Cons: the lifecycle is redesigned around subagents; every phase evaluated again as a subagent.

### Option C — `model:` in each skill's frontmatter
- Pros: no settings.
- Cons: the override lasts one turn only; a phase spans many turns.

## Decision

**Option A** (Nam, 2026-11-18: "1a", "3a", and "a" for the model): `pls init` and `pls hook install` write `"model": "opus"` into the project's `.claude/settings.json` when it names none (a model the project already set is kept), with the effort left at the model's default — the setting the evals ran with. The project hook `pls hook model` (PreModelSwitch) denies a switch to any model outside the configured one: a family alias (`opus`, `sonnet`, `haiku`, `fable`, also with a context suffix such as `opus[1m]`) allows every model ID of that family; a model ID (`claude-opus-5-5`, with a context or date suffix) allows only itself; a stronger model is denied too. A setting of another form (`opusplan`, a gateway name) is not checked — the hook never locks a project out of every model; an empty or non-string `model` is replaced by `opus` on the next `pls hook install`. The model is changed only by a commit to the project's settings, decided by the G4 owner; the agents' PreToolUse hook already denies edits of `.claude/settings*.json`.

## Consequences

- Easier: every phase of every developer runs on the evaluated model; the cost question is answered with numbers after the trial, not guessed.
- Harder / costs: Opus for every phase (about twice Sonnet's price per token; on subscription plans, usage limits are reached sooner); the hook fails open on an unreadable event or settings file (a guardrail, like the other project hooks), and it does not see `--model` at launch (not documented).
- Follow-up: phase 10 checks the hook on a real Claude Code session; the per-phase question above is decided after it.
