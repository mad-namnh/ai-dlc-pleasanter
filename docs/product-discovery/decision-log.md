# Product discovery — decision log

Discovery of a product (UI + control plane) on top of the AI-DLC Pleasanter framework. Discovery only: nothing here is a specification, an ADR or a plan. Every confirmed decision is Nam's, in the discovery conversation of the date given. Report: [`discovery-report.md`](discovery-report.md).

## Confirmed decisions

| ID | Date | Question | Decision | Consequence |
|---|---|---|---|---|
| Q1 | 2026-11-13 | Pleasanter-specific product or a generic AI software factory? | **A UI for AI-DLC Pleasanter.** Not a generic factory | The framework's differentiators (round trip, drift, slot ledger, gates, KB) are reused; no generic task / agent runtime model |
| Q2 | 2026-11-13 | First users and their job | **(a) MADLAB engineers delegating work to AI; (b) PM / tech lead following progress and cost.** Stated pain: everyone uses the repository their own way, so nobody can follow what a developer is doing, the project status or the output produced | The problem is standardisation and visibility, not autonomy for its own sake |
| Q5 | 2026-11-13 | Two change requests (CRs) touching the same site | **(c) Not allowed in parallel; checked when the CR is assigned** | Scope is known only roughly at assignment, so it is re-checked at G2 (designed sites) and at `release-plan` (actual sites); a conflict found later puts the CR in *Blocked* with the reason and the holder. A CR keeps three site sets: declared, designed, actual |
| Q6 | 2026-11-13 | Where does a run that needs a person get its answer? | **(b) Structured Human Requests in the UI** (questions, gate decisions, confirmations, blocked notices). No free chat; no resuming the session in a terminal | A run ends at each Human Request; the next run segment starts a new headless session that reads state from the repository (`skills/pls-x-lifecycle/SKILL.md` §1 already requires this). The P1 interview must emit structured questions (skill change + eval). Answers are stored verbatim with the authenticated author. No chat UI library needed |
| Q7 | 2026-11-13 | PM view: one project or many? | **(c) One project in the MVP; data model ready for a portfolio** | Minimal readiness only: `project_id` on every control-plane record and per-project membership; nothing built for the portfolio itself |
| Q8 | 2026-11-13 | Where does an AI run stop in the MVP? | **(a) At G3, on dev only** (P1→P4, apply to dev). Release to stg stays with the operator in the terminal (`pls release-plan`, `pls apply`) | No change to any write guard; the UI still shows releases from `plan.json` / `apply-log.json`. Prod is outside every option (I3, ADR-0003) |

| Q9 | 2026-11-13 | Where the shared project remote lives for the pilot | **GitHub for the pilot.** The company's git today is Backlog's git; GitHub is a temporary choice for the pilot | The design must not depend on GitHub-only features without a fallback for Backlog git (later migration). Pilot projects use demo / synthetic data unless a customer allows GitHub. Where the control plane runs for the pilot is still open |

| Q10 | 2026-11-13 | Which account the worker uses to call Claude | **(b) each developer's own Claude Code subscription, or (c) Amazon Bedrock.** Not an organisation API key | The control plane never holds Claude credentials: the worker uses whatever the developer's Claude Code is configured with. Option (b) needs confirmation that the Agent SDK sentence on claude.ai login does not cover this internal use (report §7.1 R2); until then (c) is the safe route. Subscription login is not read in `--bare` mode, so runs are non-bare and risk R1 (hooks of the checkout run) must be handled. Cost shown to the PM is tokens (and the client-side estimate), not money: a subscription has no per-run price and Bedrock bills through AWS (consistent with ADR-0013: `pls usage` computes no money) |

| Q11 | 2026-11-13 | Where the control plane runs for the pilot | **(c) On the tech lead's machine, one demo project.** The intended target afterwards is **AWS** | Demo data only. The control plane must be movable to AWS without redesign (no machine-specific paths; configuration by environment). Authenticated log-in is kept even on one machine, because authenticated gate approval (H3) is part of what the pilot must prove. AWS as the target fits Q10 (c) Bedrock |

| Q12 | 2026-11-13 | Where a CR lives | **(c) A CR is the product's own object in the pilot; integration with the tracker (GitHub Issues now, Backlog later) comes later** | The overlap risk with the company tracker (two places for the PM to follow) is deferred, not resolved: it must be decided before the product goes beyond the pilot. Minimal readiness only: a CR may carry an optional link to an external issue; no sync |

| Q13 | 2026-11-13 | Unit in which the PM sees output | **(c) The CR is the centre; a read-only "latest release" band on top of the project view** | Confirms the CR as primary object (H5). Release data is read from `releases/*/plan.json` and `apply-log.json` only; the product does not run releases (Q8) |

| Q14 | 2026-11-13 | Architecture hypotheses H1–H4 | **Confirmed** as stated below (H5 confirmed by Q13) | Discovery exit criteria met (report §0). H1 still depends on the spike and on R2; if either fails, concept C2 is the fallback |

