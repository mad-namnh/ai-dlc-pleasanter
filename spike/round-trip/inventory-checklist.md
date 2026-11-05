# Configuration component checklist — 1.5.x round-trip

Fill in after steps 3–5. Legend: ✅ round-trips 100% · 🟡 partial (explain) · ❌ does not · ➖ not tried

**Core** = must be ✅ for a Go.

| # | Group | Component | Core | API create | API update | Site package | Notes |
|---|---|---|---|---|---|---|---|
| 1 | Table | Table type (期限付き / 記録 / フォルダ / Wiki / ダッシュボード) | ✓ | 🟡 | 🟡 | 🟡 | 記録 + フォルダ ✅; 期限付き/Wiki/ダッシュボード not tried |
| 2 | Columns | Column definitions (label, type, required, default, format) | ✓ | ✅ | ✅ | ✅ | updatesite deletes definitions missing from the payload (D4) |
| 3 | Columns | 選択肢 (choices), choices linked to another site | ✓ | ✅ | ✅ | ✅ | `[[SiteId]]`: API keeps the original ID, package remaps (D6) |
| 4 | Columns | Validation (入力検証), constraints | ✓ | ✅ | ✅ | ✅ | Only ValidateRequired tried |
| 5 | Columns | Formulas (計算式) | ✓ | ➖ | ➖ | ➖ | |
| 6 | Columns | Extended columns (拡張項目) | | ➖ | ➖ | ➖ | Related to ADR-0002 |
| 7 | Screens | Editor (EditorColumnHash, tabs, セクション) | ✓ | ✅ | ✅ | ✅ | No tabs/sections yet |
| 8 | Screens | Grid (GridColumns), filters, sorting | ✓ | ✅ | ✅ | ✅ | |
| 9 | Screens | Views (ビュー) | | ✅ | ✅ | ✅ | Includes a Crosstab view |
| 10 | Links | Links between sites, lookups (ルックアップ) | ✓ | ✅ | ✅ | ✅ | Links/Summaries: API keeps original IDs, package remaps (D6) |
| 11 | Workflow | プロセス (buttons, conditions, actions) | ✓ | ✅ | ✅ | ➖ | Slices #1–#3 (D10, D20, D21) |
| 12 | Workflow | ステータス制御 (status control) | ✓ | ➖ | ➖ | ➖ | |
| 13 | Automation | 通知 (notifications) | ✓ | ✅ | ✅ | ✅ | Sample uses mail to `[Manager]`; webhooks not tried |
| 14 | Automation | リマインダー (reminders) | | ✅ | ✅ | ✅ | |
| 15 | Code | サーバースクリプト (server scripts) | ✓ | ✅ | ✅ | ✅ | Includes shared scripts. SiteIds inside strings not remapped (D3); plain-text secret found (D5) |
| 16 | Code | スクリプト (client scripts) | ✓ | ✅ | ✅ | ➖ | BR3 2026-11-05 (`report-br3-20261105.md`), D29 |
| 17 | Code | スタイル (styles) | | ✅ | ✅ | ➖ | BR3, D29 |
| 18 | Code | HTML (if used) | | ✅ | ✅ | ➖ | BR3, D29 (PositionType 1000/1010) |
| 19 | Code | 拡張SQL (extended SQL) | | ➖ | ➖ | ➖ | May be server-side files |
| 20 | Permissions | Site permissions | ✓ | ✅ | ✅ | ➖ | References user/group IDs; slices #2–#3 (D15, ADR-0006) |
| 21 | Permissions | Record and column permissions | ✓ | ➖ | ➖ | ➖ | |
| 22 | Other | CSV export/import settings (エクスポート設定) | | ➖ | ➖ | ➖ | |
| 23 | Other | Aggregations, charts, カレンダー, ガントチャート, カンバン | | 🟡 | 🟡 | 🟡 | Aggregations + Summaries (cross-site 集計) ✅; other modes not tried |
| 24 | Other | Search, 一括更新 (bulk update) | | ➖ | ➖ | ➖ | |
| 25 | Outside sites | Users / groups / 組織 (organizations) | | ➖ | ➖ | ➖ | Possibly out of scope (ADR-0001) |
| 26 | Outside sites | `Parameters/` folder on the server | | ➖ | ➖ | ➖ | Managed as files (customer IT) |
| 27 | Outside sites | Tenant settings | | ❌ | ❌ | ➖ | No tenant API (BR3 probe: 404); background server scripts live here (D31, ADR-0012) |
| 28 | Outside sites | Built-in MCP (`McpServer.json`) | | ➖ | ➖ | ➖ | D1 |

| 29 | Other | Dashboards (ダッシュボード) parts | | 🟡 | 🟡 | ➖ | BR3: types 1 timeline, 3 HTML, 4 calendar ✅ (D30); 0 quick access, 5 kanban ➖ |

## Summary

### Round 1 (2026-11-05, sites 42410 + 42411)

- Core components verified ✅: **8 / 15** (2, 3, 4, 7, 8, 10, 13, 15) — none failed
- Core components not yet verified: 1 (partially), 5, 11, 12, 16, 20, 21 → **round 2**
- All components verified: 11 / 28
- Manual share: not yet determined (no component has failed to round-trip so far)
