"""The design rules the P2 designer reads come from one source (ADR-0029 A2): the rules of `pls classify`, the
design conditions of `pls_impact_rules` and the KB's "Do this" text. These tests fail when they drift apart."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_impact_rules as IR  # noqa: E402

# one diff per classify rule: a new classify branch needs a rule in pls_impact_rules and a sample here
SAMPLES = {
    "CL-MULTISELECT-SWITCH": {"path": "settings.Columns[ClassA].MultipleSelections", "kind": "added", "before": None, "after": True},
    "CL-MULTISELECT-EXPLICIT-FALSE": {"path": "settings.Columns[ClassA].MultipleSelections", "kind": "added", "before": None, "after": False},
    "CL-CHOICE-CONTROL": {"path": "settings.Columns[ClassA].ChoicesControlType", "kind": "changed", "before": None, "after": "Radio"},
    "CL-COLUMN-REMOVED": {"path": "settings.Columns[ClassA]", "kind": "removed", "before": {"ColumnName": "ClassA"}, "after": None},
    "CL-LOOKUP-UNCHANGED": {"path": "settings.Columns[ClassA].ChoicesText", "kind": "changed",
                            "before": '[{"SiteId": 1, "Lookups": []}]', "after": '[ {"SiteId": "1", "Lookups": []} ]'},
    "CL-LOOKUP-CHANGED": {"path": "settings.Columns[ClassA].ChoicesText", "kind": "changed",
                          "before": '[{"SiteId": 1}]', "after": '[{"SiteId": 2}]'},
    "CL-CHOICES-REMOVED": {"path": "settings.Columns[ClassA].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a"},
    "CL-CHOICES-ADDED": {"path": "settings.Columns[ClassA].ChoicesText", "kind": "changed", "before": "a", "after": "a\nb"},
    "CL-DEFAULT-INPUT": {"path": "settings.Columns[NumA].DefaultInput", "kind": "changed", "before": "1", "after": "2"},
    "CL-FORMULAS": {"path": "settings.Formulas[1]", "kind": "added", "before": None, "after": {"Id": 1}},
    "CL-SUMMARIES": {"path": "settings.Summaries[1]", "kind": "added", "before": None, "after": {"Type": "Total"}},
    "CL-PERMISSIONS": {"path": "permissions.entries", "kind": "changed", "before": [], "after": ["x"]},
    "CL-PROCESS-ACCESS": {"path": "settings.Processes[send].Groups", "kind": "changed", "before": [], "after": ["${principal:g}"]},
    "CL-STATUS-CONTROL": {"path": "settings.StatusControls[1]", "kind": "added", "before": None, "after": {"Id": 1}},
    "CL-ACCESS-LIST": {"path": "settings.Views[1].Groups", "kind": "changed", "before": [], "after": ["${principal:g}"]},
    "CL-SERVER-SCRIPTS-OFF": {"path": "settings.ServerScriptsAllDisabled", "kind": "added", "before": None, "after": True},
    "CL-MIGRATION-MODE": {"path": "settings.AllowMigrationMode", "kind": "added", "before": None, "after": True},
    "CL-PHYSICAL-DELETE-HISTORIES": {"path": "settings.AllowPhysicalDeleteHistories", "kind": "removed", "before": False, "after": None},
    "CL-CLIENT-CODE-OFF": {"path": "settings.HtmlsAllDisabled", "kind": "added", "before": None, "after": True},
    "CL-EXTENDED-HEADER": {"path": "settings.ExtendedHeader", "kind": "added", "before": None, "after": "<meta name=\"x\">"},
    "CL-OTHER": {"path": "settings.GridPageSize", "kind": "changed", "before": 20, "after": 50},
}


class ImpactRulesTest(unittest.TestCase):
    def test_every_classify_rule_has_a_sample_that_classify_decides_with_the_rule_class(self):
        cl_rules = {r["id"] for r in IR.RULES if r["cls"]}
        self.assertEqual(set(SAMPLES), cl_rules)
        for rid, d in SAMPLES.items():
            with self.subTest(rule=rid):
                c = pls.classify([d])
                self.assertEqual([x["id"] for x in c["rules"]], [rid])
                # every message classify gives has its rule
                self.assertEqual(len(c["rules"]), len(c["data_impacting"] + c["permission_impacting"] + c["config_only"]))
                self.assertEqual(c["classification"], IR.BY_ID[rid]["cls"])
                self.assertEqual(c["rules"][0]["class"], IR.BY_ID[rid]["cls"])

    def test_a_new_sites_first_release_drops_the_data_rules_with_the_data_items(self):
        c = pls.classify([SAMPLES["CL-SUMMARIES"], SAMPLES["CL-STATUS-CONTROL"]])
        pls.first_release_of_new_site(c)
        self.assertEqual(c["classification"], "permission-impacting")
        self.assertEqual([x["id"] for x in c["rules"]], ["CL-STATUS-CONTROL"])
        self.assertEqual(len(c["new_site_notes"]), 1)

    def test_every_rule_id_in_classify_is_a_rule(self):
        src = Path(pls.__file__).read_text(encoding="utf-8")
        body = src[src.index("def classify("):src.index("# ---------------------------------------------------------------- lint")]
        used = set(re.findall(r'hit\("([A-Z-]+)"', body))
        self.assertNotRegex(body, r"\b(data|perm|cfg)\.append\(", "every classify branch goes through hit(), with a rule id")
        self.assertEqual(used, {r["id"] for r in IR.RULES if r["cls"]})

    def test_rule_ids_are_unique_and_kb_ids_exist(self):
        ids = [r["id"] for r in IR.RULES]
        self.assertEqual(len(ids), len(set(ids)))
        advice = IR.kb_advice()
        for r in IR.RULES:
            for k in r["kb"]:
                self.assertIn(k, advice, f"{r['id']} cites {k}, which is not a row of behaviours.md")

    def test_the_generated_reference_is_up_to_date(self):
        self.assertTrue(IR.OUT.exists(), "run: python tools/pls/pls_impact_rules.py --write")
        self.assertEqual(IR.OUT.read_text(encoding="utf-8"), IR.render(),
                         "stale — run: python tools/pls/pls_impact_rules.py --write")

    def test_the_old_summary_advice_is_gone_from_the_generated_reference(self):
        text = IR.render()
        self.assertIn("サマリ", text)
        self.assertNotIn("migration that touches one child per parent", text)


if __name__ == "__main__":
    unittest.main()
