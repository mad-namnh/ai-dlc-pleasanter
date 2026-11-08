"""Write-path inventory (I3, ADR-0008): every way `pls` can write to Pleasanter is known and guarded.

Three locks, so a new command or helper cannot write without a guard by accident:
1. every CLI subcommand is classified (writes / reads over HTTP / local only);
2. write endpoints (createsite, updatesite, bulkupsert, create, update, delete) appear only in known functions, and
   the Client write helpers are called only from known functions;
3. every writing command, run against a fake server with allow_write off or on a prod environment, sends no write.
A failure here means: classify the new command / helper and add its guard and a test — never widen the lists blindly.
"""
import ast
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
TOOLS = HERE.parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import test_http as TH  # noqa: E402

WRITES = {"apply", "bootstrap", "test", "kb-verify"}
NETWORK_READS = {"http-check", "export", "version", "adopt", "principals", "backup", "harvest", "sandbox"}
LOCAL = {"unpack", "diff", "drift", "classify", "plan", "slots", "pack", "canon", "release-plan", "bootstrap-plan", "bind",
         "refs", "merge-site", "merge-install", "xref", "env-compare", "mark-applied", "lint", "coverage", "init", "setup",
         "skills", "gate", "step", "usage"}
WRITE_ENDPOINT = re.compile(r"/(updatesite|createsite|bulkupsert|create|update|delete)\b|\{op\}")
ALLOWED_WRITE_SITES = {("pls_http", "Client.apply"), ("pls_http", "Client.create_site"), ("pls_http", "Client.bulk_upsert"),
                       ("pls_http", "run_tests"), ("pls", "http_cmd")}
CLIENT_WRITERS = {"apply": {"apply_release", "rollback"}, "create_site": {"bootstrap"}, "bulk_upsert": set()}
WRITE_RUNNERS = {"apply_release": {"http_cmd"}, "rollback": {"apply_release"}, "bootstrap": {"http_cmd"},
                 "run_tests": {"http_cmd"}}


def subcommands() -> set[str]:
    src = (TOOLS / "pls.py").read_text(encoding="utf-8")
    names = set(re.findall(r'add_parser\("([\w-]+)"', src))
    loop = re.search(r'for c in \(([^)]*)\):\s*\n\s*s = sp\.add_parser\(c\)', src)
    names |= set(re.findall(r'"([\w-]+)"', loop.group(1)))
    return names


def functions(module: Path):
    """(qualified function name, node) for every function, methods as Class.method."""
    tree = ast.parse(module.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            yield node.name, node
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    yield f"{node.name}.{sub.name}", sub


def text_of(node) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "{" + ast.unparse(v.value) + "}" for v in node.values)
    return ""


def modules():
    return [p for p in sorted(TOOLS.glob("*.py"))]


class StaticTest(unittest.TestCase):
    def test_every_subcommand_is_classified(self):
        found = subcommands()
        classified = WRITES | NETWORK_READS | LOCAL
        self.assertEqual(found - classified, set(), "new subcommand: classify it (writes / network reads / local) and guard it")
        self.assertEqual(classified - found, set(), "classified commands that no longer exist")
        self.assertFalse(WRITES & NETWORK_READS or WRITES & LOCAL or NETWORK_READS & LOCAL)

    def test_write_endpoints_only_in_known_functions(self):
        sites = set()
        for m in modules():
            for name, fn in functions(m):
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "call" and node.args:
                        if WRITE_ENDPOINT.search(text_of(node.args[0])):
                            sites.add((m.stem, name))
        self.assertTrue(sites, "the scan found no write endpoint at all — the test is broken")
        self.assertEqual(sites - ALLOWED_WRITE_SITES, set(), "a write endpoint in a new place: route it through a guarded path")

    def test_write_helpers_are_called_only_from_known_functions(self):
        calls: dict[str, set] = {k: set() for k in list(CLIENT_WRITERS) + list(WRITE_RUNNERS)}
        for m in modules():
            for name, fn in functions(m):
                short = name.split(".")[-1]
                for node in ast.walk(fn):
                    if not isinstance(node, ast.Call):
                        continue
                    f = node.func
                    attr = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                    owner = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
                    if attr in CLIENT_WRITERS and owner in ("client", "c", "self"):
                        calls[attr].add(short)
                    if attr in WRITE_RUNNERS and (owner in ("H", "") or m.stem == "pls_http"):
                        calls[attr].add(short)
        for helper, allowed in {**CLIENT_WRITERS, **WRITE_RUNNERS}.items():
            self.assertEqual(calls[helper] - allowed, set(), f"{helper} called from a new place")


class DynamicTest(unittest.TestCase):
    """Each writing command with writes not allowed: no write request reaches the server."""
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def writes(self, n=0):
        return [p for p, _ in self.fake.calls[n:] if re.search(r"/(updatesite|createsite|bulkupsert|create|update|delete)$", p)]

    def deny_writes(self):
        c = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        c["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")

    def test_apply_bootstrap_test_kbverify_send_nothing_without_allow_write(self):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        b = self.r / "releases/B-1"
        b.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"]["x1"] = {"title": "X1"}
        envs["envs"]["dev"]["values"] = {"kb_probe_parent": 950}
        envs["envs"]["dev"]["principals"] = {"admin": "User,7"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (b / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "dev", "parent_id": TH.FOLDER, "status": "planned",
                                                      "steps": [{"op": "createsite", "site": "x1", "parent_id": TH.FOLDER,
                                                                 "payload": {"Title": "X1", "ReferenceType": "Results", "SiteSettings": {}}}]}),
                                          encoding="utf-8")
        (self.r / "s.json").write_text(json.dumps([{"id": "T", "steps": [{"op": "create", "site": "${site:equipment}", "save": "e", "data": {}}]}]),
                                       encoding="utf-8")
        self.fake.sites[950] = {"SiteId": 950, "Title": "probes", "ReferenceType": "Sites", "UpdatedTime": "t0", "SiteSettings": {}}
        self.deny_writes()
        n = len(self.fake.calls)
        for argv in (["apply", "R-1", "--yes"], ["bootstrap", "B-1", "--yes"],
                     ["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "x.json"], ["kb-verify", "--env", "dev", "--yes"]):
            self.assertEqual(pls.main(argv), 2, argv)
        self.assertEqual(self.writes(n), [])

    def test_prod_is_never_written(self):
        plan, d = self.plan()
        plan["env"] = "prod"
        plan["per_site"] = {"equipment": {"site_id": TH.EQ, "side_effects": [], "payload_file": "payload-equipment.json"}}
        plan["sites"] = ["equipment"]
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.writes(n), [])

    def test_network_read_commands_never_write(self):
        n = len(self.fake.calls)
        for argv in (["http-check", "--env", "dev"], ["export", "--env", "dev", "--site", "equipment"]):
            pls.main(argv)
        self.assertEqual(self.writes(n), [])


if __name__ == "__main__":
    unittest.main()
