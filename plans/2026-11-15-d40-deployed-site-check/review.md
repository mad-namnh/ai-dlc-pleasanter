# Review — D40 deployed-site check

## Round 1 (pls-x-reviewer, opus, high) — accept with fixes

- **M1:** Links-table rewrite is not screen-only — `updatesite` reaches the same `SiteModel.Update` → `UpdateRelatedRecords` + `SiteInfo.Refresh`. → KB (curator) and TD-48/TD-50 reworded: cause not explained by the source read.
- **M2:** TD-50 drift claim untrue (`UpdatedTime` in `SITE_VOLATILE`; preflight compares the same release's snapshot). → TD-50 reworded.
- **M3:** lookup fill only implied, 単価 editable. → Resolved by Nam ("co", evidence 6); README/HANDOFF wording.
- **L1:** 数値 → 数量: confirmed by Nam's later words (evidence 7). **L2:** wording beyond verbatim → curator. **L3:** stale TD-48, review-findings status, ADR-0023 follow-up, impact checklist not tracked → fixed / TD-51. **L4:** account not stated for these reports → KB says so.

## Round 2 (pls-x-reviewer, opus, high) — accept with fixes; H1 open → stop (2 rounds used)

- **H1:** "saved once" / "no setting changed" / "(the observed saves toggled it)" not supported: evidence report 3 is 自動ポストバック off → save → on → save; the `[[44970]]` test (report 2) and restoring the JSON form very probably needed screen saves that did not help. Wording in behaviours.md D40 (C), index.json, schema.md, README, review-findings, ADR-0023, TD-50, HANDOFF. Fix: state the observed procedure as the release step; plain save not known to work; questions to Nam.
- **M1 (from round-1 M2 fix):** TD-50 says run `pls mark-applied` after the save — `pls` refuses it for an applied release (pls.py:4074-4077, 4158-4160). Fix: `pls export` + `pls drift`.
- **L1:** column toggled not named in evidence (KB says `ClassB`). **L2:** plan.md still says administrator. **L3:** "value stored after save and reopen" is DES-004 O-16 of the trial — cite it; verbatim is "luu lai thi van dung".
- Suites: Python 598 OK, Node 15/15. Not verified: Pleasanter source line numbers (no local clone).
