# Product discovery report — a UI for AI-DLC Pleasanter

Status: **discovery exit criteria met** (2026-11-13). Discovery only — not a specification, ADR or plan. Decisions: [`decision-log.md`](decision-log.md) (Q1–Q14; H1–H5 confirmed). Facts below cite the repository. Not verified by running anything: headless Claude Code (§7.1) — the spike in §12 step 2 is the check.

## 0. Exit criteria

| Criterion | Settled by |
|---|---|
| Product identity and value | Q1, Q2 |
| Primary users and jobs | Q2, §4 |
| Core journeys | §5 |
| Interaction model | Q6 |
| UX direction | Q13, H5, §6 |
| MVP boundary | Q7, Q8, Q12, decision log "MVP boundary" |
| Deployment direction | Q9, Q10, Q11, §9 |
| Architectural constraints | H1–H4 (Q14), §8 |
| Libraries and tools worth adopting | §7.2 (frontend stack still to choose, §12 step 4) |

## 1. Executive summary

The framework today is **not an agent runtime**. It is a Pleasanter-specific lifecycle method (P1 → P6, gates G1–G4, invariants I1–I9) carried out by three parts: the deterministic CLI `pls` (stdlib Python, about 40 sub-commands, `tools/pls/`), Claude Code skills that act as role prompts (`skills/`), and plain files in each customer's project repository (`docs/architecture.md` §3.2). "Orchestration" is one interactive Claude Code session following `skills/pls-x-lifecycle/SKILL.md`.

The product opportunity confirmed so far (Q1, Q2): MADLAB engineers use the repositories each in their own way, so nobody can follow what a developer is doing, the project status or the output. The agreed direction (concept C1, §11) is a control plane plus UI where change requests are assigned and run by a worker on the developer's machine up to G3 on dev, with structured Human Requests for every point that needs a person, authenticated gate records written by the control plane, and a read-only view of releases (Q5–Q14, H1–H5). Fallback if headless runs fail the spike: C2, the same views and gates without execution.

## 2. Current framework capability map

Statuses: IMPLEMENTED, PARTIAL, DESIGNED ONLY, NOT FOUND, UNCERTAIN. Test suites were not run during discovery; counts are from `HANDOFF.md` (555 OK) and a count of 568 test functions in `tools/pls/tests/`.

| Capability | Status | Evidence | Limitations | Product implication |
|---|---|---|---|---|
| Lifecycle P1–P6 with gate stops | IMPLEMENTED (method; partly enforced in code) | `pls_gate.py` docstring; L-ONB-01; `release-plan` / `apply` refuse without G3 / G4 outside dev | Phase order is a skill instruction, not a state machine | A stable backbone for the phase axis |
| Agent orchestration | PARTIAL — prompt level, one interactive session | `skills/pls-x-lifecycle/SKILL.md` ("You are the orchestrator… You stop at every gate") | No queue, no programmatic orchestrator | Delegation needs a new runtime (H1) |
| Agent identity / agent run / work item as runtime entities | NOT FOUND | grep over `tools/`, `skills/` | Skills are prompts; a run is a person's session | The UI must not show agents "working" without a runtime |
| Claimed / running / done / verified | NOT FOUND at agent level; release level has `plan.json` status and `readback_evidence` | `docs/architecture.md` §5 P5 | — | Only releases, tests and gates have trustworthy states today |
| Gate records | IMPLEMENTED — approver, verbatim quote, release digest | `pls_gate.py`, `pls_release_digest.py`, ADR-0020 (Proposed) | Approver identity self-asserted (ADR-0014 TB-1, TB-2, TB-3) | Main gap and main opportunity (H3) |
| Audit / run log | IMPLEMENTED — JSONL schema v1 per `pls` command and step marker | `pls_log.py` docstring; ADR-0013 ("a future UI reads `ops/log/` …") | Records `pls` commands, not LLM actions; tamper evidence is git history only (TB-3) | Timeline of a CR can be built from it |
| Token usage | IMPLEMENTED | `pls_usage.py`; `pls usage report --json` (`pls.py`, help "for a UI") | Depends on the observed transcript format; numbers only | Cost per CR / phase available |
| Evidence and verification | IMPLEMENTED — coverage per environment, test results, operator diff report, read-back sha256 | `pls_report.py`; `docs/architecture.md` §7.1 | — | Evidence packs for gates exist |
| Retry / cancel / recovery | PARTIAL — release level only (apply restores on failure, migrate resumes) | `docs/architecture.md` §5 P5; ADR-0015 (Proposed) | No run cancellation | Needed with a runtime |
| API / control plane / realtime events | NOT FOUND | grep (`websocket`, `http.server`, SSE …) | CLI and files only | A read layer is needed for any UI |
| Claude Code hooks (write / secret guards) | DESIGNED ONLY (`docs/architecture.md` §7.3) | none in `templates/project/` | Guards live in `pls` code (`assert_writable`) | Headless runs need hooks / permission config (TB-5) |
| MCP servers, model adapters | NOT FOUND | — | Claude Code only; `patterns/ai-gateway` parked, not core | — |
| Secret handling | IMPLEMENTED | ADR-0005, ADR-0008, ADR-0021; L-SEC-01 | — | The UI must not weaken it |
| Parallel work support | IMPLEMENTED in records (per-actor logs, unique gate names); BUILT, unused by a team for config (`pls sandbox` / `merge-site`, ADR-0011) | `pls_log.py`, `pls_gate.py`, `docs/adr/README.md` | Shared files: `slot-ledger.json`, `traceability.json`, `environments.json`; live dev tenant shared (TB-14) | Q5 rule: no parallel CRs on one site |

