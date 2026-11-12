# Plan — P3-4 every KB row has an id, a version and its evidence (design review F1, WS4-F13)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent = the P3-3 commit
- **Objective:** each row of `behaviours.md` has an ID, the version it holds on (or says it is not a server behaviour / source-derived), its evidence, and for probed entries what the probe contained and did not cover; `api.md`, `schema.md`, `skeletons.md` say what their file-level "verified on 1.5.2" rests on; a test keeps it so.
- **Tier:** Standard — KB text (curator) and one structural test; no behaviour claim may be added without evidence.
- **Evidence supplied:**
  - the two rows without ID: "Adding a new status" is a design rule (no server claim); "Server script time limit ~10 s": Pleasanter source, tag `Pleasanter_1.5.2.0`, `Implem.Pleasanter/App_Data/Parameters/Script.json` (read 2026-11-12): `ServerScriptTimeOut: 10000`, `ServerScriptTimeOutChangeable: false`, `ServerScriptTimeOutMin/Max` 0 / 86400000, `ServerScriptHttpClientTimeOut: 100000` — source-derived, not observed on a server; what happens to the save on timeout is not in that file (open);
  - probes: `references/probes/*.json` and `index.json` (contents of each probe are the evidence of what it contained);
  - each row's own text (slice / probe / spike ids already cited);
  - file history: `git log` of `api.md`, `schema.md`, `skeletons.md` (slices #1–#3, spike round 1, BR probes).
- **Change:**
  1. KB (curator): IDs D34 (status impact — design rule), D35 (server-script timeout — source-derived); for every probed entry a "Probe contained / not covered" sentence from its probe file; rows without a version state it; file headers of `api.md`, `schema.md`, `skeletons.md` state the evidence the file-level claim rests on and that a row naming its own D-entry / probe has that evidence instead. `docs/review-findings.md` rows D34, D35.
  2. Test `test_kb_rows_have_id_version_and_evidence.py`: every table row of `behaviours.md` has an ID `D\d+[a-z]?`, a version (`1.5.x`) or one of the markers "design rule" / "source-derived"; each entry with a probe in `index.json` names what its probe contained.
- **Acceptance criteria:** 1. no row without ID; 2. the test passes and fails on the parent; 3. no new behaviour claim without evidence (reviewer checks against probe files); 4. KB version bumped; TD-36, HANDOFF, register updated; 5. suites green.
- **Subagents:** `pls-kb-curator` (sonnet, medium — many rows, judgement on wording), `pls-x-reviewer` sonnet/medium.
