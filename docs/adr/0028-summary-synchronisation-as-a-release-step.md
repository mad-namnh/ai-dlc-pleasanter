# ADR-0028: Summary synchronisation as a release step (`pls summaries sync`)

- **Status:** Proposed (2026-11-16)
- **Date:** 2026-11-16
- **Deciders:** Nam
- **Related:** I2, I4 (`docs/architecture.md` §2); ADR-0004 (data-impacting changes — Decision 3 order), ADR-0008 (HTTP transport, write guard), ADR-0013 (run log); KB D16; settings coverage plan `plans/2026-11-15-settings-coverage/plan.md` WS4.1

## Context

A `Summaries[]` change (集計) does not recalculate existing destination values (KB D16). `classify` puts it in the data-impacting class with the note "migration: touch one child record per parent after the release" — a workaround that writes business records.

Pleasanter 1.5.2.0 has an API route for the recalculation: `POST /api/items/{id}/SynchronizeSummaries` (`Controllers/Api/ItemsController.cs` l.293–314, read-only clone of tag `Pleasanter_1.5.2.0`, source-derived). The screen calls the same model method (`Controllers/ItemsController.cs` l.1263). The request body (which summary, or all of the site's) and the answer are **not read**: the item model is not in the clone.

## Options

### Option A — Keep the workaround (touch one child record per parent)
- Pros: nothing to build.
- Cons: writes business records in every environment, production included; error-prone for many parents; not what the screen does.

### Option B — `pls summaries sync --env E --release R` (recommended)
- For each summary the release adds or changes (from `plan.json` classification), call `SynchronizeSummaries` on the summary's site.
- Guarded like `apply`: `assert_writable` read before every call; on a non-dev environment only after G4 for that release; typed confirmation; run log (ADR-0013); an uncertain answer is reported, never retried blindly.
- `release-plan` records it as a step after `apply` in `plan.json`, and the P5 checklist (`pls package`) names it for the customer's operator (method L) — replacing the D16 note.
- `apply` refuses to mark the release applied while a recorded sync step has not run (like `pls migrate` before `apply`, ADR-0004).
- Pros: the recalculation the screen does, per summary, with the same guards as every write; no business record touched by hand.
- Cons: a new write path (ADR-0004 Decision 3 order gains "configuration → recalculation"); the body and the answer must be probed first.

### Option C — B, but a person runs 同期 on the screen and records it with `pls step`
- Pros: no new write path.
- Cons: a manual step per summary per environment; drift between environments when one is forgotten.

## Decision

*(not decided — Nam)* Recommendation: option B, built only after a probe on dev shows the request body and that the route recalculates (option C until then).

## Consequences

- With B: ADR-0004 Decision 3 order is amended (configuration → recalculation) by this ADR when accepted; `pls_http` gains one guarded call; `test_write_guards` lists it; the P5 release-manager skill names the step (skill text → eval).
- Before building: a probe (ADR-0027 option B `settings` step, or a person's run) that adds a summary to a site with existing records, calls `SynchronizeSummaries` and reads the destination values.

## Open questions

- [ ] Request body and answer of `SynchronizeSummaries` on 1.5.2.0 — *source read of the item model, then a dev probe*
- [ ] Whether it recalculates every summary of the site or one — *same*
- [ ] Running time on many records — *first real release with a summary change (TD-27)*
