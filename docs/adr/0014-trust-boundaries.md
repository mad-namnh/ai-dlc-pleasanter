# ADR-0014: Trust boundaries — what `pls` enforces and what it trusts

- **Status:** Proposed (2026-11-09) — written for the design review (`docs/review-criteria.md` A6); Nam accepts or changes each boundary
- **Date:** 2026-11-09
- **Deciders:** Nam
- **Related:** I3, I4, I7 (`docs/architecture.md` §2), ADR-0003, ADR-0008, ADR-0010, ADR-0011, ADR-0012, ADR-0013; `docs/reviews/design-review-2026-11-09/`

## Context

`pls` enforces many rules in code (write guards, gate records, side-effect refusals). Some things it cannot enforce, because they happen outside the tool: who typed a command, whether a person really said the words recorded as their approval, who may edit files on the operator's machine, and what the network allows. The design review standard (A6) requires these boundaries to be written down, with the risk and an owner, so that a reviewer can tell a deliberate boundary from a missing control. Without such a record every gap is a finding "missing trust-boundary ADR".

This ADR lists the boundaries as they are on 2026-11-09. It does **not** accept gaps that code can close; those are listed separately at the end and stay findings until fixed.

## Open questions

- [ ] For a customer staging environment (`cstg`): are gate records protected beyond git (signed commits, protected branch on the remote, or a record store outside the agent's reach)? — *Nam, before the first cstg project*
- [ ] For production: the customer-side runner (ADR-0003) and its input verification — *customer IT (TD-02)*

## Options

### Option A — Enforce everything in code
- Pros: no trust assumptions.
- Cons: impossible for human intent (the tool cannot know what a person said) and for the operator's own machine (the person who can run `pls` can also edit its files).

### Option B — Write each boundary down, with owner, stage and compensating controls; close in code what code can close
- Pros: reviewable; gaps that code can close stay visible as findings.
- Cons: the boundaries hold only as long as their owners and controls do.

## Decision

**Option B (proposed).** The boundaries below are accepted **for the stage named in each row**. A later stage needs the follow-up named in the row before the boundary holds there.

| ID | Boundary | What `pls` does enforce | What is trusted | Risk if the trust fails | Owner | Compensating controls | Accepted for |
|---|---|---|---|---|---|---|---|
| TB-1 | **Operator machine and file system.** `gates/`, `releases/*/plan.json`, `CLAUDE.md` (profile), `environments.json`, `.pls/connections.json` are plain files | records written with exclusive create (`gates/`); approver names re-checked against the profile when a record is used (`pls_gate.require`); malformed files refused | that nobody (person or agent) writes these files by hand to get past a refusal | a forged gate record, a widened `allow_write`, a changed `role` or profile row lets a write through | operator (Nam on MADLAB machines) | hard rules in the project `CLAUDE.md` and `pls-x-lifecycle` §2 (never edit guards, profile or records to get past a refusal); every change is visible in `git diff` / history; run log `ops/log/` | `demo` |
| TB-2 | **CLI arguments that state a person's words** (`--approver`, `--quote`, `--by`, `--approved-by`, `--yes`) | the name must be an approver / operator in the profile for that gate or environment; the quote must not be empty; `--yes` is never implied | that the agent passes only names and words the person actually gave, in this session | the agent records an approval nobody gave (I4) | the approver named in the record; the operator who runs the agent | skills stop at every gate and every manual step and record only after the person speaks; run log records the actor; agent-behaviour evals (EV-03, EV-10) | `demo` |
| TB-3 | **Git history as tamper evidence** for records (gates, releases, run log) | nothing beyond exclusive create of gate files | that the repository history is not rewritten and that commits are reviewed | an edited or deleted record goes unnoticed | Nam (repository owner) | local commits per phase; no force-push rule; remote on GitHub for the framework | `demo` (follow-up for `cstg`/`prod`: protected remote branch or signed commits — open question) |
| TB-4 | **Environment role is a label in git, not bound to a URL** | writes only for `role` `dev` / `stg` with local `allow_write: true`; never `prod`; stg needs G4 | that `environments.json` names each URL with its real role, and that the operator's machine holds **no production key and has no network path to production** | a production URL labelled `stg` with a key present would be writable | operator; customer IT for production networks | I3: production deploys run inside the customer network (ADR-0003); keys only in the operator's environment variables / key files under `.pls/`; agents never ask for or hold keys | `demo`, `cstg` (production never reachable) |
| TB-5 | **Agent harness permissions** (Claude Code permission mode, allowed tools) | none — `pls` does not sandbox the agent | that the operator runs the agent with permissions that require confirmation for file edits and shell commands they care about | an agent with unrestricted permissions can do anything the operator can (TB-1) | operator | permission prompts; hard rules in project `CLAUDE.md` | `demo` |
| TB-6 | **Framework code integrity** (`PLS_HOME`, `.claude/framework.lock` path) | `pls skills check` hashes skills against the lock; tool code is not hashed | that the framework checkout the launcher points to is the reviewed one | modified tool code removes guards | operator | framework is a git repository; lock records the framework commit | `demo` |
| TB-7 | **Browser runner** (`tools/pls/browser/pls-runner.js`) runs in a person's logged-in browser session | none in code; header states dev/stg only, driven by a person | that a person injects and drives it only on dev/stg copies | a write (incl. `bulkupsert` migrations) to a wrong environment | the person driving the browser | ADR-0008 made the HTTP transport (guarded) the default; runner kept as fallback | `demo`, dev only (not accepted for stg with customer data) |
| TB-8 | **Pleasanter API limits**: `updatesite` has no conditional write; no API for scheduled scripts (D31) | `UpdatedTime` preflight before writing; read-back (`mark-applied`) after; manual deploy step + `jobs-verified` for scheduled scripts | that the window between preflight and write is short and that a change in it is caught by the read-back | a concurrent change is overwritten; it is detected afterwards, not prevented | Nam (framework) | post-apply round trip; drift check | `demo`, `cstg` |

**Gaps that are not boundaries** (code can close them; they remain review findings until fixed or until Nam records an explicit decision in `docs/tech-debt.md`):
- approval bound to a release id, not to the payload content (no digest in the G4 record);
- recovery status after a failed restore;
- behaviour when the run log cannot be written;
- handling of a timeout after the server has written.

## Consequences

- Easier: the review can classify each gap as an accepted boundary (with this ADR) or a finding.
- Harder / costs: every boundary must be re-checked before a later stage; TB-1, TB-2 and TB-3 carry most of the I4 risk and need stronger controls before customer data is involved.
- Follow-up: decide the open questions before `cstg`; revisit TB-7 when the e2e runner decision is made (`pls-p4-e2e-tester`).
