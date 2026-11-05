# ADR-0002: Column-slot ranges per ownership zone

- **Status:** Proposed — customer input deferred (TD-01)
- **Date:** 2026-11-04
- **Related:** review-findings A2, B2

## Context

Pleasanter columns are fixed-type slots (Class*, Num*, Date*, Description*, Check*, Attachments*, …). The customer can add columns in the UI. If the customer and the framework allocate the same slot on the same site, the two fields overwrite each other, together with real data.

"Ownership zones" cannot be fully enforced by permissions, because customer admins can still edit anything. Real enforcement is **drift detection + pre-deploy slot-collision checks**, plus a written agreement.

## Open questions

- [ ] Number of available slots per type on 1.5.x, and how extended columns (拡張項目) behave — *Spike / manual*
- [ ] Will the customer agree to slot ranges and put them in the contract/maintenance SLA? — *Customer (TD-01)*
- [ ] Sites created entirely by the customer: does the framework track them? — *Customer*

## Options

### Option A — Fixed slot ranges per zone
E.g. MADLAB uses A–M, the customer uses N onward (per slot type).
- Pros: simple, easy to check automatically, easy to explain to the customer
- Cons: wastes slots; existing sites with mixed usage need an exception list

### Option B — The customer only uses extended columns
- Pros: never touches the standard slot range
- Cons: depends on extended-column limitations; the customer must learn a different way

### Option C — No ranges; lock slots via the allocation ledger + pre-deploy check
- Pros: flexible
- Cons: collisions are only detected at deploy time; frequent manual reconciliation

## Decision

*(Not decided)*

Initial proposal: **A for new sites, C for existing sites** (the ledger records the current state; newly freed slots are allocated by range).

## Consequences

- Project repositories need a **column-slot allocation ledger**: `site → slot → logical name → zone → status`.
- Pre-deploy check: diff slots between production and git; a slot occupied outside the ledger → block the deploy.
- Periodic drift reports to the customer, which also serve as evidence in disputes.
