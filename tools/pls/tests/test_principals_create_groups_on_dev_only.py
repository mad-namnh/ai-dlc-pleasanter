"""`pls principals --env dev --create` (ADR-0017): the groups of design/roles.json that do not exist yet are created
on a dev environment and bound; never on stg, prod or a sandbox, never without allow_write or a confirmation, never
over an ambiguous name (Pleasanter 1.5.2 does not refuse a duplicate group name), never an update or delete."""
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_http as H  # noqa: E402
import test_http as TH  # noqa: E402

ROLES = {"roles": {"somu": {"principal": "Group", "group_name": "zz_demo_総務"},
                   "audit": {"principal": "Group", "group_name": "zz_demo_監査"}}}


class CreateGroups(unittest.TestCase):
    tearDown = TH.HttpTest.tearDown                     # the fake server only, not HttpTest's own tests

    def setUp(self):
        TH.HttpTest.setUp(self)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["principals"] = {"admin": "User,7"}
        envs["envs"]["stg"] = {"role": "stg", "sites": {}}
        envs["envs"]["sbx"] = {"role": "dev", "sandbox_of": "dev", "connection": "dev", "sites": {}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        conns = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        conns["stg"] = dict(conns["dev"])
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")
        (self.r / "design").mkdir()
        (self.r / "design/roles.json").write_text(json.dumps(ROLES, ensure_ascii=False), encoding="utf-8")

    def group_writes(self):
        return [p for p, _ in self.fake.calls if p.startswith("/api/groups/") and not p.endswith("/get")]

    def principals(self, env="dev"):
        return json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"][env].get("principals") or {}

    def events(self):
        return [json.loads(x) for f in sorted((self.r / "ops/log").glob("*.jsonl"))
                for x in f.read_text(encoding="utf-8").splitlines()]

    def test_the_missing_group_is_created_with_the_operator_and_bound(self):
        self.assertEqual(pls.main(["principals", "--env", "dev", "--create", "--yes"]), 0)
        self.assertEqual(self.group_writes(), ["/api/groups/create"])                   # only the missing one
        body = self.fake.group_bodies[0]
        self.assertEqual((body["GroupName"], body["GroupMembers"]), ("zz_demo_監査", ["User,7,False"]))
        new = self.fake.groups[-1]["GroupId"]
        self.assertEqual(self.principals(), {"admin": "User,7", "somu": "Group,374", "audit": f"Group,{new}"})
        ev = [e for e in self.events() if e.get("cmd") == "principals"][-1]
        self.assertEqual((ev["writes"], ev["env"], ev["metrics"]), (True, "dev", {"groups_created": [new]}))
        self.assertEqual(pls.main(["principals", "--env", "dev", "--create", "--yes"]), 0)   # second run: nothing to do
        self.assertEqual(self.group_writes(), ["/api/groups/create"])

    def test_without_create_nothing_is_written(self):
        self.assertEqual(pls.main(["principals", "--env", "dev"]), 1)                   # 監査 missing, reported
        self.assertEqual(self.group_writes(), [])

    def test_stg_prod_and_sandboxes_are_refused_before_any_request(self):
        for env in ("stg", "prod", "sbx"):
            n = len(self.fake.calls)
            with self.assertRaises(pls.Fail, msg=env):
                pls.main(["principals", "--env", env, "--create", "--yes"])
            self.assertEqual(self.fake.calls[n:], [], env)

    def test_no_write_without_allow_write(self):
        conns = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        conns["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "REFUSED"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertEqual(self.group_writes(), [])

    def test_not_confirmed_creates_nothing(self):
        with self.assertRaisesRegex(pls.Fail, "not confirmed"):                      # no --yes and no terminal
            pls.main(["principals", "--env", "dev", "--create"])
        self.assertEqual(self.group_writes(), [])

    def test_an_ambiguous_name_is_refused_also_when_only_binding(self):
        self.fake.groups.append({"GroupId": 999, "GroupName": "zz_demo_総務"})          # the server allows duplicates
        for argv in (["principals", "--env", "dev"], ["principals", "--env", "dev", "--create", "--yes"]):
            with self.assertRaisesRegex(pls.Fail, "matches 2 groups"):
                pls.main(argv)
        self.assertEqual(self.group_writes(), [])
        self.assertNotIn("somu", self.principals())

    def test_a_failed_lookup_is_never_taken_as_missing(self):
        real = self.fake.handle

        def broken(path, body):
            return (500, {"Message": "boom"}) if path == "/api/groups/get" else real(path, body)
        self.fake.handle = broken
        with self.assertRaisesRegex(pls.Fail, "lookup of group .* failed"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertEqual(self.group_writes(), [])

    def test_the_operator_must_be_bound_first(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["principals"] = {}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "principals.admin"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertEqual(self.group_writes(), [])
        self.assertEqual(self.principals(), {"somu": "Group,374"})                     # binding of existing ones kept

    def test_a_refused_create_stops_and_binds_nothing(self):
        real = self.fake.handle
        self.fake.handle = lambda p, b: (403, {"Message": "forbidden"}) if p == "/api/groups/create" else real(p, b)
        with self.assertRaisesRegex(pls.Fail, "answered HTTP 403"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertNotIn("audit", self.principals())

    def test_a_create_that_leaves_two_groups_is_reported_not_retried(self):
        real = self.fake.handle
        sent = []

        def twice(path, body):
            if path == "/api/groups/create":
                sent.append(path)
                real(path, body)                                                       # e.g. a parallel run
            return real(path, body)
        self.fake.handle = twice
        with self.assertRaisesRegex(pls.Fail, "lookup found .*nothing is retried"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertNotIn("audit", self.principals())
        self.assertEqual(len(sent), 1)                                                 # one request sent
        ev = [e for e in self.events() if e.get("cmd") == "principals"][-1]
        self.assertEqual(len(ev["metrics"]["groups_created"]), 1)                     # the id it was answered with

    def test_an_uncertain_create_tells_the_person_to_bind_without_create(self):
        class Uncertain:
            def call(self, path, body=None):
                return 200, {"Response": {"Data": []}}, ""

            def create_group(self, *a):
                raise H.UncertainOutcome("/api/groups/create: no complete answer")
        with self.assertRaisesRegex(pls.Fail, "may exist now.*without --create"):
            pls.bind_principals(self.r, "dev", Uncertain(), create=True,
                                conn={"allow_write": True}, yes=True)

    def test_only_groups_with_a_final_name_are_created(self):
        for spec in ({"principal": "Dept", "group_name": "zz_dept"},           # not a group
                     {"principal": "Group"},                                   # no name: never the role key
                     {"principal": "Group", "group_name": "<group name>"},     # template placeholder
                     {"principal": "Group", "group_name": " zz_pad "}):        # surrounding spaces
            (self.r / "design/roles.json").write_text(json.dumps({"roles": {"x": spec}}), encoding="utf-8")
            with self.assertRaisesRegex(pls.Fail, "not a group with a final name", msg=spec):
                pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertEqual(self.group_writes(), [])

    def test_an_answer_of_more_than_one_page_is_unknown_not_missing(self):
        real = self.fake.handle

        def paged(path, body):
            code, js = real(path, body)
            if path == "/api/groups/get":                                   # the exact group is on a later page
                js = {"Response": {"Data": [], "TotalCount": 250}}
            return code, js
        self.fake.handle = paged
        with self.assertRaisesRegex(pls.Fail, "lookup of group .* failed"):
            pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertEqual(self.group_writes(), [])
        self.assertEqual(pls._lookup_all(type("C", (), {"call": lambda s, p, b: (200, {"Response": {
            "Data": [{"GroupId": i, "GroupName": "g"} for i in range(200)]}}, "")})(), "/api/groups/get",
            "GroupName", "g", "GroupId"), None)                                # a full page without a count: unknown

    def test_refused_when_the_run_log_cannot_be_written(self):
        (self.r / "ops").mkdir(exist_ok=True)
        (self.r / "ops/log").write_text("not a folder", encoding="utf-8")
        self.assertEqual(pls.main(["principals", "--env", "dev", "--create", "--yes"]), 2)
        self.assertEqual(self.fake.calls, [])

    def test_no_group_is_ever_updated_or_deleted(self):
        pls.main(["principals", "--env", "dev", "--create", "--yes"])
        self.assertFalse([p for p in self.group_writes() if re.search(r"/(update|delete)$", p)])


if __name__ == "__main__":
    unittest.main()
