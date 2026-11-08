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
                                                                "Description": "width 797 px"}],
                                                   "Scripts": scripts}}}}


class PureTest(unittest.TestCase):
    def tearDown(self):
        SX.LITERAL.clear()

    def test_decimals_are_never_site_ids(self):
        s = "site 797; d='M0 -4.797 2.127'; x=1.797-1.798; y=797.5; [797]"
        self.assertEqual(SX.replace_ids(s, {"797": "anken"}),
                         "site ${site:anken}; d='M0 -4.797 2.127'; x=1.797-1.798; y=797.5; [${site:anken}]")

    def test_units_colours_and_names_are_never_site_ids(self):
        s = ("padding-left:110px; min-height:110px; sleep(110ms); w:110%; c:#110; item110; v110a; "
             "getSite(110); siteId=110; サイト110の一覧")
        self.assertEqual(SX.replace_ids(s, {"110": "haisosaki"}),
                         "padding-left:110px; min-height:110px; sleep(110ms); w:110%; c:#110; item110; v110a; "
                         "getSite(${site:haisosaki}); siteId=${site:haisosaki}; サイト${site:haisosaki}の一覧")
        self.assertEqual(SX.literal_left("padding:110px; id=110", "110"), [18])

    def test_recorded_literal_context_is_kept(self):
        lit = {"797": ["width 797 px"]}
        self.assertEqual(SX.replace_ids("site 797; width 797 px", {"797": "anken"}, lit), "site ${site:anken}; width 797 px")
        self.assertEqual(SX.literal_left("site 797; width 797 px", "797", lit), [5])
        self.assertEqual(SX.replace_ids("width 797 px", {"797": "anken"}), "width ${site:anken} px")     # no decision given

    def test_result_does_not_depend_on_the_order_of_ids(self):
        lit = {"797": ["calc(798, 797) mm"]}
        s = "a 797; calc(798, 797) mm"
        one = SX.replace_ids(s, {"798": "b", "797": "a"}, lit)
        two = SX.replace_ids(s, {"797": "a", "798": "b"}, lit)
        self.assertEqual(one, two)
        self.assertEqual(one, "a ${site:a}; calc(${site:b}, 797) mm")

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
                                                "Body": "var site = 797;\r\nvar w = 'width 797 px';\r\n"}]), ensure_ascii=False),
                            encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"]), 0)

    def tearDown(self):
        os.chdir(self.cwd)
        SX.LITERAL.clear()
        self.tmp.cleanup()

    def script_file(self):
        return next((self.r / "config/anken/scripts").glob("*.js"))

    def raw(self):
        with open(self.script_file(), encoding="utf-8", newline="") as fh:
            return fh.read()

    def test_keep_records_the_decision_and_every_command_respects_it(self):
        self.assertEqual(self.raw().count("${site:anken}"), 2)
        with self.assertRaises(pls.Fail):                                                   # a person must be named
            pls.main(["refs", "--site", "anken", "--keep", "width 797 px"])
        self.assertEqual(pls.main(["refs", "--site", "anken", "--keep", "width 797 px", "--reason", "CSS width", "--by", "Nam"]), 0)
        self.assertEqual(self.raw(), "var site = ${site:anken};\r\nvar w = 'width 797 px';\r\n")   # CRLF kept
        rec = json.loads((self.r / "design/refs-literal.json").read_text(encoding="utf-8"))["literal"][0]
        self.assertEqual((rec["site"], rec["number"], rec["context"], rec["by"]), ("anken", "797", "width 797 px", "Nam"))
        self.assertEqual(pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"]), 0)   # survives re-unpack
        self.assertIn("width 797 px", self.raw())
        site = json.loads((self.r / "config/anken/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Columns"][0]["Description"], "width ${site:anken} px")       # settings are never protected
        self.assertNotIn("L-REF-01", {i["rule"] for i in pls.lint(self.r)})
        p = pls.payload(pls.read_tree(self.r / "config/anken"), ENVS["envs"]["prod"], "anken")
        body = p["SiteSettings"]["Scripts"][0]["Body"]
        self.assertIn("site = 9001", body)                                                  # real id follows the env
        self.assertIn("width 797 px", body)                                                 # the literal does not

    def test_keep_needs_a_real_context(self):
        with self.assertRaises(pls.Fail):
            pls.main(["refs", "--site", "anken", "--keep", "797", "--reason", "x", "--by", "Nam"])
        self.assertFalse((self.r / "design/refs-literal.json").exists())

    def test_unknown_context_is_an_error(self):
        with self.assertRaises(pls.Fail):
            pls.main(["refs", "--site", "anken", "--keep", "nowhere 797 here", "--reason", "x", "--by", "Nam"])

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
