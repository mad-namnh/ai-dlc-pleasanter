# TD-67 — a DES agrees with the built change (check p3, blocking at G3)

Tier: **Critical** (gate coupling, ADR-0029 B / ADR-0020). Model: main session Opus 5.5, effort high.

## Nam's decisions (2026-11-18, AskUserQuestion)
- Working tree with the paused D40 task: "Làm song song (Recommended)" — stage only this task's hunks, suites in a clean worktree (HEAD + this change).
- Where: "p3 + chặn G3 (Recommended)".
- Scope keys: "Field mới trong DES (Recommended)" — `unverified:` entries, des-template + P2 skill + eval (approved under ADR-0029 C1).

## Design (Orchestrator's, reported)
- `pls gate G3 --release R --env <target> --item DES-…`: the DES the release ships. An approval runs the agreement check; findings refuse it unless `--accept-findings "<reason>"` (as G1 / G2).
- Baseline per site = the last release applied on `<env>` **before the earliest G2 approval of the named DES**, not one the G3 names (dev iterations during P3 stay inside the change). Change = `flat_diff(baseline payload model → config/ in git)`, then `classify`.
- Findings (item = site): a changed site no named DES has an element on; classification of the named DES on the site below `classify`; a rule id `classify` returns without an impact row in a named DES; a `pls scope` key without an `unverified` entry (probe id or decision record file) in a named DES; no baseline (first release on the env) → one finding (cannot be computed offline), the scope part still runs. A named DES without a document, or not approved at G2 → finding.
- `pls check p3 --env E --des DES-…` runs the same check (advisory); without them it says the agreement was not checked.
- `pls check p2` checks the shape of `unverified` entries.

## Acceptance criteria
1. `pls check p3 --env E --des DES-…` reports, per site of `config/` changed since the baseline above: no named DES element on the site; DES classification below `classify`; a `classify` rule id without an impact row; a `pls scope` component without an `unverified` entry; no baseline (first release); a named DES without a document or a standing G2 approval. `--env` without `--des` (or the reverse) is refused; without both, a note says the build was not compared.
2. The baseline is never a release the G3 names, nor one applied after the earliest G2 approval of the named DES.
3. `pls gate G3 … --decision approved` without `--env` or `--item`, or with findings, is refused unless `--accept-findings "<reason>"`; the record keeps the findings and the reason. Rejections and G4 are unchanged; `--env` is refused on other gates; `--accept-findings` still refused on G4.
4. `pls check p2` reports a malformed `unverified` entry (no key, both / neither of probe and decision, probe not `D<n>[a-z]`, decision not a file inside the project).
5. Every new refusal has a test; existing tests are adapted, not weakened; both suites green except failures caused by the uncommitted D40 work.
6. ADR-0029 As built, ADR-0020 amendment, architecture, tech-debt (TD-67 closed), HANDOFF, P2 / P3 / lifecycle text and versions updated in the same commit; nothing in the D40 hunks is staged.
7. (after review round 1) A DES edited since its G2 approval is a finding (G2 binds its content); `unverified` entries name a KB probe or a decision record naming the key; the G3 record keeps `env` and `release-plan` refuses a G3 for another target; a never-released site no named DES mentions is a finding.

## Files
- new `tools/pls/pls_des_agreement.py` (pure comparison); `tools/pls/pls.py` (baseline helper, check p3, gate G3); `tools/pls/pls_phase_check.py` (`unverified` shape); tests.
- docs: ADR-0029 As built, ADR-0020 (gate coupling), `docs/architecture.md`, `docs/tech-debt.md` (TD-67 closed), `HANDOFF.md`.
- skills: `pls-p2-solution-designer` (des-template, SKILL step), `pls-x-lifecycle` (G3 command, gates.md), versions in `skills/README.md`.

## Verify
Both suites in a clean worktree (HEAD + this change), Python 3.10 if listed, new tests failing on the parent, `pls-x-reviewer` (opus, high).

## Out of scope
Evals of P2 / lifecycle (already pending under ADR-0029; asked of Nam after commit). The D40 hunks in the working tree.
