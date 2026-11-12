# Plan — P3-7 setup opt-in, setup.md, per-site guard (design review G6, WS2-F6, WS2-F8; ADR-0021 option B)

- **Date / branch:** 2026-11-12 / `brownfield-adr`; parent `9dc2eae`
- **Tier:** Critical — write guard (`allow_write` default, guard re-validation in `apply`). Main session on Opus; review by `pls-x-reviewer` on `opus`, effort high.
- **Nam's decision (2026-11-12):** ADR-0021 option B accepted (AskUserQuestion answer "Accept option B (Recommended)").
- **Change:**
  1. `pls setup` asks the write opt-in (default no), stores `allow_write` + `allow_write_answered`; `pls init` writes `allow_write: true` only from an answered yes; old profiles count as false; `connections.example.json` false.
  2. `apply_release(…, guard)`: before every site write, after the re-read, `guard()` reloads `environments.json` and the connection and runs `assert_writable`; on refusal nothing more is written and nothing is restored (`refused` when nothing was touched, else `recovery-required`).
  3. `docs/setup.md`: the opt-in question, environment variables, a recovery table per release status. ADR-0021 Status / Decision with Nam's words; ADR index; TD-35, TD-39 (`file:` limit), TD-36, HANDOFF.
- **Out of scope:** the `file:` key-path limit (TD-39); the browser runner (person-only fallback, ADR-0014 TB-7); migrate / bootstrap / test multi-step guard re-checks (single-site writes or record writes — not named by the finding).
- **Acceptance criteria:** 1. no path writes `allow_write: true` without the person's answer; 2. a guard that stops holding mid-release stops the next site, writes nothing more; 3. existing guards unchanged or stricter; 4. tests fail on the parent; suites green (3.10 too); 5. docs as above.
