# CLAUDE.md — rules for agents working in ai-dlc-pleasanter

Current phase: **test / demo stage, architecture v0.3** (after slices #1–#3). Skills P1/P2 + KB are built; tools `pls` 0.5. See `HANDOFF.md` for the next step.

**Read `docs/architecture.md` first.** Every skill, agent, hook, check or tool you build must map to a phase (P1–P6), an artifact or an invariant (I1–I9) defined there. If it does not fit, propose an ADR instead of building it. Customer-application solutions go to `patterns/`, not into the framework core.

## Mandatory

1. **Write only to dev environments.** Write operations (create/update) may run only when the target is localhost, or an environment declared with `role: "dev"` **and** `allow_write: true` in `config.json`. Never set `role: "dev"` on a customer stg/production environment. Do not modify or loosen `assert_writable` in `scripts/common.py`. Agents must not add `--yes` unless the user asks for it.
   - `pls` HTTP transport (ADR-0008): writes need environments.json `role: "dev"` or `"stg"` **and** `allow_write: true` in the operator's local `.pls/connections.json`; `role: "prod"` is never written. Do not modify or loosen `assert_writable` in `tools/pls/pls_http.py`, and never write keys into any file other than the operator's own key files under `.pls/`. The one exception is a dev test user that `pls` itself creates for role tests (ADR-0018): `pls` writes that user's password and key only into the operator's `.pls/`, never prints them, and never for `role: "stg"` or `"prod"`. Agents never read those files and never ask for keys in chat.
2. **Never hold production API keys.** Exports from customer environments are run by the customer's operator or an authorized person. Agents work only on exported files.
3. **Never commit customer data.** Everything under `spike/round-trip/data/` is gitignored. Do not copy customer configuration, site names, person names or internal URLs into any other file in the repo. Spike reports must be sanitized.
4. **Never commit secrets.** `.env`, API keys, webhook URLs and tokens stay out of git. Plain-text secrets inside Pleasanter configuration are a blocking defect (ADR-0005).
5. **Do not guess about Pleasanter.** When unsure how an API or configuration field behaves on 1.5.x, record it under "Open questions" in the relevant ADR or spike report instead of assuming.

## Conventions

- **Language: English for everything in the repository**, even though day-to-day discussion with the project owner is in Vietnamese. This applies to every new or updated file for the whole framework build:
  - documents (`*.md`);
  - code comments, docstrings, CLI help, log messages, error messages, generated reports, config comments and Terraform descriptions.
  - Exceptions:
    - Messages shown to **Pleasanter end users** (e.g. `context.AddMessage`, errors thrown from server scripts) stay in **Japanese**.
    - Pleasanter-specific Japanese terms that are UI or product labels stay in Japanese, optionally with an English gloss on first use (e.g. プロセス (process), 期限付きテーブル (time-limited table)).
- **Naming of skills and agents:** `pls-<phase>-<role>`, kebab-case, English, max 64 characters.
  - `<phase>` = `p1`…`p6` (lifecycle phase in `docs/architecture.md`); `kb` for knowledge bases; `x` for cross-phase assets.
  - Examples: `pls-p1-requirements-analyst`, `pls-p2-solution-designer`, `pls-kb-pleasanter`.
  - Skills and agents share the convention; they are told apart by folder (`skills/` vs `agents/`), not by name.
- Every architecture decision is an ADR in `docs/adr/`. No implicit decisions in code.
- New findings from spikes → update `docs/review-findings.md` (add an item or change its severity).
- Deferred work goes into `docs/tech-debt.md` with a deadline.

## Adaptive Model Routing

Applies to every task in this repository. It never overrides the Mandatory rules, gates G1–G4, ADRs or the user's explicit choice of model; when they conflict, they win.

**What can be routed (verified in Claude Code, 2026-11-10).** The main session's model is changed only by the user (`/model`, or `model` in settings); an agent cannot switch its own model. An agent *can* choose the model of each subagent it starts (Agent tool `model`: `haiku`, `sonnet`, `opus`, `fable`; a fork always inherits) and its reasoning effort (`effort`), and agent definitions carry a default model in their frontmatter. Use only these aliases; never invent model ids.

**Classify first** — complexity, risk, reasoning needed — then use the least expensive option that can reliably finish *and verify* the task:

| Tier | Work | Route |
|---|---|---|
| Light | lookups, file search, formatting, doc wording, one isolated low-risk edit | do it inline; if delegated: `haiku`, effort `low` |
| Standard | normal implementation, refactoring, multi-file changes, tests for them | inline; if delegated: `sonnet`, effort `medium` |
| Critical | architecture and ADRs, write guards (`assert_writable`), gates and approval records, secrets, permissions, migrations and data integrity, recovery states, concurrency, hard debugging, security review | strongest available (`opus` or `fable`), effort `high`; never delegated below this tier |

- **Override weak defaults.** When an agent definition's default model is below the task's tier (e.g. a `haiku` tester or researcher on Critical work), pass `model` explicitly.
- **Escalate, do not guess.** If the current model cannot solve or verify the task with confidence, re-run it one tier up. If the main session itself is below the task's tier, say so and ask the user to switch with `/model` before continuing Critical work.
- **Subagents only when they pay:** independent work that runs in parallel, or a review that must not be anchored on the author's view. Not for a handful of tool calls. Give each a narrow brief with file paths; do not repeat an analysis already done.
- **Deterministic first:** `pls` commands, lint, grep and the test suites decide what they can decide; LLM reasoning is for what they cannot.
- **Verification scales with risk:** Light — re-read the change; Standard — the affected tests while working; Critical — also an independent review when the change touches a write guard, a gate or secrets. The commit rules in `HANDOFF.md` ("How we work": full suites, new tests shown failing on the parent commit) apply to every tier and are not reduced by this section.
- **Cost never buys down correctness, security or required verification.**
- **Evals are exempt:** a skill eval runs on the model its result file records (see `HANDOFF.md`, "How we work"); do not route it to a cheaper model.

## Working as an agent team

Framework tasks are run by the main session as Orchestrator, with the skill `pls-x-dev-orchestrator` (`.claude/skills/`). Design: [ADR-0016](docs/adr/0016-agent-team-for-framework-development.md) (Accepted 2026-11-11). Rules — stop points, who writes what, scratch space, budget: [`docs/agent-rules.md`](docs/agent-rules.md).

- The Orchestrator plans, implements, verifies and commits locally itself. Three subagents (`.claude/agents/`) do only what must be separate: `pls-x-reviewer` — read-only review of a Standard or Critical change; `pls-x-eval-case-runner` — one blind eval case per call; `pls-kb-curator` — knowledge-base edits from supplied evidence.
- Nam's global rules (`~/.claude/rules`) stay in force. Where they name an agent, this repository uses:

| Global rule says | In this repository |
|---|---|
| delegate to `planner` | the Orchestrator writes `plans/<date>-<slug>/plan.md` |
| delegate to `tester` | both framework suites, run by the Orchestrator before every commit |
| delegate to `code-reviewer` | the subagent `pls-x-reviewer` |

- Reports to Nam are in Vietnamese.
