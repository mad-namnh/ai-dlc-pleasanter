"""`pls principals` binds a role of design/roles.json with "principal": "Dept" to a department, looked up through
/api/depts/get by its code (or name) — read only: departments are the customer's organisation and are never created,
also not with --create (ADR-0017 creates groups only). Fake Pleasanter on 127.0.0.1 only."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import test_http as TH  # noqa: E402

ROLES = {"roles": {"sales": {"principal": "Dept", "dept_code": "D-100"},
                   "office": {"principal": "Dept", "dept_name": "総務部"}}}


class BindDepartments(unittest.TestCase):
    tearDown = TH.HttpTest.tearDown

    def setUp(self):
        TH.HttpTest.setUp(self)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["principals"] = {"admin": "User,7"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (self.r / "design").mkdir()
        (self.r / "design/roles.json").write_text(json.dumps(ROLES, ensure_ascii=False), encoding="utf-8")
        self.fake.depts = [{"DeptId": 31, "DeptCode": "D-100", "DeptName": "営業部"},
                           {"DeptId": 32, "DeptCode": "D-1001", "DeptName": "営業部二課"},     # like-match neighbour
                           {"DeptId": 40, "DeptCode": "D-200", "DeptName": "総務部"}]

    def principals(self):
        return json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["dev"].get("principals") or {}

    def writes(self):
        return [p for p, _ in self.fake.calls if not p.endswith("/get")]

    def test_departments_are_bound_by_code_or_name_exactly(self):
        self.assertEqual(pls.main(["principals", "--env", "dev"]), 0)
        self.assertEqual(self.principals(), {"admin": "User,7", "sales": "Dept,31", "office": "Dept,40"})
        self.assertEqual(self.writes(), [])

    def test_a_numeric_code_is_read_as_text(self):
        (self.r / "design/roles.json").write_text(json.dumps({"roles": {"sales": {"principal": "Dept", "dept_code": 300}}}),
                                                 encoding="utf-8")
        self.fake.depts.append({"DeptId": 50, "DeptCode": "300", "DeptName": "x"})
        self.assertEqual(pls.main(["principals", "--env", "dev"]), 0)
        self.assertEqual(self.principals()["sales"], "Dept,50")

    def test_a_missing_department_is_reported_and_never_created(self):
        self.fake.depts = [d for d in self.fake.depts if d["DeptId"] != 40]
        for argv in (["principals", "--env", "dev"], ["principals", "--env", "dev", "--create", "--yes"]):
            self.assertEqual(pls.main(argv), 1, argv)
        self.assertNotIn("office", self.principals())
        self.assertEqual(self.writes(), [])

    def test_an_ambiguous_department_is_refused(self):
        self.fake.depts.append({"DeptId": 41, "DeptCode": "D-201", "DeptName": "総務部"})
        with self.assertRaisesRegex(pls.Fail, "matches 2 departments"):
            pls.main(["principals", "--env", "dev"])
        self.assertNotIn("office", self.principals())

    def test_a_failed_lookup_is_a_refusal(self):
        real = self.fake.handle

        def broken(path, body):
            return (500, {"Message": "boom"}) if path == "/api/depts/get" else real(path, body)
        self.fake.handle = broken
        with self.assertRaisesRegex(pls.Fail, "lookup of department"):
            pls.main(["principals", "--env", "dev"])


if __name__ == "__main__":
    unittest.main()
