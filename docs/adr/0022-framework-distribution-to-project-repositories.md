# ADR-0022: Framework distribution to project repositories

- **Status:** Proposed (2026-11-11) — describes what `pls` does today; Nam accepts, changes or rejects it
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** `docs/architecture.md` §3.1, §3.2; ADR-0011 (merge driver), ADR-0014 (TB-6, TB-9); `skills/README.md` "Installing into a project repository"; review criterion I3 (`docs/review-criteria.md`); design review 2026-11-09 A2 item 7; roadmap P2-6

## Context

The framework (this repository) and each customer project are separate git repositories (`docs/architecture.md` §3.1). A project needs the framework's tool (`pls`) and a copy of its skills. Plan item D3 (2026-11-05) built `pls init`, a launcher and `pls skills check|sync` for this, without an ADR. The design review of 2026-11-09 (A2 item 7) asked for one: how a project finds the framework, which version of the skills it runs, and what is checked, decide what an operator's machine executes during every `pls` command and every merge of `config/*/site.json`.

## As built (2026-11-11, `tools/pls/pls.py`)

**Launcher.** `pls init` writes `pls.py` at the project root (`LAUNCHER`). It runs `<framework>/tools/pls/pls.py`, where `<framework>` is the environment variable `PLS_HOME`, else `path` in `.claude/framework.lock` (relative to the project). The **tool code is not copied and not pinned**: a project runs whatever the framework checkout at that path holds.

**Skills.** `pls skills sync` (also run by `pls init`) copies every framework skill folder (`skills/<name>/` with a `SKILL.md`) into `<project>/.claude/skills/<name>/`, replacing the previous copy, and writes `.claude/framework.lock`: `framework`, `path`, `commit` (short hash of the framework checkout), `synced`, and per skill its version (from `skills/README.md`) and a sha256 of the copied tree (line endings normalised). Skills are pinned per project; an upgrade is a sync and a commit in the project.

**Check.** `pls skills check` reports a skill missing from `.claude/skills/`, a project copy that differs from its lock hash (edited in the project), a framework copy that differs from the lock (newer version available), a framework skill not installed, and a lock in the old format. It does not hash tool code.

**Merge driver** (ADR-0011). `pls merge-install` writes `config/*/site.json merge=pls-site` to `.gitattributes` and registers in the clone's `.git/config` a driver that runs the project launcher's `merge-site` with the current Python — so every merge of a `site.json` runs the framework code the launcher resolves.

**Not distributed:** `.claude/skills/pls-x-dev-orchestrator` and `.claude/agents/` of the framework (they are for developing the framework, ADR-0016); the project `CLAUDE.md` comes from `templates/project/` once, at `pls init`, and is not synced afterwards.

## Open questions

- [ ] Should the tool be pinned like the skills (the lock's `commit` checked against the framework checkout, or a copy of `tools/pls` per project), so that a framework change cannot alter a project's guards silently (TB-6)? — *Nam, before the first `cstg` project*
- [ ] How does a customer-side operator get the tool for production (ADR-0003, `pls package` hands over a release and a stdlib `verify.py`, not `pls`)? — *ADR-0003*

## Options

### Option A — As built: skills copied and hashed per project; tool run from one framework checkout by path
- Pros: one checkout to update; projects pick up tool fixes at once; skills stay reviewable per project.
- Cons: a framework change (or a checkout on another branch) changes every project's guards without a commit in the project; `skills check` cannot see it (TB-6).

### Option B — As A, plus `pls skills check` (or every writing command) compares the lock's `commit` with the framework checkout and reports a difference
- Pros: small change; makes a tool change visible per project.
- Cons: every framework commit makes every project report a difference until it syncs.

### Option C — Vendor the tool into each project (copy of `tools/pls` pinned by the lock)
- Pros: a project's behaviour changes only with a commit in the project.
- Cons: fixes must be synced into every project; two copies of the guards to keep consistent.

## Decision

**Proposed: option A for stage `demo`**, with the first open question decided before the first `cstg` project (B is the smaller step if a pin is wanted).

## Consequences

- Easier: how a project finds and pins the framework is written down; review criterion I3 (`pls skills check`) has a reference.
- Harder / costs: none until B or C is chosen; B or C changes the launcher and the lock format.
- Follow-up: Nam decides the open question; `skills/README.md` "Installing into a project repository" points here once accepted.
