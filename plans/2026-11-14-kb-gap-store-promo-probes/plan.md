# Plan — KB gaps G-1…G-8 of a trial design: source evidence, kb-verify extension, probes

- **Date / branch / parent commit:** 2026-11-14 / `brownfield-adr` / `d326a27`
- **Objective:** carry the KB gaps of the trial `pls-trial-store-promo` DES-001 (hand-over `design/probes/2026-11-14-kb-gap-handover.md` in that repository) through ADR-0023 steps 3–4: source-derived KB entries, and probes that `pls kb-verify` can run. Step 5 (the run on dev) is the person's; step 6 follows its report.
- **Tier:** Critical — changes the safety rules of `kb-verify` probes (ADR-0009 / ADR-0025: what a probe may write and where).
- **Nam's decisions (2026-11-14, AskUserQuestion):**
  1. scope: "Mở rộng kb-verify luôn" — extend kb-verify (update of the probe's own records, principal variables, several probe sites), with an ADR Nam approves first;
  2. roles for the G-1 probe: those of the trial store-promo (`store_a01`, `store_a02`, `promo`, `accounting`); Nam prepares the trial for kb-verify (principals, test users, `side_effects.mail`, `kb_probe_parent`);
  3. G-3 (`items.Create` in a server script): manual probe by a person; ADR-0025's script guard unchanged;
  4. read more of the Pleasanter source (tag `Pleasanter_1.5.2.0`) before writing probes — done, notes in `source-notes.md`.
- **Scope:**
  1. ADR-0026 (Proposed → Nam accepts): kb-verify probes may (a) `update` a record the probe created, (b) use `$group_<role>` for a declared role's group id, (c) own several probe sites (`sites`), refer to their ids in settings as `${probe_site:<key>}` and run steps on them (`"site": "<key>"`);
  2. `tools/pls/pls_kbverify.py`, `pls_kbverify_guarded.py`, `pls.py` kb-verify: build (1) with tests;
  3. KB (curator): source-derived entries for G-1…G-8 in `behaviours.md` (new D numbers), probes in `references/probes/`, `index.json`; G-7 into `api.md`;
  4. G-3: a written manual probe procedure (KB entry open question + steps for a person).
- **Out of scope:** running `kb-verify` (person); `VERIFIED_KEYS` (step 6, after a pass); changes in the trial repository; ADR-0025's script-name guard.
- **Files:** `docs/adr/0026-*.md`, `docs/adr/README.md`, `tools/pls/pls_kbverify*.py`, `tools/pls/pls.py`, `tools/pls/tests/test_kbverify_*.py`, `skills/pls-kb-pleasanter/**`, `skills/README.md` (KB version), `docs/review-findings.md` (new D items), `HANDOFF.md`.
- **Invariants and ADRs touched:** I5, I9; ADR-0009, ADR-0023, ADR-0025 (amended by 0026).
- **Stop points expected:** 1 (accepting ADR-0026 — Nam); 5 (kb-verify run on dev — Nam).
- **Acceptance criteria:**
  1. a probe step `update` is allowed only on a record created earlier by the same probe; `site` on a step only names one of the probe's own sites; `run_on` / `vars` stay forbidden;
  2. `$group_<role>` resolves only for a role declared in `roles` and bound on the environment;
  3. every site of a probe is created under the probe folder with its own title, proven own before any write, gets the same teardown / grant removal / deletion rules as the main site (guarded probes), and `${probe_site:<key>}` is replaced only with ids of the probe's own sites; an unknown key refuses the probe file;
  4. existing probes behave unchanged (suites green);
  5. new tests fail on the parent commit;
  6. KB entries for G-1…G-8 say "source-derived, not verified" with file and tag; probes load with `KV.load_probes`.
- **Tests:** unit tests for the loader rules (update on own record only, unknown site key, undeclared `$group_`), and fake-server runs of a multi-site probe (creation, substitution, teardown, deletion of every site). Both suites; Python 3.10 if available.
- **Subagents planned:** `pls-kb-curator` (opus, high: KB entries and probes from `source-notes.md`); `pls-x-reviewer` (opus, high: Critical change) — up to 2 rounds.
- **Documents to update in the same commit:** ADR-0026 + README, `pls_kbverify.py` docstring, KB version in `skills/README.md`, `docs/review-findings.md`, `HANDOFF.md`.