| Q15 | 2026-11-13 | R2: may each developer's subscription drive the worker's headless Claude Code? | **Allowed** (Nam's statement; the basis — Anthropic answer or company agreement — is not recorded in the repository) | Q10 (b) is usable; Bedrock (c) stays the route for AWS |
| Q16 | 2026-11-13 | Spike of headless runs (report §12 step 2) | **Not needed as a separate spike:** Nam ran Claude Code headless many times while building the framework (no record of those runs in the repository) | Still unproven and to be checked in the first build task: a run that ends with Human Requests through `--json-schema`, a second segment that resumes from repository state only, and R1 (hooks of a worker checkout) |

## Architecture hypotheses — confirmed 2026-11-13 (H5 by Q13, H1–H4 by Q14)

| ID | Hypothesis | Basis | What would change it |
|---|---|---|---|
| H1 | **Execution level M3:** the UI assigns work; a worker on the developer's machine claims it and runs Claude Code headless; Pleasanter keys stay in the operator's `.pls/` | Nam "leans towards M3" (2026-11-13); keeps ADR-0008 / ADR-0021 key custody | Headless Claude Code cannot be restricted (TB-5) or cannot stop cleanly at a Human Request |
| H2 | One shared remote repository per project; workers push CR branches | Nam's proposal (2026-11-13); framework records are merge-friendly (`pls_log.py` one file per day and actor, `pls_gate.py` unique record names, one usage file per session) | Customer hosting rules for project repositories |
| H3 | **Gate records are written by the control plane** under the authenticated user, not by the worker | Closes ADR-0014 TB-2 (approver name and quote are self-asserted today); git hosts cannot reliably restrict who writes a path on a branch | An ADR decides otherwise; needs an ADR either way (I4, ADR-0020) |
| H4 | Two sources of truth: **git** for artifacts (REQ, DES, config, tests, releases, gates, run log); **control-plane store** for execution state (assignment, claimed, running via heartbeat, waiting, blocked, failed, cancelled, site leases) | Avoids a second workflow engine; the UI says "done" only when the artifact is on the remote | — |
| H5 | **The CR is the primary object**, shown on two axes that are never mixed: phase (P1…P6, G1…G4, from the repository) and execution state (from the control plane). No percentage progress bars (no data supports them) | Framework state model (`docs/architecture.md` §3.2, §4) | User tests of the wireframes |

## Rejected alternatives

| Alternative | Rejected by | Reason |
|---|---|---|
| Generic AI software factory | Q1 | Not supported by the repository; loses the Pleasanter differentiators |
| Free chat with a run | Q6 | Conversation content through the server; harder to audit |
| Developer resumes the session in a terminal | Q6 | Reintroduces "everyone their own way"; PM cannot take part |
| Site lease on shared dev / per-developer sandboxes for parallel CRs | Q5 | Chosen: no parallel work on one site |
| Portfolio view in the MVP | Q7 | Deferred; data model only |
| AI-run release to stg from the UI in the MVP | Q8 | Would change the write guard (TB-2, ADR-0008): Critical, ADR |
| Execution on a central server (M4) | not chosen (H1) | Server would hold Pleasanter keys (against ADR-0008 / ADR-0021, TB-15), shared dev tenant (TB-14), network path to on-prem customers |

## MVP boundary (proposed, Q8 settled item 11)

In: CR list and detail per project (two axes); assignment with declared sites and conflict check; worker claim / run segments / heartbeat / stop at Human Request; Human Requests for clarification and G1–G4 approval with authenticated identity; scope re-check at G2 and `release-plan`; token cost per CR and phase (`pls usage report --json`); cancel a run.
Out: customer log-in (G1 / G4 by the customer); notifications; portfolio; AI-run stg release; prod; automatic retry.

## Unresolved questions

- Where the control plane runs for the pilot (remote settled by Q9: GitHub).
- Which git features of the control plane (bot account, branch protection, webhooks) also exist on Backlog git, for the later migration.
- Customer rules for where a project repository may be hosted (README: "wherever the customer allows").
- Headless Claude Code on the developer's machine: the docs support every need of H1 (report §7.1); not yet tried. Open: R1 (hooks of an untrusted checkout), R2 (subscription use — Nam to confirm with Anthropic / the company agreement).
- Tenant-level shared resources on dev (groups, scheduled scripts, test users; TB-14) are not covered by the Q5 rule.
- Sites linked by `${site:x}`: a CR on site B can break site A without touching it (`pls xref` / `pls refs` hold the data).
- Customer edits on stg (drift) bypass CR assignment.
- How the worker writes verbatim answers with the author's identity into `requirements/sources/` without trusting the worker for that identity.
- ADR-0013 rule "one session per change request" becomes "a session never mixes two CRs".