## 3. Product model exploration

Explored execution levels (2026-11-13): M1 observe only; M2 observe + authenticated gate approval; M3 UI assigns, worker on the developer's machine; M4 execution on a central server. The levels stack. Leaning: M3 (H1), which includes M2. Details and trade-offs: `decision-log.md`.

## 4. Personas and jobs to be done

| Persona | Job | Today | Pain (Q2) |
|---|---|---|---|
| MADLAB engineer | Hand a CR to the AI, answer only what needs a person, review the result | Opens Claude Code in a project repo, works the lifecycle by chat | Each engineer works their own way; nothing outside the chat shows the work |
| PM / tech lead | Know where every CR stands, what it cost, what was delivered; approve gates | Asks people, reads repos or chats | No shared status, no output view, approver identity self-asserted (TB-2) |
| Customer (later) | Approve G1 / G4 | Through MADLAB people | Out of the MVP (Q8 list) |

## 5. Core journeys

1. **Assign** (PM or engineer): create CR → declare sites → conflict check (Q5) → assign to an engineer.
2. **Run** (worker): claim → run segment (`claude -p`, lifecycle skill) → ends with Human Requests or a push → next segment after answers.
3. **Answer** (engineer, PM): "Needs you" inbox → structured answers stored verbatim with the authenticated author.
4. **Approve a gate** (approver): evidence pack → approve / reject / changes requested → bot-written gate record (H3).
5. **Blocked** (PM / tech lead): scope conflict at G2 or `release-plan`, refusal, lost worker → reason and holder shown → decide.
6. **Follow** (PM): project view with the latest-release band (Q13) → CR detail → artifacts on the remote.
7. **Release** (operator, outside the product): `pls release-plan` / `pls apply` in the terminal; the product only shows the result.

## 6. UX direction

