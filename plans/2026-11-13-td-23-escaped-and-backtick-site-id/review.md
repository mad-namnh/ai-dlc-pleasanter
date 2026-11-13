# Review — TD-23 site id under a JSON-escaped or backtick-quoted key (Critical)

## Round 1 — accept with fixes (0 Critical, 0 High, 1 Medium, 4 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `6b7693b`; `git status` and a hash of the diff and the plan folder equal before and after.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| F1 | Medium | Same family still missed and, with TD-23 closed, untracked: `p["SiteId"] = 797`, `p['site_id'] === 797`, `797 === p["siteId"]`, `{["siteId"]: 797}`, `` [`siteId`]: 797 `` (the valid backtick key), `` siteId: `797` ``, `siteId: \"797\"`, JSON escaped twice | Nam 2026-11-13 "Mở rộng luôn trong TD-23": rule widened (bracketed name with `=`, `==`, `===`, `!=`, `!==`, `:`; backtick or escaped value under an unquoted name; AFTER_CONTEXT `797 === p["siteId"]`), test with look-alikes (`[p["siteId"], 797]` caught on the first try and fixed: a comma after `]` is not a context); JSON escaped twice → TD-42 |
| F2 | Low | `docs/review-findings.md` D3 still says rare forms tracked by TD-23 | fixed: TD-23 closed, TD-42 |
| F3 | Low | tech-debt closing note says "a backtick as the quote" — only for a quoted key | fixed: note lists the forms exactly |
| F4 | Low | existing projects see a one-time diff on the next unpack, L-REF-01 until then | stated in the TD-23 note, `HANDOFF.md` and the commit message |
| F5 | Low (info) | the optional backslash carries the accepted over-match `\"SITE_ID_COUNT\": \"797\"` | no change (same as the earlier review's F3) |

## Round 2 (last) — accept (0 Critical, 0 High, 0 Medium, 3 Low)

Reviewer: `pls-x-reviewer`, model `opus`, effort `high`; working tree against `6b7693b`; tree equal before and after. Round 1: F1–F3 fixed, F4 stated (completed by L2), F5 unchanged. Criteria 1–7 met; reviewer ran the new tests against the parent module in memory: 3 failures.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| L1 | Low | bracketed name with spaces inside the brackets before the number (`p[ "siteId" ] = 797`) and optional chaining (`797 === obj?.["siteId"]`) not recognised | recorded in TD-42 (no code change after the last review round) |
| L2 | Low | the existing-projects note leaves out scheduled scripts: L-REF-01 on them is not cleared by unpack | fixed: TD-23 note and `HANDOFF.md` say to edit them by hand |
| L3 | Low (info) | accepted over-matches consistent with existing rules (`x ? p["siteId"] : 797`, `` console.log(`siteId`, 797) ``, `p["SITE_ID_COUNT"] = 797`) | no change |
