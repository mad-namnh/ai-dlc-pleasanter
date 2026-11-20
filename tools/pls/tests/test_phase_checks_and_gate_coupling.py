"""What a REQ / DES document must contain is decided by `pls check`, and G1 / G2 refuse an approval while it reports a
finding for an approved item, unless the approver accepts it with a reason (ADR-0029 B)."""
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
import pls_front_matter as FM  # noqa: E402
import pls_phase_check as PC  # noqa: E402

REQ = """---
id: REQ-001
status: awaiting G1
type: event-driven
sources: [sources/2026-11-16-mail.md]
acceptance: 2
open_questions: [Q1]
---
# REQ-001 — escalate

## Requirement

When 担当者 escalates an inquiry, the system shall set its status to エスカレーション中.

## Acceptance criteria

1. The status is エスカレーション中 after the escalation.
2. The escalation time is recorded.
"""
INDEX = "# Requirements index\n\n| ID | Title |\n|---|---|\n| REQ-001 | escalate |\n\n| # | Question |\n|---|---|\n| Q1 | 誰が？ |\n"
DES = """---
id: DES-001
status: awaiting G2
reqs: [REQ-001]
classification: config-only
elements:
  - id: E1
    site: inquiries
    setting: status 150
    req: REQ-001
    rung: 1
  - id: E2
    site: inquiries
    setting: process escalate
    req: REQ-001
    rung: 2
impact:
  - rule: ST-STATUS-CHANGE
    element: view 未完了
    action: add 150 to the filter
---
# DES-001
"""


class FrontMatterTest(unittest.TestCase):
    def test_the_subset_is_read_and_anything_else_names_its_line(self):
        fm, body = FM.read(DES)
        self.assertEqual(fm["reqs"], ["REQ-001"])
        self.assertEqual(fm["elements"][1], {"id": "E2", "site": "inquiries", "setting": "process escalate",
                                             "req": "REQ-001", "rung": 2})
        self.assertEqual(fm["impact"][0]["rule"], "ST-STATUS-CHANGE")
        self.assertTrue(body.startswith("# DES-001"))
        self.assertEqual(FM.read("# no front matter\n"), (None, "# no front matter\n"))
        for bad, msg in (("---\nid REQ-1\n---\n", "line 1"), ("---\nid: a\nid: b\n---\n", "appears twice"),
                         ("---\nid: a\n", "never closed"), ("---\nx:\n  y: 1\n---\n", "expected `  - item`"),
                         ("---\n  id: a\n---\n", "indented line"), ("---\ne: [a, [b]]\n---\n", "nested lists"),
                         ("---\nx:\n  - a: 1\n    bad\n---\n", "expected `k: v` inside"),
                         ("---\nx:\n  - a: 1\n    a: 2\n---\n", "a appears twice in an item")):
            with self.subTest(bad=bad), self.assertRaisesRegex(FM.FrontMatterError, msg):
                FM.read(bad)

    def test_scalars(self):
        fm, _ = FM.read('---\na: 3\nb: true\nc: null\nd: "x: y"\ne: [1, "a, b", c]\nf:\n---\n')
        self.assertEqual(fm, {"a": 3, "b": True, "c": None, "d": "x: y", "e": [1, "a, b", "c"], "f": None})


class ProjectTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name)
        pls.init_project(self.r / "p", "project", "stg", "Nam", origin="new")
        self.r = self.r / "p"
        (self.r / "requirements/sources").mkdir(parents=True, exist_ok=True)
        (self.r / "requirements/sources/2026-11-16-mail.md").write_text("mail\n", encoding="utf-8")
        (self.r / "requirements/index.md").write_text(INDEX, encoding="utf-8")
        (self.r / "design/decisions").mkdir(parents=True, exist_ok=True)
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.t.cleanup()

    def req(self, text=REQ, name="REQ-001-escalate.md"):
        (self.r / "requirements" / name).write_text(text, encoding="utf-8")

    def des(self, text=DES):
        (self.r / "design/decisions/DES-001-escalate.md").write_text(text, encoding="utf-8")

    def msgs(self, phase):
        return [f"{x['item']}: {x['msg']}" for x in PC.CHECKS[phase](self.r)]

    def test_a_complete_requirement_and_design_have_no_finding(self):
        self.req()
        self.des()
        self.assertEqual(self.msgs("p1"), [])
        self.assertEqual(self.msgs("p2"), [])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["check", "p1"]), 0)

    def test_interview_answers_after_a_source_are_not_files(self):
        # the template's form `sources/<interview>.md — A3, A7`: the list splits at the comma (TD-75)
        (self.r / "requirements/sources/2026-11-11-interview-x.md").write_text("record\n", encoding="utf-8")
        self.req(REQ.replace("[sources/2026-11-16-mail.md]",
                             "[sources/2026-11-11-interview-x.md — A3, A7, P2 accepted, sources/2026-11-16-mail.md]"))
        self.assertEqual(self.msgs("p1"), [])
        self.req(REQ.replace("[sources/2026-11-16-mail.md]", "[A3, sources/2026-11-16-mail.md]"))
        self.assertEqual(self.msgs("p1"), ["REQ-001: source A3 is not a file under requirements/sources/"])
        self.req(REQ.replace("[sources/2026-11-16-mail.md]", "[sources/2026-11-16-mail.md, A3]"))
        self.assertEqual(self.msgs("p1"), ["REQ-001: source A3 is not a file under requirements/sources/"])
        # a dash that is not followed by answer numbers does not take the next item (review L2)
        self.req(REQ.replace("[sources/2026-11-16-mail.md]", "[sources/2026-11-16-mail.md — client mail, A7]"))
        self.assertEqual(self.msgs("p1"), ["REQ-001: source A7 is not a file under requirements/sources/"])

    def test_p1_findings(self):
        for change, want in (
                (lambda t: t.replace("---\nid: REQ-001", "---\nid: REQ-009"), "is not the file's id"),
                (lambda t: t.replace("type: event-driven", "type: wish"), "not an EARS type"),
                (lambda t: t.replace("[sources/2026-11-16-mail.md]", "[sources/missing.md]"), "not a file under requirements/"),
                (lambda t: t.replace("sources: [sources/2026-11-16-mail.md]\n", ""), "no source"),
                (lambda t: t.replace("エスカレーション中.\n", "エスカレーション中 and shall notify.\n", 1), "2 `shall`"),
                (lambda t: t.replace("acceptance: 2", "acceptance: 3"), "but the section lists 2"),
                (lambda t: t.replace("[Q1]", "[Q7]"), "Q7 is not in requirements/index.md"),
                (lambda t: t.split("---\n", 2)[2], "no front matter")):
            with self.subTest(want=want):
                self.req(change(REQ))
                self.assertTrue(any(want in m for m in self.msgs("p1")), self.msgs("p1"))
        self.req()
        (self.r / "requirements/index.md").write_text("# empty\n", encoding="utf-8")
        self.assertTrue(any("not listed in requirements/index.md" in m for m in self.msgs("p1")))
        self.req(name="REQ-001-other.md")
        self.assertTrue(any("also used by" in m for m in self.msgs("p1")))

    def test_p2_findings(self):
        self.req()
        for change, want in (
                (lambda t: t.replace("rung: 2", "rung: 3"), "rung 3 needs a reason"),
                (lambda t: t.replace("rung: 2", "rung: 7"), "not 1–5"),
                (lambda t: t.replace("rule: ST-STATUS-CHANGE", "rule: STATUS"), "rule must be an id of impact-rules.md"),
                (lambda t: t.replace("classification: config-only", "classification: data-impacting"), "without a `## Migration`"),
                (lambda t: t.replace("reqs: [REQ-001]", "reqs: [REQ-002]"), "has no requirements/REQ-002"),
                (lambda t: t.replace("    action: add 150 to the filter\n", ""), "no action")):
            with self.subTest(want=want):
                self.des(change(DES))
                self.assertTrue(any(want in m for m in self.msgs("p2")), self.msgs("p2"))

    def test_a_g1_approved_requirement_without_a_design_is_a_p2_finding(self):
        self.req()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["gate", "G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "ok"]), 0)
        self.assertIn("REQ-001: approved at G1 but no DES names it in reqs", self.msgs("p2"))

    def test_g1_and_g2_refuse_until_the_findings_are_fixed_or_accepted(self):
        self.req(REQ.replace("acceptance: 2", "acceptance: 5"))
        gate = ["gate", "G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "ok"]
        with contextlib.redirect_stdout(io.StringIO()) as out, self.assertRaisesRegex(pls.Fail, "G1 REFUSED: pls check p1"):
            pls.main(gate)
        self.assertIn("P1 REQ-001: front matter acceptance 5", out.getvalue())
        self.assertFalse((self.r / "gates").exists() and list((self.r / "gates").glob("*-G1-*.json")))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(gate + ["--accept-findings", "count fixed in the next round"]), 0)
        rec = json.loads(next((self.r / "gates").glob("*-G1-*.json")).read_text(encoding="utf-8"))
        self.assertEqual(rec["accept_reason"], "count fixed in the next round")
        self.assertIn("acceptance 5", rec["accepted_findings"][0])
        with contextlib.redirect_stdout(io.StringIO()):                    # a rejection is never blocked
            self.assertEqual(pls.main(["gate", "G1", "--decision", "rejected", "--approver", "Nam", "--item",
                                       "REQ-001", "--quote", "no"]), 0)
        self.des(DES.replace("rung: 2", "rung: 4"))
        g2 = ["gate", "G2", "--approver", "Nam", "--item", "DES-001", "--quote", "ok"]
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(pls.Fail, "G2 REFUSED: pls check p2"):
            pls.main(g2)
        self.des()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(g2), 0)

    def test_findings_of_other_items_do_not_block_an_approval(self):
        self.req()
        self.req(REQ.replace("REQ-001", "REQ-002").replace("type: event-driven", "type: wish"), name="REQ-002-x.md")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["gate", "G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "ok"]), 0)

    def test_p3_reports_lint_scope_and_missing_traceability_paths(self):
        (self.r / "traceability.json").write_text(json.dumps({"REQ-001": {"config": ["config/x/site.json#Columns[ClassA]"]}}),
                                                  encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(["check", "p3"]), 1)
        self.assertIn("P3 REQ-001: traceability config path config/x/site.json#Columns[ClassA] does not exist", out.getvalue())


class ReviewFindingsTest(ProjectTest):
    def gate(self, *argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            try:
                return pls.main(list(argv)), out.getvalue()
            except pls.Fail as ex:
                return str(ex), out.getvalue()

    def test_an_item_without_a_readable_document_is_never_approved_unread(self):
        g1 = ["gate", "G1", "--approver", "Nam", "--quote", "ok"]
        code, out = self.gate(*g1, "--item", "REQ-001")                       # no file at all
        self.assertIn("G1 REFUSED", code)
        self.assertIn("no document requirements/REQ-001-<slug>.md", out)
        self.req(REQ.replace("REQ-001", "REQ-007"), name="REQ-007_escalate.md")  # misnamed: not read
        code, out = self.gate(*g1, "--item", "REQ-007")
        self.assertIn("G1 REFUSED", code)
        self.assertIn("REQ-007_escalate.md: not read", out)
        (self.r / "requirements/REQ-007_escalate.md").unlink()
        self.req()
        code, out = self.gate(*g1, "--item", "REQ-1")                         # an id no document has
        self.assertIn("G1 REFUSED", code)
        (self.r / "design/DES-001-x.md").write_text(DES, encoding="utf-8")   # outside decisions/
        code, out = self.gate("gate", "G2", "--approver", "Nam", "--quote", "ok", "--item", "DES-001")
        self.assertIn("G2 REFUSED", code)
        self.assertIn("design/DES-001-x.md: not read", out)

    def test_every_req_of_a_design_has_an_element_and_g2_blocks_on_an_uncovered_req(self):
        self.req()
        self.req(REQ.replace("REQ-001", "REQ-002"), name="REQ-002-x.md")
        (self.r / "requirements/index.md").write_text(INDEX + "| REQ-002 | x |\n", encoding="utf-8")
        self.des(DES.replace("reqs: [REQ-001]", "reqs: [REQ-001, REQ-002]"))
        self.assertIn("DES-001: REQ-002 is in reqs but no element names it (every in-scope REQ has a design element)",
                      self.msgs("p2"))
        self.des()
        for rid in ("REQ-001", "REQ-002"):
            self.assertEqual(self.gate("gate", "G1", "--approver", "Nam", "--quote", "ok", "--item", rid)[0], 0)
        code, out = self.gate("gate", "G2", "--approver", "Nam", "--quote", "ok", "--item", "DES-001")
        self.assertIn("G2 REFUSED", code)
        self.assertIn("REQ-002: approved at G1 but no DES names it", out)

    def test_sources_ears_words_and_question_ids_are_read_strictly(self):
        for src, ok in (("index.md", False), ("../CLAUDE.md", False), ("REQ-001-escalate.md", False),
                        ("p2 accepted whatever", False), ("derived from REQ-999", False),
                        ("derived from REQ-001", False), ("P2 accepted", True), ("sources/2026-11-16-mail.md — A3", True)):
            with self.subTest(src=src):
                self.req(REQ.replace("[sources/2026-11-16-mail.md]", f'["{src}"]'))
                bad = [m for m in self.msgs("p1") if "source" in m]
                self.assertEqual(not bad, ok, bad)
        self.req(REQ.replace("When 担当者 escalates", "担当者 escalates"))
        self.assertTrue(any("has no `when`" in m for m in self.msgs("p1")))
        self.req(REQ.replace("[Q1]", "[Q10]"))
        (self.r / "requirements/index.md").write_text(INDEX.replace("| Q1 |", "| Q1 |"), encoding="utf-8")
        self.assertTrue(any("Q10 is not in requirements/index.md" in m for m in self.msgs("p1")))
        self.req(REQ.replace("acceptance: 2", "acceptance: true"))
        self.assertTrue(any("front matter acceptance True" in m for m in self.msgs("p1")))

    def test_accept_findings_is_for_g1_to_g3_only_and_a_broken_gate_record_is_a_refusal(self):
        code, _ = self.gate("gate", "G4", "--approver", "Nam", "--quote", "ok", "--release", "R1",
                            "--accept-findings", "x")
        self.assertIn("--accept-findings belongs to G1 / G2 / G3", code)
        code, _ = self.gate("gate", "G4", "--approver", "Nam", "--quote", "ok", "--release", "R1", "--env", "dev")
        self.assertIn("--env belongs to G3", code)
        self.req()
        (self.r / "gates").mkdir(exist_ok=True)
        (self.r / "gates/bad.json").write_text("{", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(pls.Fail):
            pls.main(["check", "p2"])


class RoundTwoTest(ProjectTest):
    def test_as_is_records_are_not_designs_and_notes_are_not_misnamed_documents(self):
        self.req()
        self.des()
        (self.r / "design/decisions/DES-000-as-is-loans.md").write_text("# as-is\n", encoding="utf-8")
        (self.r / "design/design-overview.md").write_text("# notes\n", encoding="utf-8")
        (self.r / "requirements/REQUIREMENTS-notes.md").write_text("# notes\n", encoding="utf-8")
        self.assertEqual(self.msgs("p2"), [])
        self.assertEqual(self.msgs("p1"), [])

    def test_a_g1_approved_req_whose_file_is_gone_still_needs_a_design(self):
        self.req()
        self.req(REQ.replace("REQ-001", "REQ-002"), name="REQ-002-x.md")
        (self.r / "requirements/index.md").write_text(INDEX + "| REQ-002 | x |\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            for rid in ("REQ-001", "REQ-002"):
                pls.main(["gate", "G1", "--approver", "Nam", "--quote", "ok", "--item", rid])
        (self.r / "requirements/REQ-002-x.md").unlink()
        self.des()
        self.assertIn("REQ-002: approved at G1 but no DES names it in reqs", self.msgs("p2"))


if __name__ == "__main__":
    unittest.main()
