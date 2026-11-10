"""A damaged project file (plan.json, environments.json, connections.json, the profile) is a refusal that names the
file, before anything is written — never a traceback (fail closed):
python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import pls_http as H  # noqa: E402
import test_http as TH  # noqa: E402

NOT_UTF8 = b'{"env": "dev", "note": "\x93\xfa\x96\x7b"}'          # cp932 bytes
BOM = b"\xef\xbb\xbf"


class MalformedFiles(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def planned(self):
        plan, d = self.plan()
        for site in plan["per_site"]:
            plan["per_site"][site]["payload_file"] = f"payload-{site}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return plan, d / "plan.json"

    def refused(self, *args):
        """The message of the refusal. Any other exception is the traceback this test is about."""
        n = len(self.fake.calls)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                code = pls.main(list(args))
            message = out.getvalue()
            self.assertIn(code, (1, 2), args)
        except (pls.Fail, H.TransportError, GT.GateError) as ex:
            message = str(ex)
        writes = [p for p, _ in self.fake.calls[n:] if p.rsplit("/", 1)[-1] in ("updatesite", "createsite", "create", "update",
                                                                                 "delete", "bulkupsert")]
        self.assertEqual(writes, [], args)
        return message

    def test_damaged_plan_json_refuses_apply_and_mark_applied(self):
        plan, f = self.planned()
        good = f.read_bytes()
        damaged = {"bad JSON": b"{not json", "a list": b"[]", "null": b"null", "not UTF-8": NOT_UTF8}
        for field, value in (("sites", "equipment"), ("per_site", ["equipment"]), ("steps", {"a": 1}), ("rollback", "x"),
                             ("steps", ["equipment"]), ("per_site", {"equipment": 1}), ("env", ["dev"])):
            damaged[f"{field} = {value!r}"] = json.dumps(dict(plan, **{field: value})).encode()
        for name, data in damaged.items():
            f.write_bytes(data)
            for cmd in (["apply", "R-1", "--yes"], ["mark-applied", "R-1", "--export", "equipment=x.json"]):
                with self.subTest(defect=name, cmd=cmd[0]):
                    self.refused(*cmd)
        f.unlink()
        self.assertIn("plan.json", self.refused("apply", "R-1", "--yes"))             # missing
        f.write_bytes(good)

    def test_a_refusal_names_the_file_and_the_field(self):
        plan, f = self.planned()
        f.write_text(json.dumps(dict(plan, steps={"a": 1})), encoding="utf-8")
        message = self.refused("apply", "R-1", "--yes")
        self.assertIn("releases/R-1/plan.json", message.replace("\\", "/"))
        self.assertIn("steps must be a list", message)

    def test_damaged_environments_json_refuses(self):
        self.planned()
        f = self.r / "environments.json"
        ev = json.loads(f.read_text(encoding="utf-8"))
        dev = ev["envs"]["dev"]
        damaged = {"bad JSON": b"{", "a list": b"[]", "not UTF-8": NOT_UTF8,
                   "envs a list": json.dumps(dict(ev, envs=[dev])).encode(),
                   "env a string": json.dumps(dict(ev, envs={"dev": "dev"})).encode(),
                   "sites a list": json.dumps(dict(ev, envs={"dev": dict(dev, sites=["equipment"])})).encode(),
                   "site a number": json.dumps(dict(ev, envs={"dev": dict(dev, sites={"equipment": 1})})).encode(),
                   "role a list": json.dumps(dict(ev, envs={"dev": dict(dev, role=["dev"])})).encode()}
        for name, data in damaged.items():
            f.write_bytes(data)
            for cmd in (["apply", "R-1", "--yes"], ["lint"]):
                with self.subTest(defect=name, cmd=cmd[0]):
                    self.assertIn("environments.json", self.refused(*cmd))

    def test_damaged_connections_json_refuses(self):
        self.planned()
        f = self.r / ".pls/connections.json"
        conns = json.loads(f.read_text(encoding="utf-8"))
        damaged = {"a list": b"[]", "null": b"null", "not UTF-8": NOT_UTF8,
                   "entry a string": json.dumps(dict(conns, dev="http://x")).encode(),
                   "key reference a number": json.dumps(dict(conns, dev=dict(conns["dev"], keys={"admin": 1}))).encode(),
                   "keys a list": json.dumps(dict(conns, dev=dict(conns["dev"], keys=["admin"]))).encode()}
        for name, data in damaged.items():
            f.write_bytes(data)
            with self.subTest(defect=name):
                self.assertIn("connections.json", self.refused("apply", "R-1", "--yes"))

    def test_a_profile_that_is_not_utf8_refuses_a_gate_record(self):
        (self.r / "CLAUDE.md").write_bytes("| Approvers | G4: Nam |\n".encode("utf-8") + b"\x93\xfa\x96\x7b")
        self.assertIn("CLAUDE.md", self.refused("gate", "G4", "--approver", "Nam", "--release", "R-1", "--quote", "ok"))

    def test_a_byte_order_mark_is_accepted(self):
        _, f = self.planned()
        for p in (f, self.r / "environments.json", self.r / ".pls/connections.json"):
            p.write_bytes(BOM + p.read_bytes())
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue([p for p, _ in self.fake.calls if p.endswith("/updatesite")])


if __name__ == "__main__":
    unittest.main()
