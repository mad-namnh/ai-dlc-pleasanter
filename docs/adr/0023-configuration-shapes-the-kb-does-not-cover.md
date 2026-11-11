# ADR-0023: Configuration shapes the knowledge base does not cover

- **Status:** Proposed (2026-11-11) — Nam accepts, changes or rejects it
- **Date:** 2026-11-11
- **Deciders:** Nam
- **Related:** I5, I9 (`docs/architecture.md` §2); ADR-0001 (scope evidence), ADR-0006 (principals in git), ADR-0007 (new sites), ADR-0009 (version, `kb-verify`); KB `references/probes/`; `docs/plan.md` Step 4d AU1 (this ADR is its first part: configuration shapes with the existing `kb-verify`; probes with server scripts or a second user's key remain AU1); origin: project `pls-demo-contracts` P3, 2026-11-11

## Context

A design approved at G2 can need a SiteSettings shape that the KB does not describe. In `pls-demo-contracts` (Issues site, Pleasanter 1.5.2) three design elements had no KB entry: a view of records whose 契約終了日 lies between today and today + 90 days, a total of 月額 per 取引先, and a reminder mailed to a group. The rules then in force left the project four ways out, all decided inside the project:

1. a person sets the element in the UI and the agent exports it (`harvest`);
2. the agent reads the Pleasanter source on its own initiative;
3. the release plan refuses an unverified top-level key (ADR-0001) and a person writes a per-project `--accept-unverified` record;
4. an environment-specific id inside text (`[Group379]` in a reminder `To`) is carried as a per-project `${env:x}` value.

Each project would repeat the work, reach different answers, and leave nothing behind for the next project. Nam (2026-11-11): the automation must be guided by the framework, not done project by project.

What the source showed in that case (tag `Pleasanter_1.5.2.0`): `View.NearCompletionTime` with site `NearCompletionTimeBeforeDays/AfterDays` filters `CompletionTime` from today − Before to the end of today + After, with no status condition (`Libraries/Settings/View.cs`); `General.json` sets both days to 7 with a maximum of 30; `Aggregation.Types` is Count 0, Total 1, Average 2; a mail address may hold `[Group<id>]`, `[User<id>]`, `[Dept<id>]` (`Libraries/Mails/Addresses.cs`). The source answers the *shape*; it does not show what the server stores through the API, nor whether a value above the UI maximum is used. Only a probe on a server answers that.

## Open questions

- [ ] Is a site value above `General.json` `…Max` (e.g. `NearCompletionTimeAfterDays` 90 > 30) stored and used through `updatesite`? — the probe `D33` on MADLAB dev answers it for 1.5.2.
- [ ] Customer environments may change `General.json`; does the KB need a per-environment parameter check (`pls version` reads only the version today)? — later, with the first stg / prod release that relies on such a parameter.

## Options

### Option A — One procedure in the framework; a project uses a shape only after a probe passed
Order of sources when a shape is missing:
1. the KB (`pls-kb-pleasanter`);
2. canonical exports already in git for the same environment (another project's `config/`);
3. the Pleasanter source at the tag of the environment's recorded version (`Pleasanter_<app version>`), cited by file and tag; written into the KB as **source-derived, not verified**;
4. a probe in `references/probes/` (stored shape with `expect_stored`, behaviour with record tests; kb-verify's date variables take day offsets `$today+N`);
5. `pls kb-verify --env <dev>` — a write to dev, so the person runs it or names `--yes`;
6. on pass: the KB entry is verified on that version, and a new top-level key goes into `pls_scope.VERIFIED_KEYS` with the evidence; on fail: the KB says so and the design goes back to P2 (or the requirement to P1).

The project's release plan keeps refusing the key until step 6 (ADR-0001 unchanged). A person in the UI plus `harvest` is the fallback when the source does not answer. An environment-specific id inside a field (`[Group<id>]`) is mapped by `pls` (`[${principal:x}]` in git), not by a project value.
- Pros: one answer per shape for every project; evidence collected once; no relaxation of ADR-0001; skills can say exactly what to do.
- Cons: a project waits for a framework change (probe, KB, scope key) before it can deploy the element; the first project to need a shape pays for it.

### Option B — As A, but a project may deploy to dev with `--accept-unverified` citing a source-derived KB entry
- Pros: the project is not blocked while the probe is written.
- Cons: the dev round trip of one project becomes the evidence, which ADR-0001 rejects as a basis for scope; per-project acceptance records come back.

## Decision

Proposed: **Option A**. The scope refusal is the reason the framework is safe to use; option B would turn a framework gap into a project decision again.

## Consequences

- Easier: the next project that needs a near-completion view, an aggregation or a group recipient finds it in the KB; P2 can design with it; P3 builds it without a person in the UI.
- Harder: P3 of the first project stops until the framework has the probe and the evidence (here: `D33`, scope keys `NearCompletionTimeBeforeDays/AfterDays`).
- Built with this ADR (2026-11-11): date offsets `$name±N` for date variables (`pls_http._subst`); only `kb-verify` provides date variables (`$today`, `$yesterday`, …) — `pls test` and the browser runner have none, so a P4 spec passes such dates with `--var`; principals inside mail addresses of notifications and reminders (`pls_address_principals.py`; a raw `[Group<id>]` is lint L-PERM-01 and refused by `pack`; an `${env:x}` value holding such an id is L-PERM-01 too); probe `D33`; skills P2, P3 and lifecycle name this procedure.
- Follow-up: after `kb-verify` passes, `VERIFIED_KEYS` gains `NearCompletionTimeBeforeDays`, `NearCompletionTimeAfterDays` (separate commit with the report as evidence).
