---
name: pls-x-spec-recovery
description: Writes the as-is specification (画面設計書, Japanese) of an adopted Pleasanter site from its configuration in git — columns, layout, views, statuses and processes, notifications, links, permissions and what each script does — marking every inference. Use after pls-x-onboarding has adopted a site, and whenever P1 or P2 needs to know how an existing site behaves today.
---

# pls-x-spec-recovery — as-is specification from configuration

**Goal:** one document per site that a business owner can read and P1/P2 can rely on, derived only from `config/<site>/`.
**You describe; you do not judge or redesign.** Improvements go to P1 as questions, not into this document.

## Inputs

- `config/<site>/` (site.json, scripts, permissions.json), `ops/adopt/<…>-<site>.md`, `ops/xref/<site>.json` (`pls xref --site <site>`).
- `pls-kb-pleasanter` for what each setting means (schema.md, D-entries).

## Output

`design/as-is/<site>.md`, in **Japanese** (it is read by the customer), headings:

1. 概要 — サイト名、種類 (記録/期限付き/ダッシュボード)、リンク元・リンク先サイト
2. 項目一覧 — 項目 (slot)、表示名、型、必須、選択肢 (`[[${site:x}]]` はリンク)、既定値
3. 画面レイアウト — タブ／セクション、編集画面の項目順、一覧の列、フィルタ
4. ビュー — 名前、条件、並び順
5. ステータスとプロセス — ステータス一覧、ボタンごとに: 表示条件、変更後ステータス、データ変更、通知、実行できるグループ
6. 通知・リマインダー — 条件、宛先 (`${env:x}` / `${principal:x}` / `[Manager]`)、件名
7. 集計・リンク — Summaries、Links
8. 権限 — ロール (グループ) ごとの権限
9. スクリプト — スクリプトごとに: 種類 (サーバ／クライアント)、タイミング (BeforeCreate…/画面)、読む・書く項目とサイト (xref)、処理の要約
10. 未確認事項 — 推定したこと、設定から分からないこと

## Rules

- **Only from configuration.** Every statement traces to a setting or a script line. A conclusion you drew is marked **（推定）** with the line it rests on.
- **Scripts:** use `ops/xref/<site>.json` and the script's own comments first; read a large body by searching (function names, `context.Error`, `items.`), not end to end. One short paragraph per script. A script with no clear purpose is listed under 未確認事項, not guessed.
- **No business data:** never read records; examples use placeholders.
- **Ids:** write logical names (`${site:kokyaku}` → 顧客サイト), never numeric ids.
- **Server scripts without a design decision** (lint L-LAD-01): the 9. section is that decision's source. After the person has reviewed the document, add `design/decisions/DES-000-as-is-<site>.md` (English) listing each server script by `Name` with its purpose and rung 3 reason "existing behaviour, adopted"; this clears L-LAD-01 for adopted code only.

## Checklist

- [ ] Every column, process, view, notification and script of the site appears once.
- [ ] Every （推定） names its evidence; 未確認事項 lists what only the customer can answer, as questions in Japanese.
- [ ] No numeric ids, no record data, no secrets.
- [ ] The person reviewed it before DES-000 is written.
