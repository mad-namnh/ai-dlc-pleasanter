# Architecture Decision Records

| ADR | Topic | Status |
|---|---|---|
| [0001](0001-config-scope-in-git.md) | Scope of configuration managed in git | Proposed — spike round 1 done, round 2 pending |
| [0002](0002-column-slot-allocation.md) | Column-slot ranges per ownership zone | Proposed — customer input deferred (TD-01) |
| [0003](0003-production-deploy.md) | Production deployment (on-prem) | Proposed — customer IT input deferred (TD-02) |
| [0004](0004-data-impacting-changes.md) | Data-impacting changes & dedicated gate | Accepted (2026-11-05) — migration folder required by `pls plan` |
| [0005](0005-config-storage-and-secrets.md) | Configuration storage & secrets policy | Partially accepted (runtime secrets); storage deferred (TD-03) |
| [0006](0006-site-permissions-in-git.md) | Site permissions in git (opt-in, logical principals) | Accepted (2026-11-05) |
| [0007](0007-creating-new-sites.md) | Creating new sites: skeleton bootstrap, then the normal release | Proposed (2026-11-05) |
| [0008](0008-http-transport.md) | HTTP transport with local connections (no browser in the loop) | Proposed (2026-11-05) |

New ADR: copy `0000-template.md` and use the next number. Accepted ADRs are not edited; changes are made through a new ADR with status "Supersedes".
