# ADR-0015 — Undoing a release that was applied successfully

- **Status:** Proposed (2026-11-11) — nothing is built; Nam decides before any code
- **Context owner:** Nam
- **Related:** I2 (complete payloads), I4 (gates), ADR-0004 (migrations), ADR-0008 (HTTP transport), ADR-0014 (TB-7, TB-8); design review 2026-11-09 D3 / WS4-F10

## Context

Every release folder holds `rollback-<site>.json`, the configuration of each site as it was when the release was planned. Today these files are used only **inside a failing `apply`**: when a site cannot be written, the sites already written are restored.

There is no guarded way to undo a release **after it was applied successfully**. The choices today are:

- the browser runner `rollbackRelease` — dev only, no guards, nothing recorded (ADR-0014 TB-7);
- a new release whose configuration is the old one — safe, but it needs the old state back in `config/` (a git revert), a plan, and the gates again;
- a person restoring the sites by hand.

The design review found that an operator therefore cannot "understand, execute and undo" a release from its folder alone.

## Options

### Option A — No undo command; undo is always a new release
- Pros: one write path; every change of an environment passes the same gates; the drift baseline stays simple.
- Cons: slow when a release must be taken back quickly; needs git work under pressure.

### Option B — `pls rollback <R>`: restore the planned rollback files, with the guards of `apply`
- Pros: fast; uses files that were approved together with the release (the G4 digest covers them); no git work.
- Cons: a second write path to keep safe; the rollback files are as old as the plan — anything changed since (by a later release, or in the UI) would be overwritten; data migrations are not undone by it.

### Option C — Option B, limited to the latest applied release of each site and to an unchanged site
- Pros: the rollback file is then exactly "the state before this release"; no later work is lost.
- Cons: more checks; a release that is no longer the latest still needs option A.

## Proposed decision (for Nam)

Option C, built as `pls rollback <R>`:

1. **Allowed only when** `plan.json` says `applied` or `applied-differs`, and for every site of the release: it is the latest applied release of that site in that environment, and the live site still equals what the read-back recorded (`readback_evidence.live_sha256`, or `live-<site>.json` for `applied-differs`). Otherwise refuse and name the site: undo is then a new release (option A).
2. **Same guards as `apply`:** role and `allow_write`, G4 outside dev (a **new** G4 record for the rollback, naming the release; the earlier G4 approved applying, not undoing), mail / jobs checks, the run-log check, confirmation at a terminal or `--yes` on the person's instruction, `UpdatedTime` read before each write.
3. **Order and recovery:** the rollback steps of the plan (reverse order); a failing restore ends `recovery-required`; a timeout ends `uncertain`; never a blind retry.
4. **Read-back:** every site is exported and compared with its rollback file; the plan becomes `rolled-back` only when all match. The release is then never applied again (a new plan is needed), and the drift baseline of each site goes back to the release before it.
5. **Not undone:** data migrations (`pls migrate <R> --rollback` is separate and needs `rollback.data` prepared by a person, ADR-0004), scheduled scripts (manual step, ADR-0012), records created by tests.
6. **prod:** not written by `pls`; the release package for the customer's operator already carries the rollback files (ADR-0003).

## Open questions

- Is a new G4 for the rollback right, or should the G4 of the release also cover undoing it (the files are bound to it)?
- `applied-differs` releases: the fold-back release usually follows quickly; should rollback be refused for them altogether?
- Should a sandbox (`dev-<name>`) be allowed to roll back without the "latest release" check?

## Consequences (if accepted)

- Easier: an operator can take a release back from its folder; the review criterion D3 is met.
- Harder / costs: a second guarded write command with its own tests (every refusal, read-back, recovery states); the drift baseline logic must understand a rolled-back release.
- Until decided: undo stays a new release (option A); `docs/tech-debt.md` TD-20.
