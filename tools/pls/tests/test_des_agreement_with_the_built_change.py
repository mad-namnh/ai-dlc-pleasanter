"""After P3 the built change is compared with the DES that ship it: `pls check p3 --env --des`, and G3 refuses an
approval while the comparison reports a finding, unless the approver accepts it with a reason (ADR-0029 B, TD-67)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import pls_phase_check as PC  # noqa: E402
import test_pls as TP  # noqa: E402 — a module, so its test class is not collected twice

PROBE = sorted(PC.kb_probe_ids())[0]          # any entry of the knowledge base's probe index
DES = """---
id: DES-001
status: G2 approved
reqs: [REQ-001]
classification: config-only
elements:
  - id: E1
    site: a
    setting: column ClassA removed
    req: REQ-001
    rung: 1
impact:
  - rule: CL-CHOICES-ADDED
    element: E1
    action: none
---
# DES-001
"""
FIXED = (DES.replace("classification: config-only", "classification: data-impacting")
         .replace("  - rule: CL-CHOICES-ADDED", "  - rule: CL-OTHER\n    element: E1\n    action: none\n"
                                             "  - rule: CL-COLUMN-REMOVED")
         .replace("---\n# DES-001", f"unverified:\n  - key: NotProvenKey\n    probe: {PROBE}\n---\n# DES-001\n\n"
                                    "## Migration\n\nnone\n"))


class DesAgreementTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name)
        (self.r / "environments.json").write_text(json.dumps(TP.ENVS), encoding="utf-8")
        (self.r / "CLAUDE.md").write_text("| Approvers | Nam (all gates) |\n", encoding="utf-8")
        self.cwd = os.getcwd()
        os.environ["PLS_PROFILE_DIR"] = str(self.r / "_profiles")
        os.chdir(self.r)
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(TP.export(101, 102, "http://dev.internal")), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]) == 0
        self.release("R-0-dev", "2026-11-01T10:00:00+09:00")          # what dev holds before the design
        (self.r / "design/decisions").mkdir(parents=True)
        self.des(DES)
        self.g2()
        site = self.r / "config/a/site.json"                           # the build: a column removed, a new key
        s = json.loads(site.read_text(encoding="utf-8"))
        s["Columns"] = [c for c in s["Columns"] if c["ColumnName"] != "ClassA"]
        s["NotProvenKey"] = True
        site.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")

    def tearDown(self):
        os.chdir(self.cwd)
        os.environ.pop("PLS_PROFILE_DIR", None)
        self.t.cleanup()

    def release(self, rel, at):
        d = self.r / "releases" / rel
        d.mkdir(parents=True)
        pl = pls.payload(pls.read_tree(self.r / "config/a"), TP.ENVS["envs"]["dev"], "a")
        (d / "payload-a.json").write_text(json.dumps(pl, ensure_ascii=False), encoding="utf-8")
        (d / "plan.json").write_text(json.dumps({"release": rel, "env": "dev", "sites": ["a"], "status": "applied",
                                                 "applied_at": at, "per_site": {"a": {"payload_file": "payload-a.json"}}}),
                                     encoding="utf-8")

    def des(self, text, did="DES-001"):
        (self.r / f"design/decisions/{did}-x.md").write_text(text.replace("DES-001", did), encoding="utf-8")

    def g2(self, did="DES-001"):
        GT.record(self.r, "G2", "approved", "Nam", "ok", [did], [], "2026-11-02")

    def msgs(self, des=("DES-001",), releases=()):
        return [f"{x['item']}: {x['msg']}" for x in pls.des_agreement(self.r, "dev", list(des), list(releases))]

    def run_pls(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            try:
                return pls.main(list(argv)), out.getvalue()
            except pls.Fail as ex:
                return str(ex), out.getvalue()

    def test_classification_rules_and_scope_keys_are_compared_with_the_des(self):
        m = self.msgs()
        self.assertTrue(any("`classify` gives data-impacting" in x and "at most config-only" in x for x in m), m)
        self.assertTrue(any("rule CL-COLUMN-REMOVED applies" in x for x in m), m)
        self.assertTrue(any("NotProvenKey (no round-trip evidence) — no valid `unverified` entry" in x for x in m), m)
        self.des(FIXED)
        self.g2()
        self.assertEqual(self.msgs(), [])

    def test_an_edited_design_needs_a_new_g2_and_a_new_g2_keeps_the_first_baseline(self):
        p = self.r / "design/decisions/DES-001-x.md"                   # a CRLF checkout is the same design
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        self.assertFalse(any("changed since its G2 approval" in x for x in self.msgs()))
        self.des(FIXED)                                                # edited after G2, not approved again
        self.assertTrue(any(x.startswith("DES-001: DES-001-x.md changed since its G2 approval") for x in self.msgs()))
        later = (datetime.now().astimezone() + timedelta(hours=1)).isoformat(timespec="seconds")
        self.release("R-1-dev", later)                                 # P3 deployed the build to dev
        self.des(DES)
        self.g2()                                                      # approved again (with changes) after that
        m = self.msgs()
        self.assertTrue(any("rule CL-COLUMN-REMOVED applies" in x for x in m), "the baseline stays before the first G2")
        old = GT.latest(self.r, "G2", item="DES-001")
        for p in (self.r / "gates").glob("*.json"):                     # a G2 record written before digests existed
            rec = json.loads(p.read_text(encoding="utf-8"))
            rec.pop("bound_des", None)
            p.write_text(json.dumps(rec), encoding="utf-8")
        self.assertIn(f"DES-001: its G2 approval ({old['at']}) holds no content digest of the DES — approve it again at "
                      "G2, so the build is compared with the design the approver saw", self.msgs())

    def test_the_baseline_is_never_a_release_the_g3_names(self):
        d = self.r / "releases/R-00-dev"                                # an earlier release holding the same state
        d.mkdir()
        (d / "payload-a.json").write_bytes((self.r / "releases/R-0-dev/payload-a.json").read_bytes())
        plan = json.loads((self.r / "releases/R-0-dev/plan.json").read_text(encoding="utf-8"))
        plan.update(release="R-00-dev", applied_at="2026-10-01T10:00:00+09:00")
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.des(DES.replace("site: a", "site: b"))
        self.g2()
        self.assertTrue(any(x.startswith("a: changed since R-0-dev on dev") for x in self.msgs()))
        self.assertTrue(any(x.startswith("a: changed since R-00-dev on dev") for x in self.msgs(releases=["R-0-dev"])))

    def test_first_releases_unnamed_sites_and_unapproved_or_unreadable_designs_are_findings(self):
        self.des(FIXED)
        self.g2()
        for p in (self.r / "releases/R-0-dev").iterdir():
            p.unlink()
        (self.r / "releases/R-0-dev").rmdir()
        m = self.msgs()
        self.assertEqual(len(m), 1, m)
        self.assertIn("cannot be computed offline (first release)", m[0])
        self.des(DES.replace("site: a", "site: b"))
        self.g2()
        m = self.msgs()                                                # never released and no DES names it: not silent
        self.assertTrue(any(x.startswith("a: no release of this site was applied") and "no element of DES-001" in x
                            for x in m), m)
        self.des(DES, did="DES-002")
        self.des("# no front matter\n", did="DES-003")
        self.des("---\nid DES-004\n---\n", did="DES-004")
        m = self.msgs(des=("DES-002", "DES-003", "DES-004", "DES-009"))
        self.assertIn("DES-002: not approved at G2 — a release ships approved designs only", m)
        self.assertIn("DES-003: DES-003-x.md: no front matter — the build cannot be compared with it", m)
        self.assertTrue(any(x.startswith("DES-004: DES-004-x.md: front matter unreadable") for x in m), m)
        self.assertTrue(any(x.startswith("DES-009: no document design/decisions/DES-009") for x in m), m)

    def test_g3_refuses_until_the_build_agrees_or_the_approver_accepts_and_keeps_its_target(self):
        g3 = ["gate", "G3", "--approver", "Nam", "--quote", "ok", "--release", "R-2"]
        for extra in ((), ("--item", "DES-001")):
            with self.subTest(extra=extra):
                code, _ = self.run_pls(*g3, *extra)
                self.assertIn("G3 approval needs --env <target>", code)
        code, out = self.run_pls(*g3, "--env", "dev")
        self.assertIn("G3 REFUSED: the build against its designs (pls check p3 --env --des) gives 1 finding", code)
        self.assertIn("G3 names no --item DES-…", out)
        code, out = self.run_pls(*g3, "--env", "dev", "--item", "DES-001")
        self.assertIn("G3 REFUSED", code)
        self.assertIn("rule CL-COLUMN-REMOVED applies", out)
        self.assertIsNone(GT.latest(self.r, "G3", release="R-2"))
        code, _ = self.run_pls(*g3, "--decision", "rejected")         # a rejection is never refused
        self.assertEqual(code, 0)
        code, _ = self.run_pls(*g3, "--env", "dev", "--item", "DES-001", "--accept-findings", "column unused")
        self.assertEqual(code, 0)
        rec = GT.latest(self.r, "G3", release="R-2")
        self.assertEqual((rec["accept_reason"], rec["env"]), ("column unused", "dev"))
        self.assertTrue(any("CL-COLUMN-REMOVED" in x for x in rec["accepted_findings"]))
        self.des(FIXED)
        self.g2()
        code, _ = self.run_pls(*g3[:-1], "R-3", "--env", "dev", "--item", "DES-001")
        self.assertEqual(code, 0)
        self.assertNotIn("accepted_findings", GT.latest(self.r, "G3", release="R-3"))

    def test_release_plan_refuses_a_g3_that_compared_another_target(self):
        self.run_pls("gate", "G3", "--approver", "Nam", "--quote", "ok", "--release", "R-4", "--env", "dev",
                     "--item", "DES-001", "--accept-findings", "x")
        exp = self.r / "stg.json"
        exp.write_text(json.dumps(TP.export(201, 202, "http://stg.internal")), encoding="utf-8")
        code, out = self.run_pls("release-plan", "--env", "stg", "--release", "R-4", "--export", f"a={exp}")
        self.assertIn("the G3 approval of R-4 compared the build for dev, not stg", out + str(code))

    def test_check_takes_env_and_des_together_and_only_for_p3(self):
        code, out = self.run_pls("check", "p3")
        self.assertIn("note: the build was not compared with its DES", out)
        self.assertNotIn("CL-COLUMN-REMOVED", out)
        for argv in (("--env", "dev"), ("--des", "DES-001")):
            with self.subTest(argv=argv):
                code, _ = self.run_pls("check", "p3", *argv)
                self.assertIn("--env and --des go together", code)
        code, _ = self.run_pls("check", "p2", "--env", "dev", "--des", "DES-001")
        self.assertIn("check p2: --env and --des belong to p3", code)
        code, out = self.run_pls("check", "p3", "--env", "dev", "--des", "DES-001")
        self.assertEqual(code, 1)
        self.assertIn("P3 a: rule CL-COLUMN-REMOVED applies", out)
        (self.r / "gates/broken.json").write_text("{", encoding="utf-8")        # a guard never decides unread
        code, _ = self.run_pls("check", "p3", "--env", "dev", "--des", "DES-001")
        self.assertIn("gates/broken.json is not a readable JSON record", code)

    def test_unverified_entries_name_a_kb_probe_or_a_decision_record_that_names_the_key(self):
        (self.r / "design/decisions/accept-k.md").write_text("We accept K without a probe.\n", encoding="utf-8")
        (self.r / "design/decisions/other.md").write_text("Something else.\n", encoding="utf-8")
        (self.r / "design/decisions/kitchen.md").write_text("Kitchen and KB keys.\n", encoding="utf-8")
        for entry, want in (("  - probe: D1", "needs key"), ("  - just text", "needs key"),
                            (f"  - key: K\n    probe: {PROBE}\n    decision: design/decisions/accept-k.md", "exactly one"),
                            ("  - key: K\n    probe: probe-1", "not an entry of the knowledge base"),
                            ("  - key: K\n    probe: D9999", "not an entry of the knowledge base"),
                            ("  - key: K\n    decision: ../outside.md", "is not a file of this project"),
                            ("  - key: K\n    decision: design/decisions/other.md", "does not name K"),
                            ("  - key: K\n    decision: design/decisions/kitchen.md", "does not name K"),
                            ("  - key: K\n    decision: design/decisions/DES-001-x.md", "not a decision record"),
                            ("  - key: K\n    decision: config/a/site.json", "not a decision record"),
                            ("  - key: K\n    decision: design/decisions/accept-k.md", None),
                            (f"  - key: K\n    probe: {PROBE}", None)):
            with self.subTest(entry=entry):
                self.des(DES.replace("---\n# DES-001", f"unverified:\n{entry}\n---\n# DES-001"))
                got = [x["msg"] for x in PC.p2(self.r) if "unverified" in x["msg"]]
                self.assertEqual(bool(got), want is not None, got)
                if want:
                    self.assertIn(want, got[0])
        self.des(FIXED.replace(f"probe: {PROBE}", "probe: D9999"))      # an invalid entry does not satisfy the scope part
        self.g2()
        self.assertTrue(any("NotProvenKey" in x for x in self.msgs()))


class GateRecordShapeTest(unittest.TestCase):
    def test_a_g2_digest_map_or_a_g3_target_of_the_wrong_shape_is_never_read(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "gates").mkdir()
            base = {"gate": "G2", "decision": "approved", "approver": "Nam", "at": "2026-11-02T10:00:00+09:00",
                    "items": ["DES-1"], "releases": []}
            for extra, want in (({"bound_des": [1]}, "bound_des is not a map"),
                                ({"bound_des": {"DES-1": 5}}, "bound_des is not a map"),
                                ({"env": 3}, "env is not an environment name")):
                with self.subTest(extra=extra):
                    (root / "gates/r.json").write_text(json.dumps(dict(base, **extra)), encoding="utf-8")
                    with self.assertRaisesRegex(GT.GateError, want):
                        GT.load(root)


if __name__ == "__main__":
    unittest.main()
