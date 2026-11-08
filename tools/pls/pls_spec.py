"""As-is specification skeleton (画面設計書) built from configuration only — no LLM.

`pls spec-skeleton --site <s>` writes every table of the document the skill `pls-x-spec-recovery` asks for: columns,
layout, views, statuses and processes, notifications, links, permissions, and per script its kind, timing, lines,
columns and sites (xref). What only a reader of the code can say (the purpose of a script, the overview, questions)
is left as `<!-- AI: … -->` markers, so the LLM writes a few paragraphs instead of reading the whole site.
"""
from __future__ import annotations

import json
import re

import pls_scripts as SX

TYPES = (("Class", "分類"), ("Num", "数値"), ("Date", "日付"), ("Description", "説明"), ("Check", "チェック"),
         ("Attachments", "添付"))
BUILTIN = {"Title": "タイトル", "Body": "内容", "Status": "状況", "Manager": "管理者", "Owner": "担当者",
           "StartTime": "開始", "CompletionTime": "完了", "WorkValue": "作業量", "ProgressRate": "進捗率",
           "Comments": "コメント", "IssueId": "ID", "ResultId": "ID"}
KIND_JA = {"ServerScripts": "サーバ", "Scripts": "クライアント", "Styles": "スタイル", "Htmls": "HTML"}
NOT_EVENTS = {"Id", "Name", "Title", "Body", "File", "Shared", "TryCatch", "Disabled", "Functionalize"}
AI = "<!-- AI: {} -->"


def _cell(v) -> str:
    s = "" if v is None else str(v)
    return s.replace("|", "\\|").replace("\r", "").replace("\n", " ⏎ ")[:120]


def _type(col: str) -> str:
    for prefix, ja in TYPES:
        if col.startswith(prefix):
            return ja
    return BUILTIN.get(col, "標準")


def _site(text: str, titles: dict[str, str]) -> str:
    """${site:x} → 「タイトル」(x); numbers are never shown (the skill forbids numeric ids)."""
    return SX.REF_TOKEN.sub(lambda m: f"「{titles.get(m.group(2), m.group(2))}」" if m.group(1) == "site"
                            else m.group(0), text or "")


def _choices(text: str | None, titles: dict[str, str]) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    if t.startswith(("[", "{")) and not t.startswith("[["):
        sites = re.findall(r"\$\{site:([A-Za-z0-9_\-]+)\}", t)
        return "ルックアップ: " + ", ".join(f"「{titles.get(s, s)}」" for s in sites) if sites else "JSON 定義"
    if t.startswith("[["):
        return "リンク: " + _site(t.split("]]")[0] + "]]", titles)
    lines = [x for x in t.splitlines() if x.strip()]
    shown = " / ".join(x.split(",")[1] if "," in x else x for x in lines[:6])
    return f"{len(lines)} 件: {shown}{' …' if len(lines) > 6 else ''}"


def _statuses(settings: dict) -> dict[str, str]:
    col = next((c for c in settings.get("Columns") or [] if c.get("ColumnName") == "Status"), {})
    out = {}
    for line in (col.get("ChoicesText") or "").splitlines():
        parts = line.split(",")
        if len(parts) >= 2:
            out[parts[0].strip()] = parts[1].strip()
    return out


