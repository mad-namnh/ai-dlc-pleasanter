"""`pls status` reads the project's records and names the open items and the next command, without writing anything
(lifecycle section 1, team rollout phase 7). One project is walked from a new app to a released change."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import pls_status as ST  # noqa: E402
from test_phase_checks_and_gate_coupling import DES, INDEX, REQ  # noqa: E402


def files(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()
            and "ops/log" not in p.relative_to(root).as_posix()}


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        pls.init_project(Path(self.t.name) / "p", "project", "stg", "Nam", origin="new")
        self.r = Path(self.t.name) / "p"
        (self.r / "requirements/sources").mkdir(parents=True, exist_ok=True)
        (self.r / "requirements/sources/2026-11-16-mail.md").write_text("mail\n", encoding="utf-8")
        (self.r / "requirements/index.md").write_text(INDEX, encoding="utf-8")
        (self.r / "design/decisions").mkdir(parents=True, exist_ok=True)
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.t.cleanup()

    def status(self):
        before = files(self.r)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(pls.main(["status"]), 0)
        self.assertEqual(files(self.r), before, "status wrote a file")
        return out.getvalue()

    def gate(self, g, items=(), releases=(), decision="approved"):
        GT.record(self.r, g, decision, "Nam", "ok", list(items), list(releases), "2026-11-18",
                  {"env": "stg"} if g == "G3" else None)

    def release(self, rel, env, role, status, applied_at=None):
        d = self.r / "releases" / rel
        d.mkdir(parents=True, exist_ok=True)
        plan = {"release": rel, "env": env, "env_role": role, "status": status, "sites": ["inquiries"],
                "per_site": {}, "steps": [], "rollback": [], "applied_at": applied_at}
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def next_line(self, text):
        return [x for x in text.splitlines() if x.startswith("Next:")][0]

    def test_a_change_is_walked_from_requirement_to_release(self):
        self.assertIn("Nothing open", self.status())
        (self.r / "requirements/REQ-001-escalate.md").write_text(REQ, encoding="utf-8")
        text = self.status()
        self.assertIn("P1         REQ-001", text)
        self.assertIn("pls gate G1 --approver <name> --item REQ-001", self.next_line(text))
        self.gate("G1", ["REQ-001"])
        self.assertIn("skill pls-p2-solution-designer", self.next_line(self.status()))
        (self.r / "design/decisions/DES-001-escalate.md").write_text(DES, encoding="utf-8")
        self.assertIn("pls gate G2 --approver <name> --item DES-001", self.next_line(self.status()))
        self.gate("G2", ["DES-001"])
        text = self.status()
        self.assertIn("nothing applied on dev since", text)
        self.assertIn("pls release-plan --env dev", self.next_line(text))
        self.release("R-20261118-01-dev", "dev", "dev", "planned")
        self.assertIn("python pls.py apply R-20261118-01-dev", self.next_line(self.status()))
        self.release("R-20261118-01-dev", "dev", "dev", "applied", "2999-01-01T00:00:00+00:00")
        text = self.status()
        self.assertIn("built on dev after G2", text)
        self.assertIn("pls check p3 --env stg --des DES-001", self.next_line(text))
        self.gate("G3", ["DES-001"], ["R-20261118-01-stg"])
        self.assertIn("pls release-plan --env stg --release R-20261118-01-stg", self.next_line(self.status()))
        self.release("R-20261118-01-stg", "stg", "stg", "planned")
        self.assertIn("pls gate G4 --approver <name> --release R-20261118-01-stg", self.next_line(self.status()))
        self.gate("G4", releases=["R-20261118-01-stg"])
        self.assertIn("python pls.py apply R-20261118-01-stg", self.next_line(self.status()))
        self.release("R-20261118-01-stg", "stg", "stg", "applied", "2999-01-02T00:00:00+00:00")
        self.assertIn("Nothing open", self.status())

    def test_a_design_edited_after_g2_and_a_rejection_are_named(self):
        (self.r / "requirements/REQ-001-escalate.md").write_text(REQ, encoding="utf-8")
        self.gate("G1", ["REQ-001"], decision="changes-requested")
        text = self.status()
        self.assertIn("G1: changes-requested by Nam", text)
        self.assertIn("rework REQ-001", self.next_line(text))
        self.gate("G1", ["REQ-001"])
        (self.r / "design/decisions/DES-001-escalate.md").write_text(DES, encoding="utf-8")
        self.gate("G2", ["DES-001"])
        (self.r / "design/decisions/DES-001-escalate.md").write_text(DES + "\nedited\n", encoding="utf-8")
        self.assertIn("ask G2 again", self.next_line(self.status()))

    def test_the_recovery_states_are_the_ones_pls_writes(self):
        self.assertEqual(set(ST.RECOVERY), set(pls.OPEN_STATES))

    def test_an_unfinished_apply_comes_before_every_other_item(self):
        (self.r / "requirements/REQ-001-escalate.md").write_text(REQ, encoding="utf-8")
        for status, words in (("applying", "pls mark-applied R-20261118-02-dev"),
                              ("uncertain", "pls mark-applied R-20261118-02-dev"),
                              ("applied-unverified", "pls mark-applied R-20261118-02-dev"),
                              ("recovery-required", "releases/R-20261118-02-dev/rollback-<site>.json"),
                              ("rolled-back", "make a new release plan with a new id"),
                              ("something-new", "read releases/R-20261118-02-dev/plan.json")):
            with self.subTest(status=status):
                self.release("R-20261118-02-dev", "dev", "dev", status)
                text = self.status()
                self.assertIn("release    R-20261118-02-dev", text)
                self.assertIn(words, self.next_line(text))
                self.assertNotIn("Nothing open", text)

    def test_a_rolled_back_release_replaced_by_a_newer_one_is_not_open(self):
        self.release("R-20261118-02-dev", "dev", "dev", "rolled-back")
        self.release("R-20261118-03-dev", "dev", "dev", "applied", "2999-01-01T00:00:00+00:00")
        self.assertIn("Nothing open", self.status())

    def test_a_live_difference_and_a_migrated_release_name_their_step(self):
        self.release("R-20261118-04-dev", "dev", "dev", "applied-differs", "2999-01-01T00:00:00+00:00")
        self.assertIn("fold the live values into config/", self.next_line(self.status()))
        self.release("R-20261118-05-dev", "dev", "dev", "migrated")
        self.assertIn("migrated on dev", self.status())
        nxt = {x["item"]: x["next"] for x in ST.collect(self.r)["items"]}
        self.assertIn("python pls.py apply R-20261118-05-dev", nxt["R-20261118-05-dev"])

    def test_a_stg_release_after_g4_that_did_not_end_applied_is_open(self):
        (self.r / "requirements/REQ-001-escalate.md").write_text(REQ, encoding="utf-8")
        (self.r / "design/decisions/DES-001-escalate.md").write_text(DES, encoding="utf-8")
        self.gate("G1", ["REQ-001"])
        self.gate("G2", ["DES-001"])
        self.gate("G3", ["DES-001"], ["R-20261118-01-stg"])
        self.release("R-20261118-01-stg", "stg", "stg", "planned")
        self.gate("G4", releases=["R-20261118-01-stg"])
        for status, words in (("recovery-required", "rollback-<site>.json"), ("uncertain", "pls mark-applied"),
                              ("rolled-back", "new release plan")):
            with self.subTest(status=status):
                self.release("R-20261118-01-stg", "stg", "stg", status)
                text = self.status()
                self.assertNotIn("Nothing open", text)
                self.assertIn(words, self.next_line(text))

    def test_a_taken_over_app_starts_with_onboarding_and_keeps_its_pending_request(self):
        os.chdir(self.cwd)
        pls.init_project(Path(self.t.name) / "q", "project", "stg", "Nam", origin="existing")
        self.r = Path(self.t.name) / "q"
        os.chdir(self.r)
        (self.r / "requirements/sources").mkdir(parents=True, exist_ok=True)
        (self.r / "requirements/sources/2026-11-18-pending-export.md").write_text("x\n", encoding="utf-8")
        text = self.status()
        self.assertIn("skill pls-x-onboarding", self.next_line(text))
        self.assertNotIn("pending-export", text)                      # not before the onboarding
        (self.r / "ops/onboarding").mkdir(parents=True)
        (self.r / "ops/onboarding/2026-11-18-summary.md").write_text("done\n", encoding="utf-8")
        self.assertIn("skill pls-p1-requirements-analyst", self.next_line(self.status()))

    def test_a_broken_gate_record_is_the_only_item(self):
        (self.r / "requirements/REQ-001-escalate.md").write_text(REQ, encoding="utf-8")
        (self.r / "gates").mkdir(exist_ok=True)
        (self.r / "gates/2026-11-18-G1-bad.json").write_text("{", encoding="utf-8")
        state = ST.collect(self.r)
        self.assertEqual([x["item"] for x in state["items"]], ["gates/"])
        self.assertIn("repairs or removes", self.next_line(self.status()))

    def test_traceability_links_count_as_design_and_equal_states_share_a_line(self):
        for n in (1, 2, 3):
            (self.r / f"requirements/REQ-00{n}-x.md").write_text(REQ.replace("REQ-001", f"REQ-00{n}"), encoding="utf-8")
        self.gate("G1", ["REQ-001", "REQ-002", "REQ-003"])
        text = self.status()
        self.assertIn("REQ-001 … REQ-003 (3)", text)
        self.assertIn("G1 approved, no DES names it", text)
        (self.r / "traceability.json").write_text(json.dumps({f"REQ-00{n}": {"design": ["DES-001"]} for n in (1, 2, 3)}),
                                                  encoding="utf-8")
        self.assertNotIn("no DES names it", self.status())

    def test_a_sandbox_gets_its_harvest_and_sync_line(self):
        env = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        env["envs"]["dev-taro"] = {"role": "dev", "sandbox_of": "dev", "sites": {}}
        (self.r / "environments.json").write_text(json.dumps(env), encoding="utf-8")
        text = self.status()
        self.assertIn("pls harvest --env dev-taro --site <site>", text)
        self.assertIn("pls sandbox sync --name taro", text)


if __name__ == "__main__":
    unittest.main()
