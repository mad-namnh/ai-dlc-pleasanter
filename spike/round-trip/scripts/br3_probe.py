"""BR3 spike (ADR-0001 round 2, plan Step 4c): do Htmls, Scripts, Styles and dashboard parts round-trip?

Writes ONLY to a dev environment (pls_http.assert_writable: role dev + allow_write) under its parent folder:
creates two probe sites `zz_probe_br3_results` (Results) and `zz_probe_br3_dash` (Dashboards). They are never
deleted by this script (agents do not delete; a person removes them in the UI).

Checks, per site:
  1. sent vs stored      — what Pleasanter kept, dropped or added on save (canonicalisation, D8);
  2. raw round trip      — export → updatesite(export) → export: 0 differences expected;
  3. pls round trip      — export → pls logical/unpack → read_tree → pack → updatesite → export: 0 differences
                           expected (scripts split into files and reassembled; ids → ${site:x} → ids);
  4. references          — every probe site id inside the stored settings became ${site:x} in the logical model,
                           and packing for another environment puts that environment's ids back (no write).

Usage (from the framework root):
  python spike/round-trip/scripts/br3_probe.py --project "<project dir with environments.json>" --env dev
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "tools" / "pls"))
import pls  # noqa: E402
import pls_http as H  # noqa: E402

TITLE_A, TITLE_B = "zz_probe_br3_results", "zz_probe_br3_dash"


def settings_a(id_b: int) -> dict:
    return {
        "Scripts": [
            {"Id": 1, "Title": "全画面スクリプト", "All": True,
             "Body": "$p.events.on_grid_load = function () {\r\n  console.log('一覧: ' + `${1 + 1}`);\r\n};\r\n"
                     f"var dashboardSiteId = {id_b};\r\n"},
            {"Id": 2, "Title": "新規・編集", "New": True, "Edit": True,
             "Body": "// 編集画面\n$p.events.on_editor_load = function () { $('#Results_Title').css('color', 'red'); };\n"},
            {"Id": 3, "Title": "無効化", "Index": True, "Disabled": True, "Body": "alert('disabled');"},
        ],
        "Styles": [
            {"Id": 1, "Title": "全体", "All": True, "Body": "#MainContainer { font-family: \"Meiryo\"; }\r\n.grid td { color: #333; }"},
            {"Id": 2, "Title": "一覧", "Index": True, "Body": "/* 一覧 */ .grid { width: 100%; }"},
        ],
        "Htmls": [
            {"Id": 1, "Title": "ヘッダー", "PositionType": 1000, "All": True,
             "Body": "<div id=\"probe-header\" data-x='1'>備品貸出 <b>テスト</b>&nbsp;&amp;</div>"},
            {"Id": 2, "Title": "編集フッター", "PositionType": 1010, "Edit": True,
             "Body": "<script>console.log(\"html block\");</script>\n<style>.x{}</style>"},
        ],
    }


def settings_b(id_a: int) -> dict:
    return {"DashboardParts": [
        # Types seen in real exports: 0 quick access, 1 timeline, 3 HTML, 4 calendar, 5 kanban. Timeline/calendar/kanban
        # parts need "View" (an object): without it updatesite fails with HTTP 500 and an HTML error page (BR3 probe).
        {"Id": 1, "Title": "お知らせ", "Type": 3, "X": 0, "Y": 0, "Width": 6, "Height": 10, "ShowTitle": True,
         "HtmlContent": f"<p>テスト <a href=\"/items/{id_a}/index\">台帳</a></p>"},
        {"Id": 2, "Title": "タイムライン", "Type": 1, "X": 6, "Y": 0, "Width": 6, "Height": 20, "SiteId": id_a,
         "TimeLineSites": str(id_a), "TimeLineTitle": "[Title]", "TimeLineBody": "[ClassA]", "TimeLineItemCount": 20,
         "TimeLineDisplayType": 2, "View": {}},
        {"Id": 3, "Title": "カレンダー", "Type": 4, "X": 0, "Y": 10, "Width": 6, "Height": 20, "SiteId": id_a,
         "CalendarSites": str(id_a), "CalendarSitesData": [str(id_a)], "CalendarType": 1,
         "CalendarTimePeriod": "Monthly", "CalendarFromTo": "UpdatedTime", "View": {}},
    ]}


def section_report(sent: dict, stored: dict) -> list[str]:
    out = []
    for sec, items in sent.items():
        got = stored.get(sec)
        if got is None:
            out.append(f"  {sec}: DROPPED entirely")
            continue
        for s_it, g_it in zip(items, got):
            dropped = sorted(set(s_it) - set(g_it))
            added = sorted(set(g_it) - set(s_it))
            changed = sorted(k for k in set(s_it) & set(g_it) if s_it[k] != g_it[k])
            if dropped or added or changed:
                out.append(f"  {sec}[{s_it.get('Id')}]: dropped {dropped} added {added} changed {changed}")
        if len(items) != len(got):
            out.append(f"  {sec}: sent {len(items)} item(s), stored {len(got)}")
    return out or ["  everything sent was stored unchanged"]


def diffs(a: dict, b: dict) -> list[str]:
    return [f"{d['path']}: {pls.short(d.get('before'))} → {pls.short(d.get('after'))}" for d in pls.flat_diff(a, b)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--env", default="dev")
    ap.add_argument("--reuse", help="ids of probe sites from an earlier run: RESULTS_ID,DASHBOARD_ID (no new sites)")
    a = ap.parse_args()
    proj = Path(a.project)
    e_all = json.loads((proj / "environments.json").read_text(encoding="utf-8"))
    e = e_all["envs"][a.env]
    conn = H.load_connection(proj, a.env)
    H.assert_writable(e, conn, a.env)
    if e.get("role") != "dev":
        raise SystemExit(f"{a.env}: probes write only to role dev (role is {e.get('role')!r})")
    c = H.Client(conn["url"], H.resolve_key(conn, None))
    parent = e["parent_id"]

    def create(title, rt):
        st, js, text = c.call(f"/api/items/{parent}/createsite",
                              {"Title": title, "ReferenceType": rt, "Body": "", "SiteSettings": {}})
        if st != 200 or not js or not js.get("Id"):
            raise SystemExit(f"createsite {title}: HTTP {st} {text[:200]}")
        return int(js["Id"])

    def update(sid, title, rt, ss):
        st, _, text = c.call(f"/api/items/{sid}/updatesite", {"Title": title, "ReferenceType": rt, "Body": "", "SiteSettings": ss})
        if st != 200:
            raise SystemExit(f"updatesite {sid}: HTTP {st} {text[:200]}")

    def live(sid):
        return pls.site_data(c.export_site(sid))

    if a.reuse:
        id_a, id_b = (int(x) for x in a.reuse.split(","))
        for sid, (title, rt) in ((id_a, (TITLE_A, "Results")), (id_b, (TITLE_B, "Dashboards"))):
            cur = live(sid)
            if cur.get("Title") != title or cur.get("ReferenceType") != rt:
                raise SystemExit(f"--reuse {sid} is {cur.get('Title')!r} ({cur.get('ReferenceType')}), not the probe site "
                                 f"{title!r} ({rt}) — refusing to overwrite it")
        print(f"reusing {TITLE_A}={id_a}, {TITLE_B}={id_b} ({a.env})")
    else:
        id_a, id_b = create(TITLE_A, "Results"), create(TITLE_B, "Dashboards")
        print(f"created {TITLE_A}={id_a}, {TITLE_B}={id_b} under {parent} ({a.env})")
    sent = {id_a: settings_a(id_b), id_b: settings_b(id_a)}
    rts = {id_a: ("Results", TITLE_A), id_b: ("Dashboards", TITLE_B)}

    # the probe sites as managed sites of a temporary environment, so pls maps their ids to references
    env = copy.deepcopy(e)
    env["sites"] = {"probe_a": {"id": id_a, "title": TITLE_A}, "probe_b": {"id": id_b, "title": TITLE_B}}
    other = copy.deepcopy(env)
    other["sites"] = {"probe_a": {"id": 900001, "title": "x_a"}, "probe_b": {"id": 900002, "title": "x_b"}}
    names = {id_a: "probe_a", id_b: "probe_b"}
    ok = True
    for sid in (id_a, id_b):
        rt, title = rts[sid]
        print(f"\n=== {title} ({rt}, {sid})")
        update(sid, title, rt, sent[sid])
        first = live(sid)
        print("1. sent vs stored:")
        for line in section_report(sent[sid], first["SiteSettings"]):
            print(line)

        update(sid, title, rt, first["SiteSettings"])                  # raw round trip
        second = live(sid)
        d2 = diffs(first["SiteSettings"], second["SiteSettings"])
        print(f"2. raw round trip: {len(d2)} difference(s)")
        for x in d2[:10]:
            print("   ", x)

        with tempfile.TemporaryDirectory() as tmp:                     # pls round trip through files
            model = pls.logical({"Response": {"Data": second}}, env)
            pls.write_tree(model, Path(tmp) / names[sid])
            back = pls.read_tree(Path(tmp) / names[sid])
            files = sorted(str(p.relative_to(tmp)) for p in Path(tmp).rglob("*") if p.is_file())
            payload = pls.payload(back, env, names[sid])
            payload_other = pls.payload(back, other, names[sid])
        print(f"   files: {files}")
        update(sid, title, rt, payload["SiteSettings"])
        third = live(sid)
        d3 = diffs(second["SiteSettings"], third["SiteSettings"])
        print(f"3. pls round trip (unpack → files → pack → apply): {len(d3)} difference(s)")
        for x in d3[:10]:
            print("   ", x)

        blob_model = json.dumps(model, ensure_ascii=False)
        raw_left = [str(i) for i in (id_a, id_b) if str(i) in blob_model]
        refs = sorted(set(pls.REF_RE.findall(blob_model)))
        blob_other = json.dumps(payload_other, ensure_ascii=False)
        leaked = [str(i) for i in (id_a, id_b) if str(i) in blob_other]
        print(f"4. references in git model: {refs}; raw probe ids left in the model: {raw_left or 'none'}; "
              f"ids of this env left in a payload for another env: {leaked or 'none'}")
        ok &= not d2 and not d3 and not raw_left and not leaked
    print(f"\nRESULT: {'PASS — all components round-trip and map' if ok else 'DIFFERENCES — see above'}")
    print(f"Probe sites stay in {a.env} (ids {id_a}, {id_b}); a person deletes them in the UI.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
