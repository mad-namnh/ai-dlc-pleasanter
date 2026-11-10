"""Script tooling (BR7):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_scripts as SX  # noqa: E402

ENVS = {"managed_sites": ["anken"], "envs": {
    "dev": {"role": "dev", "sites": {"anken": {"id": 797, "title": "案件"}}},
    "prod": {"role": "prod", "sites": {"anken": {"id": 9001, "title": "案件"}}}}}


def export(scripts):
    return {"Response": {"Data": {"SiteId": 797, "Title": "案件", "ReferenceType": "Issues", "Body": "",
                                  "SiteSettings": {"Version": 1.017,
                                                   "Columns": [{"ColumnName": "ClassA", "LabelText": "顧客",
                                                                "Description": "siteId: 797 px"}],
                                                   "Scripts": scripts}}}}


class PureTest(unittest.TestCase):
    def tearDown(self):
        SX.LITERAL.clear()
        SX.REFERENCE.clear()

    def test_decimals_are_never_site_ids(self):
        s = "siteId = 797; d='M0 -4.797 2.127'; x=1.797-1.798; y=797.5; [[797]]"
        self.assertEqual(SX.replace_ids(s, {"797": "anken"}),
                         "siteId = ${site:anken}; d='M0 -4.797 2.127'; x=1.797-1.798; y=797.5; [[${site:anken}]]")

    def test_only_numbers_written_as_site_ids_are_replaced(self):
        # real lines of the PLAY BOARD app (site ids 103-120 collide with status codes, timings and colours)
        kept = ("const CASE_INFLUENCER_STATUS_SELECTION = 103;\nconst JUNCTION_STATUS_CODES = [102, 103, 104, 107];\n"
                "box-shadow: 0 2px 8px rgba(103,58,183,.35);\nsetTimeout(restoreHashtag, 103);\nconst maxAttempts = 103;\n"
                "103,ユーザー無効\n/* site 103 を変更しない */\npbWarn('[playboard][product-103] 失敗');\n")
        self.assertEqual(SX.replace_ids(kept, {"103": "x"}), kept)
        ids = ('_notiPickSiteId("NOTIFICATION_SITE_ID", 103);\nif ($p.siteId() === 103) {}\nitems.Get(103, "{}");\n'
               "$p.apiGet({ id: 103, done: f });\nfetch('/api/items/103/get');\nurl = '/api/items/' + 103;\n"
               '"SiteId": 103,\n[[103]]\nClassA~103,Title\nconst X_SITE_ID = 103;\n')
        out = SX.replace_ids(ids, {"103": "x"})
        self.assertNotIn("103", out)
        self.assertEqual(out.count("${site:x}"), 10)
        self.assertEqual(len(SX.possible_ids(kept, "103")), 8)          # every 103 in `kept` is listed, none replaced
        self.assertEqual(SX.possible_ids(ids, "103"), [])

    def test_possible_numbers_are_grouped_for_reading(self):
        g = SX.possible_group
        self.assertEqual(g("  // site 103 を変更しない"), "comment")
        self.assertEqual(g("  pbWarn('[playboard][product-104] 失敗');"), "log or message text")
        self.assertEqual(g("const CASE_INFLUENCER_STATUS_SELECTION = 103;"), "status or code value")
        self.assertEqual(g("setTimeout(restoreHashtag, 120);"), "timing or retry")
        self.assertEqual(g("box-shadow: 0 2px 8px rgba(103,58,183,.35);"), "colour or layout")
        self.assertEqual(g("        return 797;"), "other")                       # a person has to read this one

    def test_look_alike_names_and_calls_are_not_contexts(self):
        s = ("this.items.splice(103, 1); cart.items.push(103); updateStatus(siteId, 103); SITE_IDLE_TIMEOUT = 103; "
             "websiteId = 103; siteIdx = 103; 期間 1~103 日")
        self.assertEqual(SX.replace_ids(s, {"103": "x"}), s)

    def test_ids_across_lines_reversed_or_not_first_are_found(self):
        s = ("$p.apiGet({\n    id: 103,\n    done: f });\nitems.Get(\n  103);\nif (103 === $p.siteId()) {}\n"
             "$p.apiGet({ data: {}, id: 103 });\nconst ANKEN_SITE_ID = 103;\n")
        out = SX.replace_ids(s, {"103": "x"})
        self.assertNotIn("103", out)
        self.assertEqual(out.count("${site:x}"), 5)

    def test_hand_written_reference_outside_a_context_is_flagged(self):
        self.assertEqual(SX.unstable_refs("const ANKEN = ${site:anken};", "s"), ["anken"])
        self.assertEqual(SX.unstable_refs("const ANKEN_SITE_ID = ${site:anken}; items.Get(${site:anken});", "s"), [])

    def test_a_person_can_mark_a_possible_number_as_a_reference(self):
        s = "const ANKEN = 797; const LIMIT = 797;"
        self.assertEqual(SX.replace_ids(s, {"797": "anken"}, None, {"797": ["const ANKEN = 797"]}),
                         "const ANKEN = ${site:anken}; const LIMIT = 797;")

    def test_units_colours_and_names_are_never_site_ids(self):
        s = ("padding-left:110px; min-height:110px; sleep(110ms); w:110%; c:#110; item110; v110a; "
             "siteId=110; siteId=110px")
        self.assertEqual(SX.replace_ids(s, {"110": "haisosaki"}),
                         "padding-left:110px; min-height:110px; sleep(110ms); w:110%; c:#110; item110; v110a; "
                         "siteId=${site:haisosaki}; siteId=110px")
        self.assertEqual(SX.literal_left("padding:110px; siteId=110", "110"), [22])

    def test_recorded_literal_context_is_kept(self):
        lit = {"797": ["siteId: 797 (legacy)"]}
        s = "siteId = 797; siteId: 797 (legacy)"
        self.assertEqual(SX.replace_ids(s, {"797": "anken"}, lit), "siteId = ${site:anken}; siteId: 797 (legacy)")
        self.assertEqual(SX.literal_left(s, "797", lit), [9])
        self.assertEqual(SX.replace_ids("siteId: 797 (legacy)", {"797": "anken"}), "siteId: ${site:anken} (legacy)")  # no decision

    def test_result_does_not_depend_on_the_order_of_ids(self):
        lit = {"797": ["getSiteId(797) legacy"]}
        s = "siteId = 797; getSiteId(798); getSiteId(797) legacy"
        one = SX.replace_ids(s, {"798": "b", "797": "a"}, lit)
        two = SX.replace_ids(s, {"797": "a", "798": "b"}, lit)
        self.assertEqual(one, two)
        self.assertEqual(one, "siteId = ${site:a}; getSiteId(${site:b}); getSiteId(797) legacy")

    def test_short_or_generic_contexts_are_refused(self):
        self.assertIsNotNone(SX.check_context("797", "797"))
        self.assertIsNotNone(SX.check_context(", 797, 798, 1", "797"))
        self.assertIsNotNone(SX.check_context("x ${site:a} 797 abc", "797"))
        self.assertIsNone(SX.check_context("width 797 px", "797"))

    def test_syntax_check_with_node(self):
        if not SX.node_available():
            self.skipTest("node not installed")
        big = "var 顧客名 = 'あ';\n" * 30000                                                  # multi-byte across chunks
        errs = SX.syntax_errors([("ok", "if (x) { return 1; }\nvar s = '${site:anken}';", True), ("bad", "var a = ;\n", True),
                                 ("client-return", "return 1;", False), ("jp:1", big, False)])
        self.assertEqual([e["label"] for e in errs], ["bad", "client-return"])
        self.assertEqual(errs[0]["line"], 1)

    def test_xref(self):
        data = SX.xref({"Columns": [{"ColumnName": "ClassA", "LabelText": "顧客"}]},
                       {"Scripts": [{"Name": "a", "Body": "$p.set('ClassA', 1); items.Get(${site:kokyaku}); Status"}]})
        self.assertEqual(data["scripts"][0]["columns"], ["ClassA", "Status"])
        self.assertEqual(data["scripts"][0]["sites"], ["kokyaku"])
        self.assertEqual(data["columns"]["ClassA"], {"label": "顧客", "scripts": ["Scripts/a"]})


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        (self.r / "design").mkdir()
        self.cwd = os.getcwd()
        os.chdir(self.r)
        self.exp = self.r / "dev.json"
        self.exp.write_text(json.dumps(export([{"Id": 1, "Title": "lib", "All": True,
                                                "Body": "var siteId = 797;\r\nvar w = 'siteId: 797 px';\r\nvar s = 797;\r\n"}]),
                                        ensure_ascii=False),
                            encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"]), 0)

    def tearDown(self):
        os.chdir(self.cwd)
        SX.LITERAL.clear()
        SX.REFERENCE.clear()
        self.tmp.cleanup()

    def script_file(self):
        return next((self.r / "config/anken/scripts").glob("*.js"))

    def raw(self):
        with open(self.script_file(), encoding="utf-8", newline="") as fh:
            return fh.read()

    def test_keep_records_the_decision_and_every_command_respects_it(self):
        self.assertEqual(self.raw().count("${site:anken}"), 2)
        with self.assertRaises(pls.Fail):                                                   # a person must be named
            pls.main(["refs", "--site", "anken", "--keep", "siteId: 797 px"])
        with self.assertRaises(pls.Fail):                                                   # and their own words
            pls.main(["refs", "--site", "anken", "--keep", "siteId: 797 px", "--reason", "CSS width", "--by", "Nam"])
        self.assertEqual(pls.main(["refs", "--site", "anken", "--keep", "siteId: 797 px", "--reason", "CSS width", "--by", "Nam",
                                   "--quote", "797 there is a width in px, keep it"]), 0)
        self.assertEqual(self.raw(), "var siteId = ${site:anken};\r\nvar w = 'siteId: 797 px';\r\nvar s = 797;\r\n")   # CRLF kept
        rec = json.loads((self.r / "design/refs-literal.json").read_text(encoding="utf-8"))["literal"][0]
        self.assertEqual((rec["site"], rec["number"], rec["context"], rec["by"], rec["quote"]),
                         ("anken", "797", "siteId: 797 px", "Nam", "797 there is a width in px, keep it"))
        self.assertEqual(pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"]), 0)   # survives re-unpack
        self.assertIn("siteId: 797 px", self.raw())
        site = json.loads((self.r / "config/anken/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Columns"][0]["Description"], "siteId: ${site:anken} px")     # settings are never protected
        self.assertNotIn("L-REF-01", {i["rule"] for i in pls.lint(self.r)})
        p = pls.payload(pls.read_tree(self.r / "config/anken"), ENVS["envs"]["prod"], "anken")
        body = p["SiteSettings"]["Scripts"][0]["Body"]
        self.assertIn("siteId = 9001", body)                                                # real id follows the env
        self.assertIn("siteId: 797 px", body)                                               # the literal does not
        self.assertIn("var s = 797;", body)                                                 # a POSSIBLE number neither

    def test_ref_marks_a_possible_number_and_survives_unpack(self):
        with self.assertRaises(pls.Fail):                                                   # a person must be named
            pls.main(["refs", "--site", "anken", "--ref", "var s = 797;"])
        with self.assertRaises(pls.Fail):                                                   # and their own words
            pls.main(["refs", "--site", "anken", "--ref", "var s = 797;", "--reason", "site of 案件", "--by", "Nam", "--quote", " "])
        self.assertEqual(pls.main(["refs", "--site", "anken", "--ref", "var s = 797;", "--reason", "site of 案件", "--by", "Nam",
                                   "--quote", "yes, s is the 案件 site"]), 0)
        self.assertEqual(self.raw(), "var siteId = ${site:anken};\r\nvar w = 'siteId: ${site:anken} px';\r\nvar s = ${site:anken};\r\n")  # CRLF kept
        self.assertNotIn("L-REF-03", {i["rule"] for i in pls.lint(self.r)})       # the recorded reference covers it
        rec = json.loads((self.r / "design/refs-literal.json").read_text(encoding="utf-8"))["reference"][0]
        self.assertEqual(rec["quote"], "yes, s is the 案件 site")
        self.assertEqual((rec["number"], rec["context"], rec["by"]), ("797", "var s = 797;", "Nam"))
        self.assertEqual(pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"]), 0)   # survives re-unpack
        self.assertIn("var s = ${site:anken};", self.raw())
        # round trip: the payload read back (baseline, mark-applied) equals git — the reference is not seen as drift
        for env in ("dev", "prod"):
            pl = pls.payload(pls.read_tree(self.r / "config/anken"), ENVS["envs"][env], "anken")
            back = pls.payload_model(pl, ENVS["envs"][env], "anken")
            self.assertEqual(back["scripts"], pls.read_tree(self.r / "config/anken")["scripts"], env)
        p = pls.payload(pls.read_tree(self.r / "config/anken"), ENVS["envs"]["prod"], "anken")
        self.assertIn("var s = 9001;", p["SiteSettings"]["Scripts"][0]["Body"])
        # the decision was recorded with the dev number; an export of prod (id 9001) is read the same way
        prod = self.r / "prod.json"
        prod.write_text(json.dumps(export([{"Id": 1, "Title": "lib", "All": True, "Body": p["SiteSettings"]["Scripts"][0]["Body"]}])
                                   ).replace('"SiteId": 797', '"SiteId": 9001'), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(prod), "--env", "prod", "--site", "anken"]), 0)
        self.assertIn("var s = ${site:anken};", self.raw())

    def test_keep_needs_a_real_context(self):
        with self.assertRaises(pls.Fail):
            pls.main(["refs", "--site", "anken", "--keep", "797", "--reason", "x", "--by", "Nam", "--quote", "q"])
        self.assertFalse((self.r / "design/refs-literal.json").exists())

    def test_unknown_context_is_an_error(self):
        with self.assertRaises(pls.Fail):
            pls.main(["refs", "--site", "anken", "--keep", "nowhere 797 here", "--reason", "x", "--by", "Nam", "--quote", "q"])

    def test_broken_decisions_file_is_a_clear_error(self):
        (self.r / "design/refs-literal.json").write_text('{"literal": [{"site": "anken", "number": "797"}]}', encoding="utf-8")
        with self.assertRaises(pls.Fail):
            pls.main(["lint"])

    def test_lint_reports_syntax_errors(self):
        if not SX.node_available():
            self.skipTest("node not installed")
        self.script_file().write_text("var a = ;\n", encoding="utf-8")
        self.assertIn("L-SCR-02", {i["rule"] for i in pls.lint(self.r)})


if __name__ == "__main__":
    unittest.main()
