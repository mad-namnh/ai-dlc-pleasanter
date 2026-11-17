# Review — first probes on ADR-0027

## Round 1 (pls-x-reviewer, opus, medium) — reject (probes / KB), code acceptable with doc fixes
- **F1 High:** D51 could not answer merge vs replace: the source (SiteUtilities.cs l.2358–2440) upserts only six lists and ignores a `SiteSettings` key; the KB row said the body shape was not in the clone → D51 rebuilt as a Process upsert (rename 1, add 2, column label kept), judged; `settings_partial` body = `Processes` / `StatusControls` lists only; the source reading recorded in ADR-0027 As built (WS3c-1 answered from the source: the route cannot fix a JSON link).
- **F2 High:** D50's Owner expectation would fail on a correct store (string vs int) and the shape sent is not the screen's `["<id>"]` → D50 probes Groups only (List<int>); the Owner filter's screen shape recorded source-derived.
- **F3 Medium:** `observe` counted a pass as verified and a fail as fail → an observe probe ends `observed` whatever its checks said and never decides its entry; test.
- **F4 Medium:** `siteConfig` selectors / variables changed `pls test` → kb-verify only (`site_ops` given); test-spec.md stays true.
- **F5 Low:** reminder column CompletionTime on a Results site → `DateA` (a DateA column added).
- **F6 Low:** OperatorType number assumption → named in D49's not covered.
- **F7 Low:** docs (module docstring, ADR-0009 note, kb-gaps.md, ADR-0027 As built); repeated "not verified" text → curator.

## Round 2 (same reviewer) — accept with fixes; Low only
- N1: observe run path untested → `ObserveRunTest` (a failing check ends `observed`).
- N2: `pls test` siteConfig behaviour not pinned → `PlsTestSiteConfigTest` (positional paths, literal `$x`, no selector).
- N3: literal principal ids in process settings (pre-existing, now also via settings_partial) → TD-70.
- N4: TD-50 cited but not in this tree → resolves with the D40 task commit.
