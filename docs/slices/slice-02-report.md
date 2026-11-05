# Vertical slice #2 — report (2026-11-05)

A multi-part customer change carried through P1–P5 with skills v0.2 / KB 0.5 and `pls` v0.3. The aim was to exercise what slice #1 did not: several sites in one release, data migrations, and permissions.

- **Requirement source:** a customer mail written by an independent role-play customer, `pls-demo-inquiry/sources/2026-11-05-customer-mail-category-accounting-time.md`. It asks for three things:
  - split カテゴリ 契約・請求 into 契約 and 請求;
  - give 経理チーム read access to inquiries and 対応履歴;
  - record 対応時間 per 対応履歴 and show a total per inquiry.
- **Project repository:** `pls-demo-inquiry` (merged to `main`)
- **Environments:** dev 44565/44566, stg 44573/44574 (MADLAB dev, Pleasanter 1.5.2)
- **Release:** R-20261105-05 on stg. It changed 2 sites and carried 2 migrations. Two rehearsals on dev came first: R-20261105-03-dev and R-20261105-04-dev.
- **Gates:** Nam approved all of them. G1 and G2 were each approved twice:
  - G1: approved, then REQ-013 revised.
  - G2: approved, then reopened for B4 after T-015 and approved again.
  - G3 and G4: approved once each.

## Result per phase

| Phase | What happened | Verdict |
|---|---|---|
| P1 Requirements | 9 EARS requirements (REQ-007…015), 3 of them derived (REQ-009 AI choices, REQ-012 no change, REQ-015 対応回数 unchanged). Questions Q8–Q22 carry `[assumed]` defaults. | ✅ G1 |
| P2 prerequisites | Brought site `responses` under git. The prerequisite check found that 作業時間 already exists and is filled. That conflicts with REQ-013 (new column), so it went back to G1, which revised REQ-013 to use 作業時間 (Q23). | ✅ loop back to G1 |
| P2 Design | DES-003 in three parts:<br>• A: choices plus migration M1.<br>• B: permissions in git (ADR-0006). 経理 gets value 1.<br>• C: Summary Total into NumB, plus migration M2 because summaries do not recalculate existing parents (D16).<br>Classified data- and permission-impacting. Probes PR-1…PR-3 ran on dev before P3. | ✅ G2 |
| P3 Build | Config edited in git. Principals are mapped per environment (`${principal:x}`). Slot ledger updated. | ✅ |
| P4 Verify | **T-015 failed AC5:** a read-only 経理 user still sees the エスカレーション button, and pressing it returns 403. Two causes:<br>• KB D19 had been written from a probe site without a matching process.<br>• DES-003 had rejected process access control because of that entry.<br>Fixed by correcting D19, adding D20, and redesigning B4 with `Groups: [${principal:support}]` on the process (`pls` maps the process ACL IDs). G2 approved again, then T-001…T-016 passed. | ✅ G3 after one design loop |
| P5 Release | `release-plan` ran in dependency order (inquiries → responses) with the migration gate.<br>`applyRelease`: the preflight checked UpdatedTime; the apply step would restore the previous config automatically on failure.<br>M1 and M2 found 0 records on stg.<br>Round trip: 0 differences on both sites, then `mark-applied`; drift against the new baseline is 0.<br>Smoke tests T-009, T-010 and T-016 passed. | ✅ G4 |
| P6 Operate | Not exercised in this slice. | — |

## Findings → framework backlog

| # | Finding | Severity | Change |
|---|---|---|---|
| S2-1 | A probe that does not reproduce the real configuration produced a wrong KB entry (D19), and the design relied on it. P4 caught it, but only through a role-based test user. | High | ✅ D19 corrected, D20 added. **Rule for the KB skill:** a probe used as design evidence must include the feature it is evidence for (here, a process with a matching display condition). Role-based tests (TD-11) proved essential and are now part of slice tests. |
| S2-2 | Process access-control IDs (`Groups`/`Users`/`Depts`) depend on the environment, just like permissions. | High | ✅ `pls` maps them through `${principal:x}`. L-PERM-01 also covers process ACLs. |
| S2-3 | Adding a Summary needs a data step: existing parents are not recalculated, and there is no API to sync them (D16). The migration (M2) also changes 更新日時/更新者 of one child per parent. | Medium | ✅ Summary changes are classified data-impacting. The customer must be told (O7). |
| S2-4 | A P2 prerequisite check (does the request duplicate an existing column?) changed a requirement before design started. | Medium | Add "existing column or feature already covers it?" to the P1/P2 impact checklist (skills v0.3). |
| S2-5 | Transport: one base64 transcription error on a large export. | Medium | ✅ Exports now move in halves, each checked with SHA-256. Still manual and token-heavy, so it stays under S4/ADR-0003. |
| S2-6 | Migrations were rehearsed on dev data only. stg had 0 matching records, so the first real migration volume remains untested. | Medium | Open (plan Step 4 item 3). |
| S2-7 | `ai1.js` choice list was edited directly, but its generator spec is not in the repository. | Low | O2 — bring the spec into git before `ai1` is regenerated. |

## Open items handed to the customer or later stages

- Q8–Q24: answer from the customer (assumptions approved at G1/G2).
- O3: production environment and the real groups for `accounting` (Q13) and `support` (Q24). dev and stg use the test groups `zz_test_経理` (372) and `zz_test_サポート` (373) and the test user 10061.
- O7: tell the customer that M2 changes 更新日時 and 更新者.
- Mail: still deferred (TD-10).
