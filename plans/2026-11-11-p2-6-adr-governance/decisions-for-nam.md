# ADR decisions for Nam — 2026-11-11 (roadmap P2-6, design review A3)

Only Nam changes an ADR's Status line or Decision section (`docs/agent-rules.md` stop point 1). One row per ADR that is not fully Accepted, with the agent's recommendation. "Built" is what `pls` already relies on (`docs/adr/README.md`). After a decision, the README row and the ADR's Status line change together.

| ADR | Now | Built | Recommendation | Why |
|---|---|---|---|---|
| 0001 scope in git | Proposed; Decision section says "not decided — waiting for spike round 2", although round 2 results are written above it | `pls_scope` refuses plans outside the scope | **Accept option B**, writing the Decision from the round 2 results | code and ADR-0012 already rely on B; the empty Decision is the A3 finding |
| 0002 column slots | Proposed (TD-01, customer input) | ledger, L-SLOT-01, plan check | **Accept for stage `demo`**; ranges per customer stay TD-01 | the mechanism is used in every slice; only the customer ranges are open |
| 0003 production deploy | Proposed (TD-02, customer IT) | `pls package` + `verify.py` | **Keep Proposed** | depends on customer IT (waiting list item 2 of HANDOFF) |
| 0005 storage & secrets | Partially accepted (TD-03) | L-SEC-01 refusals | **Keep as is** | storage depends on the customer |
| 0007 new sites | Proposed | bootstrap, bind; slice #3, `pls-demo-contracts` | **Accept** | used end to end on dev and stg |
| 0008 HTTP transport | Proposed | default transport, `assert_writable` | **Accept**, with ADR-0021 for setup and key files | every write path depends on it; the key-file wording is settled by ADR-0021 |
| 0009 version & kb-verify | Proposed | `pls version`, `kb-verify`, version check in `release-plan` | **Accept** | built and used (KB 0.13–0.20) |
| 0010 mail & jobs safety | Proposed | `side_effects` refusals | **Accept**; mail testing on dev (AU4) stays out of scope | guards are relied on by `test` and `apply` |
| 0011 sandboxes, harvest, merge | Proposed; no team run yet | `sandbox`, `harvest`, `merge-site` | **Keep Proposed until the first run with two developers** | built but never exercised by a team |
| 0013 observability | Proposed | run log (writing commands refuse without it, P2-5), `step`, `usage` | **Accept** | P2-5 decided the failure policy; AU6 extended `usage` |
| 0014 trust boundaries | Proposed, 15 rows pending | cited everywhere | **Decide per row** (waiting list item 1); recommendation: accept TB-1…TB-15 for `demo` as written, keep the 3 open questions for `cstg` | each row already names what is not covered |
| 0015 undo an applied release | Proposed, nothing built | no | **Keep Proposed** until before `cstg` (TD-20) | not needed in demo; undo is a new release |
| 0020 gate records & approvers | Proposed (new) | yes | **Accept option C** (as built for `demo`; G4 approvers for `cstg` / `prod` decided before the first `cstg` project) | the only conflicts are the target approvers of §4 |
| 0021 setup profile, keys, overrides | Proposed (new) | as option A | **Accept option B**; P3-7 then makes the opt-in a question with default `false`; the `file:` limit becomes a tech-debt line (P2-7) | closes TB-10 / TB-11 gaps in code |
| 0022 distribution | Proposed (new) | yes | **Accept option A for `demo`**; tool pinning decided before `cstg` | works today; TB-6 records the risk |

## Also for Nam

1. **ADR-0012 (Accepted).** The "Implementation notes (2026-11-09)" were added after acceptance. Once ADR-0020 is accepted: change the Status line to "Accepted (2026-11-05); implementation notes replaced by ADR-0020 (2026-11-…)" and either remove the notes or head them "Replaced by ADR-0020". Not done by the agent (stop point 1).
2. **`CLAUDE.md` Mandatory rule 1** (A4 item 4): `plans/2026-11-11-p2-6-adr-governance/proposed-CLAUDE-md-write-rule.patch` scopes the spike-era wording to `spike/round-trip/`; `git apply --check` passes. Protected path: apply and commit it, or reject it.
3. **ADR-0004 decision 3** (review A3: bulk upsert untested): closed by roadmap P0-5 — migrations run through `pls migrate` over HTTP (`tools/pls/tests/test_migrate_over_http.py`). No decision needed.
