# A configuration shape the KB does not cover (ADR-0023)

Use this when a design element needs a SiteSettings property, value or behaviour that `pls-kb-pleasanter` does not describe — in P2 (designing) or P3 (building). It is a **framework** step: the answer is recorded once, in the framework, for every project. A project never settles it on its own.

## Order of sources

| # | Source | What it gives | Who |
|---|---|---|---|
| 1 | `pls-kb-pleasanter` (`schema.md`, `behaviours.md`, `skeletons.md`) | verified shape and behaviour, with the version | you |
| 2 | canonical exports already in git for the **same environment** (`config/<site>/site.json` of another project on that server) | a stored shape, as Pleasanter wrote it | you |
| 3 | Pleasanter source at the tag of the environment's recorded version — `https://github.com/Implem/Implem.Pleasanter`, tag `Pleasanter_<app version>` (e.g. `Pleasanter_1.5.2.0`; the version comes from `pls http-check`) | the shape (class fields, enums, defaults in `App_Data/Parameters/*.json`) and how it is evaluated | you, read only; send nothing about the project |
| 4 | a KB probe `skills/pls-kb-pleasanter/references/probes/<D…>.json` | an executable check: `expect_stored` for the stored shape, record tests for the behaviour (dates: `$today+N`, `$today-N`) | the framework (KB curator), from the source evidence |
| 5 | `pls kb-verify --env <dev>` | the result on the server | **the person** runs it, or names `--yes` for that dev environment (it creates probe sites) |
| 6 | KB entry verified on that version; a new top-level key in `tools/pls/pls_scope.py` `VERIFIED_KEYS` with the evidence | the project may use it | the framework, then `pls skills sync` in the project |

What step 3 gives is written into the KB as **source-derived, not verified**. It is enough to design with (P2: say it is pending verification, and keep the branch that is safe if it fails), not enough to deploy: until step 6, `release-plan` refuses a new top-level key (ADR-0001), and you do not ask for `--accept-unverified`.

## What you do not do

- Guess a property name or value, or copy one from a forum or a manual of another version.
- Ask the person to set it in the UI as the first step. A person in the UI plus `pls harvest` is the fallback only when the source does not answer.
- Put an environment-specific id inside text into `${env:x}`. Ids belong in `environments.json` principals and sites: a mail address token `[Group<id>]` / `[User<id>]` / `[Dept<id>]` is written `[${principal:<name>}]` (pls maps it both ways).

## When the probe fails

The KB records that the shape does not hold on that version (or what it does instead). The design element goes back to P2/G2; if no mechanism remains, the requirement goes back to P1/G1 — as the design's open point said.

## Example (`pls-demo-contracts`, 2026-11-11)

"契約終了日 from today to today + 90": not in the KB (1), not in any export on that server (2); source at `Pleasanter_1.5.2.0` (3): `View.NearCompletionTime` + `NearCompletionTimeBeforeDays/AfterDays`, `General.json` maximum 30 → probe D33 checks whether 90 is stored and used (4–5); scope keys only after it passes (6).
