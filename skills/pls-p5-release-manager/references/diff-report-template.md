# `releases/<release>/diff-report.md` — template

The first part is for the business owner (Japanese). The second part is for the operator (English). Both come from the raw diff (`raw-diff-<site>.md`), `plan.json` and the requirements. Do not state anything the raw diff does not show.

```markdown
# <release> — <target>: <title>

## お客様向けサマリー（日本語）

**今回の変更で利用者から見て変わること**
- <REQ-…> <画面・一覧・ボタン・通知の変化を利用者の言葉で>

**既存データ・権限への影響**
- <なし／移行内容（件数・方法）／権限の変更（誰が何をできるようになる・できなくなる）>

**リリース手順と戻し方**
- 順序：<site> → <site>（理由）
- 失敗時：<自動で元の設定に戻す／移行の戻し方>

**確認事項（未決）**
- <Q… / O…>

## Operator details (English)

| Item | Value |
|---|---|
| Target | <env>, sites <name (id)>, … |
| Classification | config-only / data-impacting / permission-impacting — reason |
| Order | <site> → <site> (dependency) |
| Checks by `pls` | complete payload, drift (0 / accepted: <record>), slots clean, migration gate |
| Rollback | reverse order from `rollback-<site>.json`; migrations: <rollback> |
| After apply | export → `mark-applied` (0 differences) → smoke <T-…> |

Raw changes: `raw-diff-<site>.md` (n differences per site).
```
