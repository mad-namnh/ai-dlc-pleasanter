# Plan — P3-8 review standard v2.2 (design review final report §2.5)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent `37f3226`
- **Tier:** Light (one document) — but `docs/review-criteria.md` is a protected path (agent-rules stop point 3): the change is proposed as `proposed-review-criteria.md.patch`, Nam applies or rejects it.
- **Change proposed:** v2.2 header and change note; the count of criteria (65: A 6, B 11, C 11, D 6, E 4, F 4, G 6, H 6, I 6, J 5); FAIL when any part of a criterion is violated, PARTIAL only when no part is violated; one report row and one status per criterion.
- **Decision for Nam:** the FAIL/PARTIAL rule settles the WS-7 disputes D-1 (F4 → PARTIAL) and D-2 (G2 → FAIL) for the next review (HANDOFF waiting list item 6).
- **Check:** `git apply --check` of the patch on `37f3226` passes.
