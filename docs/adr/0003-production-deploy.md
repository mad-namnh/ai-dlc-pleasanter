# ADR-0003: Production deployment (on-prem)

- **Status:** Proposed — customer IT input deferred (TD-02)
- **Date:** 2026-11-04
- **Related:** review-findings A3, B1, D1, D4

## Context

Production is inside the customer's on-prem network. Tenant-admin API keys are very powerful. Agent hooks are not a security boundary. Hard rule: **AI never holds production keys and has no network path to production.**

Spike round 1 showed that `updatesite` replaces the whole configuration (D4): any deploy silently overwrites customer UI edits unless drift is checked first.

## Open questions

- [ ] Will the customer allow an automated runner inside their network? Where (server, VM, self-hosted CI runner, …)? — *Customer IT (TD-02)*
- [ ] Is there an on-prem staging environment? Does it mirror production? — *Customer IT*
- [ ] Who issues API keys; what is the minimum permission needed to deploy configuration? — *Spike + customer IT*
- [ ] Allowed deployment windows; user notification procedure — *Customer*
- [ ] Will Pleasanter's built-in MCP be used in any environment (D1)? — *Customer*

## Options

### Option A — Runner inside the customer network, automated deploy after G4
- Pros: fast, repeatable, full logs
- Cons: needs customer IT approval for infrastructure; the runner must be protected

### Option B — Deploy package + manual import by the customer's operator
The framework produces a "deploy package" (packed configuration + deploy plan + checklist + post-deploy verification script).
- Pros: easy for the customer to accept; no new infrastructure
- Cons: slow, person-dependent, error-prone

### Option C — Start with B, move gradually to A
- Pros: can start immediately; builds trust first
- Cons: two flows to maintain during the transition

## Decision

*(Not decided)*

Initial proposal: **C**. The deploy package is designed so that the runner in option A consumes exactly the same package.

## Consequences

- Every deploy goes through a **deploy plan** (A3): snapshot → dependency order → apply → smoke test → restore on failure.
- Every deploy sends the **complete** configuration and is preceded by a **mandatory drift check** (D4).
- The AI working environment (MADLAB local/CI) has no route to the customer network — enforced at the network layer.
- Audit log: who approved, who ran it, which version, when.

## Note (2026-11-05)

ADR-0008 gives `pls apply` an HTTP transport with operator-local connections and keys. Option A can run exactly that command inside the customer network; the agent never holds the keys (I3).
