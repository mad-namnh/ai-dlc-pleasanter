# Log — TD-34

Counts: subagent calls 0/6, review rounds 0/2, fix attempts 0/3.

- 2026-11-13 | built: resolve_key confines file: keys (resolved path) to the connection file's folder or profile_dir (moved to pls_http, pls.profile_dir delegates); test_key_files_only_in_pls_or_the_profile_folder.py; ratchet: 'file not found' refusal now tested → removed from the list. Docs: ADR-0021 (open question + follow-up as built), ADR-0014 TB-11 control, TD-34 closed, setup.md, pls_http docstring. Suites 536 OK (3.12), 536 OK skipped=2 (3.10), node 15.
- 2026-11-13 | subagent 1/6: reviewer opus high round 1/2 — accept with fixes; F1 partly a stop point (Status/Decision wording proposed), F2 fixed strictly per option B, F3–F5 fixed. Suites 539 OK (3.12); 3.10 and node green before the last test (538 OK skipped=2, 15 pass). Round 2 next.
- 2026-11-13 | subagent 2/6: reviewer opus high round 2/2 — accept with fixes, 4 Low (fixed or for Nam). Parent ff5d27a: new tests 5 of 7 fail (2 baselines). Suites 539 OK (3.12), 539 OK skipped=2 (3.10), node 15. Counts: subagent calls 2/6, review rounds 2/2. Committed.
