# Review — TD-63 classify rules for six site switches

Reviewer: pls-x-reviewer (opus), round 1, 2026-11-18, working tree against 65ba2e5. Verdict: **accept with fixes**. No Critical / High.

Source claims checked by the reviewer against Pleasanter_1.5.2.0 (ServerScriptUtilities.cs l.1089/1236; IssueModel.cs l.3302, ResultModel.cs l.2984; HtmlImports.cs l.78; SiteSettings.cs l.406/940/1222; IssueValidators.cs l.1106-1116; HtmlScripts.cs l.130/136; HtmlTemplates.cs l.182/223-227): match.

| Id | Sev | Finding | Disposition |
|---|---|---|---|
| M1 | Medium | KB D44/D46/D47, generated impact-rules D47 advice, review-findings D43–D47, inventory-checklist row 30 still said "held back / decision record (TD-63)" | Fixed: KB rows by pls-kb-curator (KB 0.35, source-derived effects with lines), impact-rules regenerated, both doc rows updated |
| L1 | Low | CL-EXTENDED-HEADER design text said no secret check; L-SEC-01 does read it | Fixed: "no script check reads it (no ladder reason, no syntax check; L-SEC-01 still refuses a secret)" |
| L2 | Low | ExtendedHeader script heuristic: misses entity-encoded / iframe, false positive on `content="one=two"` | Fixed: iframe/object/embed, data:text/html, `&#`, handler needs leading whitespace; message says "looks like"; code comment says it is a pointer, not a check; tests for both cases |
| L3 | Low | no test for a boolean switch changed in place | Fixed: True→False case per boolean key |
| L4 | Low | `pls_impact_rules.py --check` is not a flag | Noted: evidence is the test `test_the_generated_reference_is_up_to_date`, not `--check` |

After the fixes: 3.12 737 OK; 3.10 737 OK (skipped=2); node 16/16. Round 2 not needed (no Critical/High; fixes are text, a message heuristic and tests).
