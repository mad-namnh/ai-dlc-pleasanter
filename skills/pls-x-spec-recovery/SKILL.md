---
name: pls-x-spec-recovery
description: Writes the as-is specification (画面設計書, Japanese) of an adopted Pleasanter site from its configuration in git — columns, layout, views, statuses and processes, notifications, links, permissions and what each script does — marking every inference. Use after pls-x-onboarding has adopted a site, and whenever P1 or P2 needs to know how an existing site behaves today.
---

# pls-x-spec-recovery — as-is specification from configuration

**Goal:** one document per site that a business owner can read and P1/P2 can rely on, derived only from `config/<site>/`.
**You describe; you do not judge or redesign.** Improvements go to P1 as questions, not into this document.

## Inputs

- `config/<site>/` (site.json, scripts, permissions.json), the adoption report `ops/adopt/<date>-<env>-<site>.md` if there is one (not required), `ops/xref/<site>.json` (`pls xref --site <site>`).
- `pls-kb-pleasanter` for what each setting means (schema.md, D-entries).

## Output

Start with `pls spec-skeleton --site <site>`: it writes `design/as-is/<site>.md` with every table below filled from the configuration. **Do not edit the tables.** Write only the places marked with an `AI:` HTML comment (overview, one or two sentences per script, 未確認事項), reading each script by searching it, not end to end. Write a document only for a site a change request touches.

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
- **What the configuration does not say** is written as （設定未確認） in place — never filled in. A column that only has default settings still gets its own row (slot, type, 「既定」).
- **Notification conditions** that are views (`BeforeCondition`/`AfterCondition` = view Id) are written as the view's name.
- **未確認事項** has two parts: questions for the customer (Japanese) and points you can settle later from the configuration.
- **No business data:** never read records; examples use placeholders.
- **Ids:** write logical names (`${site:kokyaku}` → 顧客サイト), never numeric ids.
- **Server scripts without a design decision** (lint L-LAD-01): the 9. section is that decision's source. After the person has reviewed the document — record it in its header (「レビュー: <name>, <date>」) and commit (`docs(as-is): …`) — add `design/decisions/DES-000-as-is-<site>.md` (English) listing each server script by `Name` with its purpose and rung 3 reason "existing behaviour, adopted"; this clears L-LAD-01 for adopted code only. Client scripts need no DES-000 entry.

## Checklist

- [ ] Every column, process, view, notification and script of the site appears once.
- [ ] Every （推定） names its evidence; 未確認事項 lists what only the customer can answer, as questions in Japanese.
- [ ] No numeric ids, no record data, no secrets.
- [ ] The person reviewed it before DES-000 is written.
