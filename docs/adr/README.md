# Architecture Decision Records

"Status" is the ADR's own Status line; only Nam changes it (`docs/agent-rules.md` stop point 1). "Built and relied upon" says what `pls` and the skills already do on the basis of the ADR, so an ADR that is Proposed but in use is visible. Decisions still open for Nam on 2026-11-11: `plans/2026-11-11-p2-6-adr-governance/decisions-for-nam.md`.

| ADR | Topic | Status | Built and relied upon |
|---|---|---|---|
| [0001](0001-config-scope-in-git.md) | Scope of configuration managed in git | Proposed — spike round 2 results written; Decision section still "not decided" | yes: `pls_scope` refuses a release plan with a property outside the round-trip scope |
| [0002](0002-column-slot-allocation.md) | Column-slot ranges per ownership zone | Proposed — customer input deferred (TD-01) | yes: slot ledger, L-SLOT-01, plan check |
| [0003](0003-production-deploy.md) | Production deployment (on-prem) | Proposed — customer IT input deferred (TD-02) | partly: `pls package` + stdlib `verify.py` for the customer's operator; the customer-side apply method is open |
| [0004](0004-data-impacting-changes.md) | Data-impacting changes & dedicated gate | Accepted (2026-11-05) | yes: migration folder required by `release-plan`; `pls migrate` over HTTP, before apply |
| [0005](0005-config-storage-and-secrets.md) | Configuration storage & secrets policy | Partially accepted (runtime secrets); storage deferred (TD-03) | yes: L-SEC-01 refusals in `unpack`, `harvest`, `release-plan` |
| [0006](0006-site-permissions-in-git.md) | Site permissions in git (opt-in, logical principals) | Accepted (2026-11-05) | yes |
| [0007](0007-creating-new-sites.md) | Creating new sites: skeleton bootstrap, then the normal release | Proposed (2026-11-05) | yes: `bootstrap-plan`, `bootstrap`, bind |
| [0008](0008-http-transport.md) | HTTP transport with local connections (no browser in the loop) | Proposed (2026-11-05) | yes: the default transport; write guard `assert_writable` |
| [0009](0009-version-detection-and-kb-verification.md) | Pleasanter version detection and executable KB verification | Proposed (2026-11-05) | yes: `pls version`, `kb-verify`, version check in `release-plan` |
| [0010](0010-mail-and-job-safety-outside-production.md) | Mail and scheduled-job safety outside production | Proposed (2026-11-05) | yes: `side_effects` refusals in `test` and `apply` |
| [0011](0011-parallel-development-sandboxes-harvest-merge.md) | Parallel development: sandboxes, harvest and semantic merge | Proposed (2026-11-05) | yes, not yet used by a team: `sandbox`, `harvest`, `merge-site`, `merge-install` |
| [0012](0012-scheduled-server-scripts-scope.md) | Scope of scheduled (background) server scripts | Accepted (2026-11-05) — option B: files in git, manual deploy, person verifies (no API). Notes added on 2026-11-09 after acceptance; ADR-0020 (Proposed) proposes to replace them | yes: `_index.json` layout, L-JOB-01, `jobs-verified` |
| [0013](0013-observability-and-tool-first.md) | Observability (run log, token usage) and tool-first work | Proposed (2026-11-08) | yes: run log (writing commands refuse when it cannot be written), `pls step`, `pls usage` |
| [0014](0014-trust-boundaries.md) | Trust boundaries — what `pls` enforces and what it trusts | Proposed (2026-11-09; revised 2026-11-10) — every row pending | cited by code and skills; no row accepted yet |
| [0015](0015-undoing-an-applied-release.md) | Undoing a release that was applied successfully (`pls rollback`) | Proposed (2026-11-11) | no: undo is a new release |
| [0016](0016-agent-team-for-framework-development.md) | An agent team for developing the framework (Orchestrator + three subagents, permission rules) | Accepted (2026-11-11) — 4 open questions stay open | yes |
| [0017](0017-creating-groups-from-the-permission-design.md) | Creating the groups of the permission design on dev (`pls principals --create`) | Accepted (2026-11-11) — option B | yes: `pls principals --create` |
| [0018](0018-test-users-and-keys-for-role-tests.md) | Test users and their API keys for role tests on dev | Accepted (2026-11-11) — option C (B fallback) | yes: `pls test-users` |
| [0019](0019-test-users-in-role-groups.md) | Test users in their role's group (supersedes ADR-0017 rules 2–3) | Accepted (2026-11-11) — option B | yes: `pls test-users` |
| [0020](0020-gate-records-and-approver-model.md) | Gate records, approvers and profile records (one approver per record; G3 / G4 outside dev; Operators; onboarding first) | Proposed (2026-11-11) — option C: as built for `demo`, approvers for `cstg` / `prod` open | yes: `pls gate`, `profile set`, `jobs-verified`, every G3 / G4 check |
| [0021](0021-machine-setup-profile-key-files-and-environment-overrides.md) | Machine setup profile, key files and environment overrides (`PLS_CONNECTIONS`, `PLS_PROFILE_DIR`, `PLS_ACTOR`) | Accepted (2026-11-12) — option B; opt-in asked (built), `file:` limit open | yes: `pls setup` asks the write opt-in, `init --profile` |
| [0022](0022-framework-distribution-to-project-repositories.md) | Framework distribution: launcher, `framework.lock`, `skills check|sync` | Proposed (2026-11-11) — option A for `demo` | yes |
| [0023](0023-configuration-shapes-the-kb-does-not-cover.md) | Configuration shapes the KB does not cover: source at the version's tag → KB probe → `kb-verify` → KB + scope key, once in the framework | Proposed (2026-11-11) — option A | yes, as option A: `references/kb-gaps.md` in the lifecycle skill; P2/P3 skills; `$today±N` probe variables; `[${principal:x}]` in mail addresses |
| [0024](0024-standing-permission-for-dev-writes.md) | Standing permission for dev writes: recorded once per project and dev environment in the person's words, it confirms `apply` / `bootstrap` / `migrate` on role dev until revoked | Accepted (2026-11-12) — option B | yes: `pls profile set dev-writes on|off --env <dev env>`, `_confirm_write`; apply-log `confirmed` |

New ADR: copy `0000-template.md` and use the next number. Accepted ADRs are not edited; changes are made through a new ADR with status "Supersedes".
