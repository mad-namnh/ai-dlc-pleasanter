"""Comparing one site across environments (BR5):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_compare as CMP  # noqa: E402

ENVS = {"managed_sites": ["anken", "kokyaku"], "envs": {
    "dev": {"role": "dev", "sites": {"anken": {"id": 797}, "kokyaku": {"id": 500}}, "principals": {"soumu": "Group,2"}},
    "prod": {"role": "prod", "sites": {"anken": {"id": 9001}, "kokyaku": {"id": 9500}}, "principals": {"soumu": "Group,77"}}}}


def site(sid, cust, extra=None, perms=None):
    ss = {"Version": 1.017, "Columns": [{"ColumnName": "ClassA", "LabelText": "顧客", "ChoicesText": f"[[{cust}]]"},
                                        {"ColumnName": "NumA", "LabelText": "金額"}],
          "Notifications": [{"Id": 1, "Type": 1, "Address": "[Manager]"}]}
    ss.update(extra or {})
    return {"SiteId": sid, "Title": f"案件一覧 {sid}", "ReferenceType": "Issues", "Body": "", "InheritPermission": sid,
            "Permissions": perms or [], "SiteSettings": ss}


def package(s, include_notifications=True, group=77):
    ss = dict(s["SiteSettings"])
    if not include_notifications:
        ss.pop("Notifications")
    return {"HeaderInfo": {"AssemblyVersion": "1.5.1.0", "BaseSiteId": s["SiteId"], "PackageTime": "2026-11-05T12:00:00",
                           "IncludeNotifications": include_notifications, "IncludeSitePermission": True},
            "Sites": [dict(s, SiteSettings=ss)],
            "Permissions": [{"SiteId": s["SiteId"], "Permissions": [{"ReferenceId": s["SiteId"], "DeptId": 0, "GroupId": group,
                                                                     "UserId": 0, "PermissionType": 31}]}],
            "PermissionIdList": {"GroupIdList": [{"GroupId": group, "GroupName": "総務"}], "UserIdList": [], "DeptIdList": []}}


class CompareTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def write(self, name, doc):
        (self.r / name).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return name

    def run_compare(self, *sources):
        args = ["env-compare", "--site", "anken"]
        for s in sources:
            args += ["--source", s]
        code = pls.main(args)
        return code, next((self.r / "ops/env-compare").glob("*-anken.md")).read_text(encoding="utf-8")

    def test_ids_that_differ_per_environment_are_not_differences(self):
        dev = self.write("dev.json", {"Response": {"Data": site(797, 500, perms=["Group,2,31"])}})
        prod = self.write("prod.json", package(site(9001, 9500)))
        code, rep = self.run_compare(f"dev={dev}", f"prod={prod}")
        self.assertEqual(code, 0, rep)
        self.assertIn("No differences", rep)
        self.assertIn("Pleasanter 1.5.1.0", rep)

    def test_content_unmapped_id_and_missing_package_part_are_classified(self):
        dev = self.write("dev.json", {"Response": {"Data": site(797, 500, perms=["Group,2,31"])}})
        prod_site = site(9001, 9500, extra={"Links": [{"ColumnName": "ClassA", "SiteId": 9777}]})
        prod_site["SiteSettings"]["Columns"][1]["LabelText"] = "金額(税込)"
        dev_site = json.loads(json.dumps(site(797, 500, extra={"Links": [{"ColumnName": "ClassA", "SiteId": 777}]}, perms=["Group,2,31"])))
        dev = self.write("dev.json", {"Response": {"Data": dev_site}})
        prod = self.write("prod.json", package(prod_site, include_notifications=False))
        code, rep = self.run_compare(f"dev={dev}", f"prod={prod}")
        self.assertEqual(code, 1)
        self.assertRegex(rep, r"\| content \| `settings.Columns.*LabelText`")
        self.assertRegex(rep, r"\| id-like \| `settings.Links")                # 777 vs 9777: unmanaged site on both sides
        self.assertRegex(rep, r"\| not-in-package \| `settings.Notifications")
        self.assertIn("exported without Notifications", rep)

    def test_git_as_a_source(self):
        dev = self.write("dev.json", {"Response": {"Data": site(797, 500, perms=["Group,2,31"])}})
        self.assertEqual(pls.main(["unpack", dev, "--env", "dev", "--site", "anken"]), 0)
        code, _ = self.run_compare("git", f"dev={dev}")
        self.assertEqual(code, 0)

    def test_version_from_a_package_needs_no_connection(self):
        prod = self.write("prod.json", package(site(9001, 9500)))
        self.assertEqual(pls.main(["version", "--env", "prod", "--from-package", prod]), 0)
        rec = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["prod"]["pleasanter"]
        self.assertEqual((rec["app"], rec["schema"], rec["build"]), ("1.5.1.0", 1.017, None))
        self.assertTrue(rec["source"].startswith("site package"))

    def test_real_changes_are_never_called_id_like(self):
        def cls(path, a, b):
            return CMP.classify({"path": path, "before": a, "after": b}, [], {"5432"})
        self.assertEqual(cls("settings.Columns[NumA].Max", 100, 200), "content")          # a limit, not an id
        self.assertEqual(cls("scripts.ServerScripts[calc].Body", "if(x>100)", "if(x>200)"), "content")
        self.assertEqual(cls("settings.Version", 1.017, 1.018), "content")
        self.assertEqual(cls("settings.Columns[ClassA].ChoicesText", "[[777]]", "[[9777]]"), "id-like")
        self.assertEqual(cls("settings.Links[ClassA].SiteId", 777, 9777), "id-like")
        self.assertEqual(cls("settings.Columns[ClassA].Description", "上限 10 件", "上限 20 件"), "content")   # short numbers
        self.assertEqual(cls("settings.Notifications[1].Address", "port 5432", "port 6543"), "content")  # an env value
        self.assertEqual(CMP.classify({"path": "settings.Processes[a:1].Notifications[1]", "before": 1, "after": None},
                                      ["Notifications"]), "not-in-package")

    def test_bad_inputs_are_errors_not_differences(self):
        dev = self.write("dev.json", {"Response": {"Data": site(797, 500)}})
        with self.assertRaises(pls.Fail):
            self.run_compare(f"dev={dev}", "prod=missing.json")
        with self.assertRaises(pls.Fail):
            self.run_compare(f"dev={dev}", "dev=git")
        two = package(site(9001, 9500))
        two["Sites"].append(dict(two["Sites"][0], SiteId=9002, Title="別サイト"))
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["prod"]["sites"].pop("anken")                                       # not mapped yet
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        prod = self.write("prod.json", two)
        with self.assertRaises(pls.Fail):                                               # never guess the site
            self.run_compare(f"dev={dev}", f"prod={prod}")

    def test_permissions_compared_only_when_both_sides_have_them(self):
        dev = self.write("dev.json", {"Response": {"Data": site(797, 500, perms=["Group,2,31"])}})
        self.assertEqual(pls.main(["unpack", dev, "--env", "dev", "--site", "anken"]), 0)
        (self.r / "config/anken/permissions.json").unlink()                              # opt-in (ADR-0006)
        code, rep = self.run_compare("git", f"dev={dev}")
        self.assertEqual(code, 0, rep)
        self.assertIn("permissions not compared", rep)

    def test_git_with_scripts_matches_the_export(self):
        s = site(797, 500, extra={"ServerScripts": [{"Id": 1, "Name": "calc", "BeforeUpdate": True, "Body": "var a = 1;\r\n"}],
                                  "Views": [{"Id": 1, "Name": "v"}]}, perms=["Group,2,31"])
        dev = self.write("dev.json", {"Response": {"Data": s}})
        self.assertEqual(pls.main(["unpack", dev, "--env", "dev", "--site", "anken"]), 0)   # not canonicalised yet
        code, rep = self.run_compare("git", f"dev={dev}")
        self.assertEqual(code, 0, rep)

    def test_version_from_package_keeps_the_build_only_for_the_same_version(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["prod"]["pleasanter"] = {"app": "1.5.1.0", "build": "201510", "schema": 1.017}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        prod = self.write("prod.json", package(site(9001, 9500)))
        self.assertEqual(pls.main(["version", "--env", "prod", "--from-package", prod]), 0)
        rec = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["prod"]["pleasanter"]
        self.assertEqual(rec["build"], "201510")                                          # same app → token kept
        old = package(site(9001, 9500))
        old["HeaderInfo"]["PackageTime"] = "2026-01-01T00:00:00"
        with self.assertRaises(pls.Fail):                                               # older package refused
            pls.main(["version", "--env", "prod", "--from-package", self.write("old.json", old)])
        with self.assertRaises(pls.Fail):
            pls.main(["version", "--env", "prod", "--from-package", prod, "--app", "1.6.0.0"])

    def test_package_reader(self):
        doc, info = CMP.from_package(package(site(9001, 9500)))
        self.assertEqual(doc["Response"]["Data"]["Permissions"], ["Group,77,31"])
        self.assertEqual(info["principal_names"], {"Group,77": "総務"})
        with self.assertRaises(ValueError):
            CMP.from_package(package(site(9001, 9500)), 1234)


if __name__ == "__main__":
    unittest.main()
