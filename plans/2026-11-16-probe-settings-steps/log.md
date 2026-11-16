# Log — ADR-0027 build

- 2026-11-16 Built in worktree wt-0027 (base 75f9b3b). New test file 14 tests OK.
- Parent check (HEAD versions of pls.py, pls_http.py, pls_kbverify.py, pls_kbverify_guarded.py swapped in): new file 15 tests → failures=5, errors=9 (one passes on the parent: the teardown refusal, which already existed).
- refusals_without_a_test.txt: run_tests "unknown op" now run by a test → line removed (meta-test). Suites: 3.12 667 OK after that, 3.10 667 OK (skipped=2), node 16/16. Review next.
- Review round 1 (opus, high; subagent 1/6): accept with fixes, F1 High → all fixed (review.md). Round 2 next.
- Review round 2: accept with fixes, R2-1 Medium + Low → fixed (review.md). Commit after suites.
