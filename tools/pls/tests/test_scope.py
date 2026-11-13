"""Components proven to round-trip (ADR-0001, BR3):  python -m unittest discover -s tools/pls/tests -v"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import pls_scope as SC  # noqa: E402
import test_pls as TP  # noqa: E402


class PureTest(unittest.TestCase):
    def test_known_components_pass_and_unknown_ones_are_listed(self):
        ok = {"Version": 1.017, "Columns": [], "Processes": [], "Htmls": [], "Scripts": [], "Styles": [],
              "DashboardParts": [{"Id": 1, "Type": 3}, {"Id": 2, "Type": 1, "View": {}}, {"Id": 3, "Type": 4, "View": {}}]}
        self.assertEqual(SC.unverified(ok), [])
        bad = {"Columns": [], "StatusControls": [], "DashboardParts": [{"Id": 7, "Type": 5, "View": {}}, {"Id": 8, "Type": 0}]}
        self.assertEqual(SC.unverified(bad), [
            "StatusControls (no round-trip evidence)",
            "DashboardParts[7] type 5 (kanban) (no round-trip evidence)",
            "DashboardParts[8] type 0 (quick access) (no round-trip evidence)"])

    def test_near_completion_days_have_round_trip_evidence(self):
        """KB probe D33 passed on dev 1.5.2.0 (2026-11-12): the site's range days are stored and used."""
        self.assertEqual(SC.unverified({"NearCompletionTimeBeforeDays": 0, "NearCompletionTimeAfterDays": 90,
                                        "Views": [{"Id": 1, "NearCompletionTime": True}]}), [])

    def test_dashboard_part_edge_cases(self):
        parts = [{"Id": 1, "Type": 1}, {"Id": 2}, {"Id": 3, "Type": "3"}, {"Id": 4, "Type": True, "View": {}},
                 {"Id": 5, "Type": 4, "View": {}}]
        found = SC.unverified({"DashboardParts": parts})
        self.assertTrue(any("[1] type 1 has no View" in x for x in found))           # would be HTTP 500 (D30)
        self.assertTrue(any("[2] has no Type" in x for x in found))
        self.assertTrue(any("[3] Type '3' is not an integer" in x for x in found))
        self.assertTrue(any("[4] Type True is not an integer" in x for x in found))
        self.assertFalse(any("[5]" in x for x in found))

    def test_findings_merge_live_and_git(self):
        self.assertEqual(SC.site_findings({"StatusControls": []}, {"StatusControls": [], "Formulas": []}),
                         ["Formulas (no round-trip evidence)", "StatusControls (no round-trip evidence)"])


class ReleasePlanTest(TP.PlsTest):
    """Reuses the two-site stg fixture of test_pls; only the scope check is exercised here."""

    def plan(self, *extra):
        sa, sb = self._two_sites()
        live = json.loads(sb.read_text(encoding="utf-8"))
        live["Response"]["Data"]["SiteSettings"]["StatusControls"] = [{"Id": 1}]      # e.g. a customer's status control
        sb.write_text(json.dumps(live), encoding="utf-8")
        git_b = self.r / "config/b/site.json"                                        # git holds it too (as after unpack)
        site = json.loads(git_b.read_text(encoding="utf-8"))
        site["StatusControls"] = [{"Id": 1}]
        git_b.write_text(json.dumps(site), encoding="utf-8")
        return pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}", *extra])

    def test_unverified_component_in_live_settings_refuses_the_plan(self):
        self.assertEqual(self.plan(), 1)
        self.assertFalse((self.r / "releases/R1").exists())

    def test_decision_record_accepts_it_and_is_recorded_in_the_plan(self):
        rec = self.r / "scope-decision.md"
        rec.write_text("StatusControls accepted for this release: verified by hand after apply (Nam, 2026-11-05)", encoding="utf-8")
        self.assertEqual(self.plan("--accept-unverified", str(rec)), 0)
        plan = json.loads((self.r / "releases/R1/plan.json").read_text(encoding="utf-8"))
        scope = plan["per_site"]["b"]["checks"]["scope"]
        self.assertEqual(scope["accepted_by"], str(rec))
        self.assertIn("StatusControls (no round-trip evidence)", scope["unverified"])
        self.assertEqual(plan["per_site"]["a"]["checks"]["scope"], "verified")
        self.assertEqual(len(scope["record_sha256"]), 64)                                  # tied to the record's content

    def test_unverified_component_only_in_git_refuses_too(self):
        sa, sb = self._two_sites()
        git_a = self.r / "config/a/site.json"
        site = json.loads(git_a.read_text(encoding="utf-8"))
        site["Formulas"] = [{"Id": 1}]
        git_a.write_text(json.dumps(site), encoding="utf-8")
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 1)
        self.assertFalse((self.r / "releases/R1").exists())                               # refused: nothing written

    def test_missing_decision_record_is_an_error(self):
        with self.assertRaises(pls.Fail):
            self.plan("--accept-unverified", "nope.md")


# keep the inherited tests of PlsTest from running twice (never touch tests defined in ReleasePlanTest itself)
for _name in [n for n in dir(TP.PlsTest) if n.startswith("test_") and n not in ReleasePlanTest.__dict__]:
    setattr(ReleasePlanTest, _name, None)

if __name__ == "__main__":
    unittest.main()
