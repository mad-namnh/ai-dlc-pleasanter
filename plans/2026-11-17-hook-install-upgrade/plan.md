# Plan — pls hook install replaces its own older entries (TD-69)

- **Tier:** Standard. **Origin:** Nam 2026-11-17 "cu lam tiep khong can hoi".
- **Change:** `pls_hooks.install` replaces entries whose command runs `pls.py" hook` when they differ from the current ones; other hooks kept; no write when nothing changes.
- **Acceptance:** test with an older entry and a foreign hook; suites green; review.