Primary object: the change request (Q13), on two axes that are never mixed (H5): phase from the repository, execution state from the control plane. Screens: W1 "Needs you" inbox (engineer's first screen), W2 CR detail (phase line, site sets declared / designed / actual, timeline from `ops/log`, artifacts, open Human Requests), W3 project overview with a read-only latest-release band. Interaction: forms, not chat (Q6). Rules: a state is shown only from an authoritative source (heartbeat for *running*, `readback_evidence` for *applied*); no percentage progress; a blocked CR always shows its reason and who holds what.

## 7. Technology and ecosystem research — *in progress*

### 7.1 Headless Claude Code and the Claude Agent SDK (checked 2026-11-13)

Sources: <https://code.claude.com/docs/en/headless>, <https://code.claude.com/docs/en/agent-sdk/overview>. What the docs say; nothing was run.

| Need of H1 (worker on the developer's machine) | What the docs say | Fit |
|---|---|---|
| Run without a person at the terminal | `claude -p` (CLI) or the Agent SDK (Python / TypeScript, "the Claude Code binary as a library") | Yes |
| Use the project's skills, `CLAUDE.md`, hooks | Without `--bare`, `-p` loads them as an interactive session does | Yes — but see risk R1 |
| Restrict what the agent may do (TB-5) | `--allowedTools` (permission rule syntax, e.g. `Bash(git diff *)`), `--permission-mode` (`dontAsk` denies anything that would prompt), `--permission-prompts none`; `-p` starts in Manual mode from v2.1.302 when nothing sets a mode | Yes |
| End the run with structured Human Requests (Q6) | `--output-format json` + `--json-schema` → `structured_output`; absent when the run ended without valid output (must be checked) | Yes — the run's last act can be the list of questions or the gate request |
| Session and cost per run | JSON result has `session_id` and `total_cost_usd` (client-side estimate) | Yes — simpler than reading transcripts; `pls usage` stays for the per-step view |
| Cancel a run | SIGINT or SDK `interrupt()` ends the turn; SIGTERM exits with 143 and leaves the turn unfinished | Yes |
| Live progress (heartbeat, timeline) | `--output-format stream-json` events, incl. `system/init`, `api_retry`, subagent messages with `parent_tool_use_id` | Yes |
| Permission request routed to a person | Agent SDK `canUseTool` callback; CLI `--permission-prompt-tool` | Possible; under Q6 the simpler rule is to deny and report |

**Risks found**

- **R1 — hooks of an untrusted checkout run.** "Without `--bare`, a `-p` session runs the hooks in a project's `.claude/settings.json` … even in a folder you've never trusted", with no trust dialog. A worker that checks out a CR branch someone else pushed runs that branch's hooks on the developer's machine, where Pleasanter keys live in `.pls/`. Mitigation candidates: the worker runs only on branches of the shared remote protected by review; hooks / settings taken from the framework, not the branch (`--bare` + `--settings`, but bare mode does not run hooks); compare `.claude/` with `framework.lock` before a run (`pls skills check` hashes skills, not settings — ADR-0014 TB-6).
- **R2 — authentication and terms. Resolved by Nam (Q15, 2026-11-13): subscription use is allowed; basis not recorded in the repository.** Original finding: "Unless previously approved, Anthropic does not allow third party developers to offer claude.ai login or rate limits for their products, including agents built on the Claude Agent SDK. Use the API key authentication methods". `--bare` never reads the subscription login. Whether an internal MADLAB tool that starts each developer's own Claude Code with their own login falls under this sentence is not answered by the page — to be confirmed with Anthropic / the company's agreement before H1 is built. With an API key, cost is pay-per-token on an organisation key.
- **R3 — Managed Agents** (Anthropic-hosted loop, optional self-hosted sandbox) exists as a third route; not evaluated. The cloud sandbox has no network path to MADLAB dev Pleasanter; a self-hosted sandbox would need a separate look.

### 7.2 UI libraries, protocols and reference products (checked 2026-11-13)

License, last push and latest release from the public GitHub API on 2026-11-13; nothing installed. The frontend stack itself is a Phase E question (React SPA or server-rendered pages from a Python service), so library verdicts are conditional on it.

| Candidate | Kind | License · activity · latest release | Fit with the decisions so far | Verdict |
|---|---|---|---|---|
| React Flow (`xyflow/xyflow`) | library — node graphs | MIT · 2026-11-12 · `@xyflow/svelte@1.7.1` (2026-11-02) | The lifecycle is a fixed line P1…P6 with four gates, not a graph users edit or explore; a graph would invite a second workflow model in the UI | **Reject for the MVP**; reference only |
| shadcn/ui | component registry (code copied into the app, on Radix or Base UI) | MIT · 2026-11-12 · `shadcn@4.23.0` (2026-10-27) | Tables, forms, badges, dialogs are what W1–W3 need; owned code, no runtime dependency on a vendor | **Prototype** if the stack is React |
| Radix Primitives / Base UI | accessible headless primitives | MIT · 2026-10-14 (no GitHub release) / MIT · 2026-11-13 · `v1.9.0` | Accessibility of forms and dialogs (Human Requests) | Chosen together with shadcn/ui, not separately |
| assistant-ui, CopilotKit | chat / copilot UI for agents | MIT · active (`assistant-ui@0.0.129`, `v1.87.1`, both 2026-11-12) | Q6 removed free chat | **Reject**; reference for how agent steps are shown |
| AG-UI | event protocol agent ↔ UI | MIT · 2026-11-12 | Our UI talks to the control plane, not to agents; the control plane's own events come from git + worker heartbeats | **Reference only** (event naming, interrupt / human-in-the-loop events) |
| Storybook | component workshop and tests | MIT · 2026-11-13 · `v10.6.7` (2026-11-10) | Useful once there is a component set; not for a one-machine demo | **Later** |
| htmx | hypermedia for server-rendered pages | GitHub API reports `NOASSERTION` (license to read in the repo) · 2026-11-12 · `v4.0.1` | The framework is Python; server-rendered pages keep one language and no client state (UI never authoritative) | **Prototype candidate** for Phase E, against React |
| Argo CD | product (GitOps) | Apache-2.0 · `v3.6.1` | Desired state in git vs live state, sync and drift status — the same model as I1 / `pls drift` | **Study UX** |
| GitHub Actions deployment approvals ("required reviewers" on environments) | product feature | — | Authenticated approval that blocks a run, with history — the shape of a gate Human Request | **Study UX** |
| GitHub Copilot coding agent / Agent HQ | **overlapping product** | — | Assign an issue to an agent → draft PR → review requested; the requester cannot approve the PR; Claude available in Agent HQ (secondary source). Runs in GitHub's cloud: no network path to MADLAB dev Pleasanter, no `.pls/` keys, no G1–G4 | **Study UX; not a substitute** |
| Backlog API, Git webhooks, official Backlog MCP server, `bee` CLI (Nulab, MIT, 2026) | integration surface of the company's tracker | — | Issues, pull requests and push webhooks are reachable by API, MCP and CLI | **Reference** for the later move from GitHub to Backlog |

Sources: <https://github.blog/ai-and-ml/github-copilot/assigning-and-completing-issues-with-coding-agent-in-github-copilot/>, <https://github.blog/2026/02/whats-new-with-github-copilot-coding-agent/>, <https://learn.microsoft.com/en-us/training/modules/github-copilot-code-agent/3-assign-track-troubleshoot-copilot-code-agent-tasks>, <https://support.nulab.com/hc/en-us/articles/8752305095577-How-to-set-up-Git-webhooks-in-Backlog>, <https://glama.ai/mcp/servers/nulab/backlog-mcp-server/tools/add_pull_request>, <https://atmarkit.itmedia.co.jp/ait/articles/2609/03/news027.html>.

Not yet covered: timeline components, admin templates, Figma resources, Claude Code plugins / MCP servers for the developer workflow, accessibility test tools.

## 8. Architecture options — *in progress*

Constraints so far: no second workflow engine in the UI; UI state is never authoritative; worker never writes gate records (H3); no Pleasanter keys and no Claude credentials on the server (Q10); movable from one machine to AWS (Q11); plain git, not GitHub-only APIs, for anything the core depends on (Q9).

**Smallest architecture that fits (hypothesis, not a decision):**

```
 Browser ──HTTP──► Control plane (one service + one database)
                     │  execution state: projects, members, CRs (3 site sets),
                     │  run segments, Human Requests, heartbeats
                     │  reads artifacts from its own clone of the project remote
                     │  (git fetch; `pls … --json` read-only where it exists)
                     │  writes gate records as a bot commit (H3)
                     ▲
                     │ worker polls (outbound only: works behind NAT, Japan + Vietnam)
 Developer machine: worker ──► `claude -p` + project skills, `--allowedTools`,
                     `--json-schema` for Human Requests ──► `pls` (keys in .pls/)
                     └─► pushes the CR branch to the shared remote
```

- Phase axis is derived from repository artifacts; the control plane stores only execution state (H4, H5).
- The worker pulls work; nothing connects into a developer machine.
- `pls` is reused as the deterministic reader where it can be (`pls usage report --json` exists; coverage, gate and release status have no JSON output today — a framework change).
- Database: SQLite on one machine is enough for the pilot; a managed database on AWS later.
- Realtime: polling is enough for the pilot; server-sent events when needed.
- Log-in: GitHub OAuth fits the pilot (GitHub remote); the company log-in later.
- Frontend: React + shadcn/ui or server-rendered pages + htmx — open (§7.2).

## 9. Deployment model comparison

| Model | Security | Fit | Status |
|---|---|---|---|
| Local-first (everything on one machine) | Best; no shared state | No team view | Pilot host only (Q11) |
| Centralized execution (M4) | Server holds Pleasanter keys (against ADR-0008 / ADR-0021, TB-15) and needs a path to on-prem customers | Rejected for now | Rejected |
| **Hybrid: central control plane + workers on developer machines** | Keys and Claude credentials stay on developer machines (Q10); control plane holds CRs, answers, identities | Team view + local execution | **Direction**: pilot on the tech lead's machine with GitHub (Q9, Q11), then AWS |

## 10. Risks, assumptions and open questions

See `decision-log.md`, "Unresolved questions".

## 11. Product concept candidates

The decisions narrowed the field; the three concepts below stack (C2 ⊂ C1 → C3) rather than compete.

| | **C1 — CR workspace with local workers** (leading) | **C2 — Visibility and gate console** (fallback) | **C3 — AI layer on the tracker** (after the pilot) |
|---|---|---|---|
| Users | Engineers, PM / tech lead | PM / tech lead, approvers | Same as C1, inside Backlog |
| Main value | Everyone runs CRs the same way; status, cost and output visible | Status, cost and authenticated gates without running anything | No second place to follow work |
| Journeys | 1–7 | 4, 6, 7 (engineers keep working in the terminal and push) | 1–7, with the CR = an issue |
| Core capabilities | Control plane, worker, Human Requests, bot gate records, read of artifacts | Control plane reading the remote; authenticated gate records | C1 + tracker integration (API, webhooks, MCP / `bee`) |
| UX | W1–W3 | W3, W2 without run controls, gate forms | W1–W3 embedded or linked from issues |
| Technical implications | Headless Claude Code (§7.1), R1, R2, framework changes (structured P1 questions, `--json` status) | No runtime; standardisation only by convention (pushes, `pls step`) | Two trackers (GitHub, Backlog) |
| MVP boundary | Decision log "MVP boundary" | C1 minus items 2, 3, 5, 7 | not in the MVP |
| When | Default path | If H1 fails in the spike or R2 / R1 cannot be solved | Before going beyond the pilot (Q12) |

## 12. Recommended next discovery steps

Before a product specification or implementation plan:

1. ~~R2 — confirm subscription use~~ — **done**: allowed (Nam, Q15).
2. ~~Spike H1~~ — **replaced** (Q16): headless runs are known from framework work. The first build task checks what is still unproven: ending a run with `--json-schema` Human Requests, a second segment from repository state only, and R1.
3. **Paper test of W1–W3** with one or two engineers and a PM: do they read the two axes correctly; does "Blocked" explain itself.
4. **Decide the frontend stack** (React + shadcn/ui or server-rendered + htmx) by who will maintain it.
5. **ADRs to propose** (Critical items need Nam's decision): control plane writes gate records under an authenticated user (I4, ADR-0020, ADR-0014 TB-2); run segments vs ADR-0013 "one session per change request"; P1 interview as structured questions; JSON output for status commands of `pls`; hook / settings trust of a worker checkout (R1, TB-6).
6. **Tracker overlap** (Q12): decide before the product goes beyond the pilot.
