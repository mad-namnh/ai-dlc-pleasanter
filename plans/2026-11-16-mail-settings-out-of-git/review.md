# Review — mail settings out of git

## Round 1 (pls-x-reviewer, opus, high) — reject

- **H1:** logical() dropping the keys removed the ADR-0001 scope refusal for them (getsite → updatesite round trip never probed) → plan_site adds a SCOPE finding for each live-only key the raw live site holds (not in VERIFIED_KEYS); `--accept-unverified` needed until a probe; test.
- **H2:** adopt `payload-<name>.json` and applied-differs `live-<site>.json` still held the addresses → both strip them; tests.
- **H3:** production package files lack the keys; checklist told the operator to apply / restore the files as they are → checklist step "before each updatesite copy the four keys from the site"; I2 / L-DEP-01 exception documented; TD-60 (deadline: before the first production release); test of the checklist text.
- **M1:** Client.apply's own getsite widened the TB-8 window → apply_release passes its re-read SiteSettings; the inner read only when none is given (restores).
- **M2:** a hand edit in site.json reached payload files → payload() strips the keys; architecture L-SEC-01 row corrected.
- **L1:** a read that timed out reported as an uncertain write; missing SiteSettings treated as none → TransportError "nothing sent" for both; test.
- **L2:** ADR-0010 note wording (pls apply and restores; kb-verify probe sites), consequences (set on the screen; drift / compare / read-back blind; scope refusal; package) and TD-59 widened to every browser-runner write path.

## Round 2 (pls-x-reviewer, opus, high) — accept with fixes; no Critical/High

- **F1 Medium (process):** ADR-0010 note and the I1 / I2 exceptions are the Orchestrator's wording of Nam's decision; an invariant exception needs his approval (stop points 1, 2) → `proposed-wording-for-nam.md`; I1 row now names the exception too. **Not committed until Nam approves.**
- **F2 Medium:** tests added — single-site `plan` (rollback.json without the keys, L-DEP-01 clean), `apply_release` reads each site twice only (preflight + re-read) and carries that read.
- **F3 Low:** `siteConfig` steps refuse the four keys (results are committed); test.
- **F4 Low:** `pls pack` prints a note on stderr; help text; TD-59 names pack output.
- **F5 Low:** `--summary` strips any scope suffix and lists a key once; test.
- **F6 Low:** inventory rows 97–100; ADR note says what happens to keys committed earlier.
- **F7 Low:** live hashes in plan.json → TD-61.
