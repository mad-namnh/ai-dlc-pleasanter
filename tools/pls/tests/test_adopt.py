"""Adopting an existing site (BR4):  python -m unittest discover -s tools/pls/tests -v"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import pls_adopt as AD  # noqa: E402
import test_http as TH  # noqa: E402

OLD = 903     # an existing customer site, not created by the framework


class PureTest(unittest.TestCase):
    def test_referenced_sites(self):
        ss = {"Links": [{"ColumnName": "ClassA", "SiteId": 500}], "Columns": [{"ColumnName": "ClassB", "ChoicesText": "[[600]]"},
              {"ColumnName": "ClassC", "ChoicesText": "[[700,Filter]]"}], "Summaries": [{"SiteId": 800, "Id": 1}],
              "Processes": [{"Id": 1, "CurrentStatus": 100}], "UseSearchFilter": True}
        self.assertEqual(AD.referenced_sites(ss), {500, 600, 700, 800})

    def test_script_id_uses_lists_possible_numbers_as_kept(self):
        raw = {"Scripts": [{"Id": 1, "Title": "lib", "Body": "var siteId = 797;\nvar path = 'M10 797 2.127 6';"}]}
        uses = AD.script_id_uses(raw, {"797": "anken"})
        self.assertEqual(len(uses), 2)
        self.assertIn("→ ${site:anken}", uses[0])
        self.assertTrue(uses[1].startswith("POSSIBLE — kept as written") and "line 2" in uses[1])

    def test_unsafe_and_duplicate_script_names_keep_every_body(self):
        import tempfile
        model = {"meta": {}, "settings": {}, "permissions": None, "scripts": {"ServerScripts": [
            {"Id": 1, "Name": "calc", "Body": "A();"}, {"Id": 2, "Name": "calc", "Body": "B();"},
            {"Id": 3, "Name": "計算: 更新?", "Body": "C();"}, {"Id": 4, "Name": "../x", "Body": "D();"}]}}
        with tempfile.TemporaryDirectory() as t:
            pls.write_tree(model, Path(t) / "s")
            back = pls.read_tree(Path(t) / "s")["scripts"]["ServerScripts"]
            self.assertEqual([x["Body"] for x in back], ["A();", "B();", "C();", "D();"])
            self.assertEqual([x["Name"] for x in back], ["calc", "calc", "計算: 更新?", "../x"])   # real names kept
            self.assertFalse((Path(t) / "x.js").exists())                                       # nothing outside

    def test_raw_principals(self):
        self.assertEqual(AD.raw_principals({"entries": ["${principal:admin},511", "Group,42,31"]}), ["Group,42,31"])


class CliTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def add_old_site(self):
        self.fake.sites[OLD] = {
            "SiteId": OLD, "Title": "案件一覧", "ReferenceType": "Issues", "UpdatedTime": "t0", "Body": "",
            "InheritPermission": OLD, "Permissions": ["User,1,511", "Group,42,31"],
            "SiteSettings": {"Version": 1.017, "ReferenceType": "Issues",
                             "Columns": [{"ColumnName": "ClassA", "LabelText": "顧客", "ChoicesText": f"[[{TH.EQ}]]"},
                                         {"ColumnName": "NumA", "LabelText": "金額"}],
                             "EditorColumnHash": {"General": ["IssueId", "ClassA", "NumA", "DateB"]},
                             "Links": [{"ColumnName": "ClassA", "SiteId": 4242}],
                             "Tabs": [{"Id": 1, "LabelText": "詳細"}],
                             "ServerScripts": [{"Id": 1, "Name": "calc", "BeforeUpdate": True, "Body": "var x = 1;"}]}}

    def test_adopt_is_read_only_and_gives_a_drift_baseline(self):
        self.add_old_site()
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"]), 0)
        calls = self.fake.calls[n:]
        self.assertEqual([p for p, _ in calls], [f"/api/items/{OLD}/getsite"])        # one read, nothing else
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        self.assertEqual(envs["envs"]["dev"]["sites"]["anken"], {"id": OLD, "title": "案件一覧"})
        self.assertIn("anken", envs["managed_sites"])
        site = json.loads((self.r / "config/anken/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Columns"][0]["ChoicesText"], "[[${site:equipment}]]")   # managed site mapped
        ledger = json.loads((self.r / "design/slot-ledger.json").read_text(encoding="utf-8"))["anken"]
        self.assertEqual(sorted(ledger), ["ClassA", "DateB", "NumA"])                   # editor-only slot too
        self.assertEqual({v["zone"] for v in ledger.values()}, {"customer"})
        report = next((self.r / "ops/adopt").glob("*-dev-anken.md")).read_text(encoding="utf-8")
        self.assertIn("Tabs (no round-trip evidence)", report)
        self.assertIn("- 4242", report)                                                 # unmanaged reference
        self.assertIn("Group,42,31", report)
        self.assertIn("- calc", report)
        export = next((self.r / ".pls/exports").glob("dev-anken-adopt-*.json"))
        self.assertEqual(pls.main(["drift", str(export), "--env", "dev", "--site", "anken"]), 0)

    def test_failure_leaves_nothing_registered_and_a_rerun_works(self):
        self.add_old_site()
        orig = pls.write_tree
        def boom(*a, **k):
            raise OSError("disk full")
        pls.write_tree = boom
        try:
            with self.assertRaises(OSError):
                pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"])
        finally:
            pls.write_tree = orig
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        self.assertNotIn("anken", envs["envs"]["dev"]["sites"])
        self.assertFalse((self.r / "config/anken").exists())
        self.assertFalse(list((self.r / "releases").glob("A-*")) if (self.r / "releases").exists() else [])
        self.assertEqual(pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"]), 0)

    def test_secrets_refuse_before_anything_is_written(self):
        self.add_old_site()
        self.fake.sites[OLD]["SiteSettings"]["ServerScripts"][0]["Body"] = "var password = 'abcdefghijklmnop';"
        with self.assertRaises(pls.Fail):
            pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"])
        self.assertFalse((self.r / "config/anken").exists())

    def test_secret_detector_flags_literals_not_concatenation(self):
        rx = pls.SECRET_RES["assigned-secret"]

        def hit(body):
            return bool(rx.search(json.dumps({"Body": body}, ensure_ascii=False)))     # as adopt and lint see it
        for body in ("var password = 'abcdefghijklmnop';", 'const API_KEY = "abcdEFGH12345678";',
                     '"token": "abcdefghijklmnopq"'):
            self.assertTrue(hit(body), body)
        for body in ("url = base + '?access_token=' +\n    urlEncode(accessToken);\nvar g = 0; while (url !== '')",
                     "var token = 'Bearer ' + x + 'abcdefghijklmn'", "password: 'short'"):
            self.assertFalse(hit(body), body)                                  # false alarm seen on a brownfield trial app

    def test_second_environment_registers_the_id_only_and_bootstrap_skips_it(self):
        self.add_old_site()
        self.assertEqual(pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"]), 0)
        before = (self.r / "config/anken/site.json").read_text(encoding="utf-8")
        copy_ = json.loads(json.dumps(self.fake.sites[OLD]))
        copy_.update(SiteId=OLD + 1, Title="案件一覧(本番)")
        copy_["SiteSettings"]["Columns"][1]["LabelText"] = "金額(税込)"
        self.fake.sites[OLD + 1] = copy_
        self.assertEqual(pls.main(["adopt", "--env", "prod", "--site", str(OLD + 1), "--name", "anken"]), 0)
        self.assertEqual((self.r / "config/anken/site.json").read_text(encoding="utf-8"), before)    # git untouched
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        self.assertEqual(envs["envs"]["prod"]["sites"]["anken"]["id"], OLD + 1)
        self.assertEqual(envs["managed_sites"].count("anken"), 1)
        report = next((self.r / "ops/adopt").glob("*-prod-anken.md")).read_text(encoding="utf-8")
        self.assertIn("Differences from config/anken", report)
        self.assertIn("金額(税込)", report)
        envs["envs"]["stg"] = {"role": "stg", "parent_id": 5, "sites": {}}
        envs["managed_sites"] = ["anken"]                      # only the adopted site matters for this check
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertEqual(pls.main(["bootstrap-plan", "--env", "stg", "--release", "B-1"]), 0)    # skipped, not an error

    def test_adopt_never_overwrites(self):
        self.add_old_site()
        self.assertEqual(pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"]), 0)
        with self.assertRaises(pls.Fail):
            pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "anken"])
        with self.assertRaises(pls.Fail):
            pls.main(["adopt", "--env", "dev", "--site", str(OLD), "--name", "other"])     # same site, other name
        with self.assertRaises(pls.Fail):
            pls.main(["adopt", "--env", "dev", "--site", str(TH.EQ), "--name", "Bad Name"])


class PackageTest(unittest.TestCase):
    """pls adopt-package: every site of a UI site package, read only, referenced sites first."""
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def sites(self):
        master = {"SiteId": 911, "Title": "企業マスタ", "ReferenceType": "Results", "ParentId": 900, "UpdatedTime": "t0",
                  "Body": "", "SiteSettings": {"Version": 1.017, "ReferenceType": "Results", "Columns": [{"ColumnName": "Title"}]}}
        case = {"SiteId": 910, "Title": "案件一覧", "ReferenceType": "Issues", "ParentId": 900, "UpdatedTime": "t0", "Body": "",
                "SiteSettings": {"Version": 1.017, "ReferenceType": "Issues",
                                 "Columns": [{"ColumnName": "ClassA", "LabelText": "企業",
                                              "ChoicesText": '[{"SiteId": 911, "Lookups": []}]'}],
                                 "Links": [{"ColumnName": "ClassA", "SiteId": 911}],
                                 "Scripts": [{"Id": 1, "Title": "lib", "Body": "const COMPANY_SITE_ID = 911; const S = 911;"}]}}
        secret = {"SiteId": 912, "Title": "下書き", "ReferenceType": "Results", "ParentId": 900, "UpdatedTime": "t0", "Body": "",
                  "SiteSettings": {"Version": 1.017, "ReferenceType": "Results",
                                   "ServerScripts": [{"Id": 1, "Name": "x", "Body": "var token = 'abcdefghijklmnopqrstu';"}]}}
        folder = {"SiteId": 900, "Title": "アプリ", "ReferenceType": "Sites", "ParentId": 0, "UpdatedTime": "t0", "Body": "",
                  "SiteSettings": {"Version": 1.017, "ReferenceType": "Sites"}}
        for s in (master, case, secret, folder):
            self.fake.sites[s["SiteId"]] = s
        pkg = self.r / ".pls/pkg.json"
        pkg.write_text(json.dumps({"HeaderInfo": {"BaseSiteId": 900}, "Sites": [folder, case, master, secret]}), encoding="utf-8")
        return pkg

    def test_names_are_required_then_referenced_sites_come_first_and_only_reads(self):
        pkg = self.sites()
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["adopt-package", "--env", "dev", "--package", str(pkg)]), 1)    # no names yet
        self.assertEqual(self.fake.calls[n:], [])
        self.assertFalse((self.r / "config/anken").exists())
        names = self.r / ".pls/names.json"
        names.write_text(json.dumps({"910": "anken", "911": "kigyo", "下書き": None, "900": "app"}), encoding="utf-8")
        self.assertEqual(pls.main(["adopt-package", "--env", "dev", "--package", str(pkg), "--names", str(names)]), 0)
        calls = [p for p, _ in self.fake.calls[n:]]
        self.assertTrue(all(p.endswith("/getsite") for p in calls))                        # read only
        self.assertLess(calls.index("/api/items/911/getsite"), calls.index("/api/items/910/getsite"))   # referenced first
        self.assertNotIn("/api/items/912/getsite", calls)                                  # skipped (null)
        site = json.loads((self.r / "config/anken/site.json").read_text(encoding="utf-8"))
        self.assertIn("${site:kigyo}", site["Columns"][0]["ChoicesText"])
        body = next((self.r / "config/anken/scripts").glob("*.js")).read_text(encoding="utf-8")
        self.assertIn("COMPANY_SITE_ID = ${site:kigyo}", body)
        self.assertIn("const S = 911;", body)                                              # POSSIBLE, kept as written

    def test_a_failing_site_does_not_stop_the_others(self):
        pkg = self.sites()
        names = self.r / ".pls/names.json"
        names.write_text(json.dumps({"910": "anken", "911": "kigyo", "912": "draft", "900": "app"}), encoding="utf-8")
        self.assertEqual(pls.main(["adopt-package", "--env", "dev", "--package", str(pkg), "--names", str(names)]), 1)
        self.assertTrue((self.r / "config/anken/site.json").exists())
        self.assertFalse((self.r / "config/draft").exists())                              # refused: secret (I7)

    def test_an_unexpected_error_on_one_site_is_reported_and_the_others_continue(self):
        pkg = self.sites()
        names = self.r / ".pls/names.json"
        names.write_text(json.dumps({"910": "anken", "911": "kigyo", "下書き": None, "900": "app"}), encoding="utf-8")
        real = pls.adopt

        def flaky(r, env, name, exp, today, stamp):
            if name == "kigyo":
                raise KeyError("SiteSettings")
            return real(r, env, name, exp, today, stamp)
        pls.adopt = flaky
        try:
            self.assertEqual(pls.main(["adopt-package", "--env", "dev", "--package", str(pkg), "--names", str(names)]), 1)
        finally:
            pls.adopt = real
        self.assertTrue((self.r / "config/anken/site.json").exists())
        self.assertFalse((self.r / "config/kigyo").exists())

    def test_second_environment_reuses_names_by_title(self):
        pkg = self.sites()
        names = self.r / ".pls/names.json"
        names.write_text(json.dumps({"910": "anken", "911": "kigyo", "下書き": None, "900": "app"}), encoding="utf-8")
        self.assertEqual(pls.main(["adopt-package", "--env", "dev", "--package", str(pkg), "--names", str(names)]), 0)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg"] = {"role": "stg", "sites": {}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["stg"] = c["dev"]
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        copy = json.loads(pkg.read_text(encoding="utf-8"))
        for s in copy["Sites"]:                                                            # the same app, new ids
            s["SiteId"] += 100
            s["ParentId"] = s["ParentId"] + 100 if s["ParentId"] else 0
            self.fake.sites[s["SiteId"]] = dict(s)
        p2 = self.r / ".pls/pkg-stg.json"
        p2.write_text(json.dumps(copy), encoding="utf-8")
        self.assertEqual(pls.main(["adopt-package", "--env", "stg", "--package", str(p2), "--names", str(names)]), 0)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        self.assertEqual(envs["envs"]["stg"]["sites"]["anken"]["id"], 1010)
        self.assertEqual(envs["envs"]["stg"]["sites"]["kigyo"]["id"], 1011)

    def test_plan_without_names_uses_known_titles(self):
        pkg = {"Sites": [{"SiteId": 1, "Title": "A", "ParentId": 0}, {"SiteId": 2, "Title": "B", "ParentId": 1,
                          "SiteSettings": {"Links": [{"SiteId": 3}]}}, {"SiteId": 3, "Title": "C", "ParentId": 1}]}
        plan = AD.package_plan(pkg, {"A": {"a"}, "B": {"b"}, "C": {"c"}}, {})
        self.assertEqual([n for _, n, _ in plan["order"]], ["a", "c", "b"])
        self.assertEqual(AD.package_plan(pkg, {"A": {"a", "a2"}}, {})["missing"][0], (1, "A"))


if __name__ == "__main__":
    unittest.main()
