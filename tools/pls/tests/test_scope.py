"""Components proven to round-trip (ADR-0001, BR3):  python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
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
        bad = {"Columns": [], "PermissionForUpdating": {}, "DashboardParts": [{"Id": 7, "Type": 5, "View": {}}, {"Id": 8, "Type": 0}]}
        self.assertEqual(SC.unverified(bad), [
            "PermissionForUpdating (no round-trip evidence)",
            "DashboardParts[7] type 5 (kanban) (no round-trip evidence)",
            "DashboardParts[8] type 0 (quick access) (no round-trip evidence)"])

    def test_near_completion_days_have_round_trip_evidence(self):
        """KB probe D33 passed on dev 1.5.2.0 (2026-11-12): the site's range days are stored and used."""
        self.assertEqual(SC.unverified({"NearCompletionTimeBeforeDays": 0, "NearCompletionTimeAfterDays": 90,
                                        "Views": [{"Id": 1, "NearCompletionTime": True}]}), [])

    def test_creation_permissions_formulas_and_status_controls_have_evidence(self):
        """KB probes D36, D41, D42 passed on dev 1.5.2.0 (2026-11-14): stored as sent and applied."""
        self.assertEqual(SC.unverified({"PermissionForCreating": {"Group": 15}, "Formulas": [{"Id": 1, "Target": "NumC"}],
                                        "StatusControls": [{"Id": 1, "ReadOnly": True}]}), [])

    def test_scalar_keys_stored_by_probes_d43_to_d47_have_evidence(self):
        """KB probes D43-D47 on dev 1.5.2.0 (2026-11-16): every key they expect stored was read back as sent, except
        DashboardPartsAsynchronousLoading (recorded only when it differs from the server's parameter). The four mail
        address keys round-trip but stay unverified until they are kept out of git (Nam 2026-11-15); six switches that
        turn off guards or carry free HTML stay unverified until classify has a rule for them (TD-63)."""
        probes = Path(__file__).resolve().parents[3] / "skills/pls-kb-pleasanter/references/probes"
        keys = set()
        for f in sorted(probes.glob("D4[3-7]-site-scalars-*.json")):
            keys |= set(json.loads(f.read_text(encoding="utf-8"))["expect_stored"])
        self.assertEqual(len(keys), 86)
        held_back = sorted(["AddressBook", "MailToDefault", "MailCcDefault", "MailBccDefault",       # kept out of git
                            "DashboardPartsAsynchronousLoading",                                       # not stored
                            "ServerScriptsAllDisabled", "ScriptsAllDisabled", "HtmlsAllDisabled",      # guards off,
                            "AllowPhysicalDeleteHistories", "AllowMigrationMode", "ExtendedHeader"])   # no classify rule
        self.assertEqual(sorted(keys - SC.VERIFIED_KEYS), held_back)
        self.assertEqual(SC.unverified({k: "x" for k in held_back}),
                         [f"{k} (no round-trip evidence)" for k in held_back])

    def test_a_status_control_naming_principals_stays_unverified(self):
        """Principal ids differ per environment and pls maps none of them inside status controls."""
        for k in ("Depts", "Groups", "Users"):
            found = SC.unverified({"StatusControls": [{"Id": 2, "ReadOnly": True, k: [379]}]})
            self.assertEqual(len(found), 1, found)
            self.assertIn("StatusControls[2] names principals", found[0])
        self.assertEqual(SC.unverified({"StatusControls": [{"Id": 3, "Groups": [], "ReadOnly": True}]}), [])

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
        self.assertEqual(SC.site_findings({"PermissionForUpdating": {}}, {"PermissionForUpdating": {}, "Exports": []}),
                         ["Exports (no round-trip evidence)", "PermissionForUpdating (no round-trip evidence)"])


class ReleasePlanTest(TP.PlsTest):
    """Reuses the two-site stg fixture of test_pls; only the scope check is exercised here."""

    def plan(self, *extra):
        sa, sb = self._two_sites()
        live = json.loads(sb.read_text(encoding="utf-8"))
        live["Response"]["Data"]["SiteSettings"]["PermissionForUpdating"] = {"Group": 4}   # a component without evidence
        sb.write_text(json.dumps(live), encoding="utf-8")
        git_b = self.r / "config/b/site.json"                                        # git holds it too (as after unpack)
        site = json.loads(git_b.read_text(encoding="utf-8"))
        site["PermissionForUpdating"] = {"Group": 4}
        git_b.write_text(json.dumps(site), encoding="utf-8")
        return pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}", *extra])

    def test_unverified_component_in_live_settings_refuses_the_plan(self):
        self.assertEqual(self.plan(), 1)
        self.assertFalse((self.r / "releases/R1").exists())

    def test_decision_record_accepts_it_and_is_recorded_in_the_plan(self):
        rec = self.r / "scope-decision.md"
        rec.write_text("PermissionForUpdating accepted for this release: verified by hand after apply (Nam, 2026-11-05)", encoding="utf-8")
        self.assertEqual(self.plan("--accept-unverified", str(rec)), 0)
        plan = json.loads((self.r / "releases/R1/plan.json").read_text(encoding="utf-8"))
        scope = plan["per_site"]["b"]["checks"]["scope"]
        self.assertEqual(scope["accepted_by"], str(rec))
        self.assertIn("PermissionForUpdating (no round-trip evidence)", scope["unverified"])
        self.assertEqual(plan["per_site"]["a"]["checks"]["scope"], "verified")
        self.assertEqual(len(scope["record_sha256"]), 64)                                  # tied to the record's content

    def test_unverified_component_only_in_git_refuses_too(self):
        sa, sb = self._two_sites()
        git_a = self.r / "config/a/site.json"
        site = json.loads(git_a.read_text(encoding="utf-8"))
        site["Exports"] = [{"Id": 1}]
        git_a.write_text(json.dumps(site), encoding="utf-8")
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 1)
        self.assertFalse((self.r / "releases/R1").exists())                               # refused: nothing written

    def test_scope_command_lists_from_git_what_release_plan_would_refuse(self):
        self._two_sites()
        git_a = self.r / "config/a/site.json"
        site = json.loads(git_a.read_text(encoding="utf-8"))
        site["Exports"] = [{"Id": 1}]
        site["DashboardParts"] = [{"Id": 8, "Type": 0}]
        git_a.write_text(json.dumps(site), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(["scope"]), 1)
        text = out.getvalue()
        self.assertIn("a: 2 without round-trip evidence", text)
        self.assertIn("SCOPE Exports (no round-trip evidence)", text)
        self.assertIn("SCOPE DashboardParts[8] type 0 (quick access)", text)
        self.assertIn("b: no finding", text)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(["scope", "--site", "b"]), 0)                       # one clean site
        self.assertNotIn("a:", out.getvalue())
        with self.assertRaisesRegex(pls.Fail, "config/zz/site.json not found"):
            pls.main(["scope", "--site", "zz"])
        for bad in ("../a", "a/..", ".."):
            with self.assertRaisesRegex(pls.Fail, "a site name, not a path"):
                pls.main(["scope", "--site", bad])

    def test_missing_decision_record_is_an_error(self):
        with self.assertRaises(pls.Fail):
            self.plan("--accept-unverified", "nope.md")


# keep the inherited tests of PlsTest from running twice (never touch tests defined in ReleasePlanTest itself)
for _name in [n for n in dir(TP.PlsTest) if n.startswith("test_") and n not in ReleasePlanTest.__dict__]:
    setattr(ReleasePlanTest, _name, None)

if __name__ == "__main__":
    unittest.main()
