# Plan — TD-34: `file:` key references only inside the connection file's folder or the machine-profile folder

- **Date / branch:** 2026-11-13 / `brownfield-adr`; parent `ff5d27a`
- **Tier:** Critical (secrets / keys, ADR-0014 TB-11). Review `pls-x-reviewer`, `opus`, high.
- **Decision already made:** ADR-0021 option B, accepted by Nam 2026-11-12 ("`file:` limited to `.pls/` and the profile folder"); Nam 2026-11-13: "lam tiep TD-39 va cac task con lai".
- **Change:** `pls_http.resolve_key` resolves a `file:` reference (relative to the connection file, or absolute) with `Path.resolve()` and reads it only when the real path lies inside the project's `.pls/` (changed after review round 1: not the folder of a connection file named by `$PLS_CONNECTIONS`) or the machine-profile folder (`$PLS_PROFILE_DIR` or `~/.pls/profiles`); else a refusal that names both folders. `profile_dir()` moves to `pls_http` (one definition; `pls.profile_dir` calls it).
- **Acceptance:** 1. relative key inside `.pls/` (also `test-users/…`) and the profile key written by `pls setup` keep working; 2. `../x.key`, an absolute path elsewhere, a path that escapes through `..` after a valid prefix → refused before the file is read; 3. tests fail on the parent; suites green (3.10); 4. docs: ADR-0021 "As built" note, ADR-0014 TB-11, tech-debt TD-34 closed, `docs/setup.md` key paragraph, pls_http docstring.