def skeleton(name: str, model: dict, titles: dict[str, str]) -> str:
    st = model.get("settings") or {}
    meta = model.get("meta") or {}
    cols = st.get("Columns") or []
    labels = {c["ColumnName"]: c.get("LabelText") or BUILTIN.get(c["ColumnName"], c["ColumnName"]) for c in cols}
    x = SX.xref(st, model.get("scripts") or {})
    status = _statuses(st)
    title = titles.get(name, name)
    out = [f"# 画面設計書（現行）— {title}", "",
           f"> 生成: `pls spec-skeleton --site {name}`（設定から機械的に作成）。AI 記述欄（HTML コメント）の箇所だけを記述し、表は編集しない。", ""]

    out += ["## 1. 概要", "", "| 項目 | 値 |", "|---|---|",
            f"| サイト | {title}（`{name}`） |", f"| 種類 | {meta.get('ReferenceType') or st.get('ReferenceType')} |",
            f"| リンク先 | {', '.join(sorted({_site('${site:%s}' % s, titles) for s in _links(st) - {name}})) or 'なし'} |", "",
            AI.format("このサイトの目的と使われ方を 2〜3 文で（設定・スクリプトのコメントに基づく。推定は（推定）と書く）"), ""]

    out += ["## 2. 項目一覧", "", "| 項目 | 表示名 | 型 | 必須 | 選択肢・リンク | 既定値 | 参照するスクリプト数 |",
            "|---|---|---|---|---|---|---|"]
    for c in cols:
        cn = c["ColumnName"]
        out.append(f"| {cn} | {_cell(labels[cn])} | {_type(cn)} | {'必須' if c.get('ValidateRequired') else ''} | "
                   f"{_cell(_choices(c.get('ChoicesText'), titles))} | {_cell(c.get('DefaultInput'))} | "
                   f"{len((x['columns'].get(cn) or {}).get('scripts') or [])} |")
    out.append("")

    out += ["## 3. 画面レイアウト", ""]
    for tab, items in (st.get("EditorColumnHash") or {}).items():
        out.append(f"- 編集画面 `{tab}`: " + ", ".join(labels.get(i, i) for i in items or []))
    tabs = st.get("Tabs") or []
    if tabs:
        out.append("- タブ: " + ", ".join(_cell(t.get("LabelText")) for t in tabs))
    for key, ja in (("GridColumns", "一覧の列"), ("FilterColumns", "フィルタ")):
        if st.get(key):
            out.append(f"- {ja}: " + ", ".join(labels.get(i, i) for i in st[key]))
    out.append("")

    out += ["## 4. ビュー", ""]
    views = st.get("Views") or []
    out += ["| 名前 | 条件の項目 | 並び順 |", "|---|---|---|"] + [
        f"| {_cell(v.get('Name'))} | {_cell(', '.join(labels.get(k, k) for k in (v.get('ColumnFilterHash') or {})))} | "
        f"{_cell(', '.join(f'{labels.get(k, k)} {d}' for k, d in (v.get('ColumnSorterHash') or {}).items()))} |"
        for v in views] if views else ["なし"]
    out.append("")

    out += ["## 5. ステータスとプロセス", "",
            "ステータス: " + (", ".join(f"{k} {v}" for k, v in status.items()) or "（設定未確認）"), ""]
    procs = st.get("Processes") or []
    if procs:
        out += ["| ボタン | 名前 | 現在 → 変更後 | 表示条件 | 入力チェック | 通知 | 実行できる |", "|---|---|---|---|---|---|---|"]
        for p in procs:
            who = ", ".join(_site(str(g), titles) for g in (p.get("Groups") or []) + (p.get("Users") or []) + (p.get("Depts") or []))
            out.append(f"| {_cell(p.get('DisplayName'))} | {_cell(p.get('Name'))} | "
                       f"{status.get(str(p.get('CurrentStatus')), p.get('CurrentStatus'))} → {status.get(str(p.get('ChangedStatus')), p.get('ChangedStatus'))} | "
                       f"{'あり' if (p.get('View') or {}).get('ColumnFilterHash') else 'なし'} | {len(p.get('ValidateInputs') or [])} | "
                       f"{len(p.get('Notifications') or [])} | {_cell(who) or '全員'} |")
    else:
        out.append("プロセス: なし")
    ctrl = st.get("StatusControls") or []
    if ctrl:
        out.append(f"\nステータス制御: {len(ctrl)} 件（" + ", ".join(_cell(c.get('Name')) for c in ctrl) + "）")
    out.append("")

    out += ["## 6. 通知・リマインダー", ""]
    for key, ja in (("Notifications", "通知"), ("Reminders", "リマインダー")):
        rows = st.get(key) or []
        out.append(f"- {ja}: {len(rows)} 件" + "".join(f"\n  - {_cell(r.get('Subject') or r.get('Prefix'))}（宛先: {_cell(r.get('Address'))}）" for r in rows))
    out.append("")

    out += ["## 7. 集計・リンク", ""]
    out += [f"- リンク: {labels.get(lk.get('ColumnName'), lk.get('ColumnName'))} → {_site(str(lk.get('SiteId')), titles)}"
            for lk in st.get("Links") or []] or ["- リンク: なし"]
    out += [f"- 集計: {_site(str(sm.get('SiteId')), titles)} の {sm.get('DestinationColumn')} ← {sm.get('Type')} {sm.get('SourceColumn') or ''}"
            for sm in st.get("Summaries") or []] or ["- 集計: なし"]
    out.append("")

    out += ["## 8. 権限", ""]
    perm = model.get("permissions") or {}
    out += [f"- {_cell(e)}" for e in perm.get("entries") or []] or ["- （権限の設定なし／継承）"]
    if perm.get("inherit"):
        out.append(f"- 継承元: {_site(str(perm['inherit']), titles)}")
    out.append("")

    out += ["## 9. スクリプト", "", "| 種類 | 名前 | タイミング | 行数 | 読み書きする項目 | 参照サイト | 処理の要約 |",
            "|---|---|---|---|---|---|---|"]
    xs = {(s["kind"], s["script"]): s for s in x["scripts"]}
    for kind, items in (model.get("scripts") or {}).items():
        for it in items or []:
            nm = it.get("Name") or it.get("Title") or f"Id {it.get('Id')}"
            ev = [k for k, v in it.items() if v is True and k not in NOT_EVENTS]
            info = xs.get((kind, nm), {"columns": [], "sites": []})
            colstr = ", ".join(labels.get(c, c) for c in info["columns"][:8]) + (" …" if len(info["columns"]) > 8 else "")
            out.append(f"| {KIND_JA.get(kind, kind)} | {_cell(nm)} | {_cell(', '.join(ev))} | {(it.get('Body') or '').count(chr(10)) + 1} | "
                       f"{_cell(colstr)} | {_cell(', '.join(titles.get(s, s) for s in info['sites']))} | "
                       f"{AI.format('1〜2 文で処理内容（コメント・関数名・context.Error から）')} |")
    out += ["", "## 10. 未確認事項", "", "### お客様への確認事項", "", AI.format("設定から分からず、お客様しか答えられないこと（日本語の質問）"),
            "", "### 設定から後で確認できること", "", AI.format("推定した点と、その根拠の行"), ""]
    return "\n".join(out)


def _links(st: dict) -> set[str]:
    """Logical names of sites this configuration points to (links, lookups, summaries)."""
    blob = json.dumps(st, ensure_ascii=False)
    return {m.group(2) for m in SX.REF_TOKEN.finditer(blob) if m.group(1) == "site"}


def ai_markers(text: str) -> int:
    """How many `<!-- AI: … -->` places are still open (0 = the narrative is written)."""
    return text.count("<!-- AI:")
