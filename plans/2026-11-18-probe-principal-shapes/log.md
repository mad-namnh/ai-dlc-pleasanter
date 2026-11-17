# Log

- 2026-11-18 implemented in a worktree; kb-verify module tests OK; scan of every KB probe's site settings: no new finding.
- 2026-11-18 suites: 3.12 738 OK; 3.10 738 OK (skipped=2); node 16/16. New test on the parent (pls_kbverify.py unchanged since 65ba2e5): 12 subtest failures, all in test_no_principal_is_named_in_other_shapes.
- 2026-11-18 review round 1 (opus): accept with fixes, L1–L5 handled (review.md); suites again 738 OK / 738 OK skipped=2 / node 16; 29 KB probes pass check_probe.
