"""Skill structure (design review I1): every working skill ends its procedure with a checklist, the skills that write
project files list their outputs, and the lifecycle asks for `pls skills check` at the start and a completion report
at the end of every phase and session (I3, I6). The knowledge base is reference material and is exempt."""
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[3] / "skills"
WRITES_PROJECT_FILES = ("pls-p1-requirements-analyst", "pls-p2-solution-designer", "pls-p3-config-builder",
                        "pls-p5-release-manager", "pls-x-spec-recovery")


def headings(name: str) -> list[str]:
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    return re.findall(r"^##\s+(.+?)\s*$", text, re.M)


class SkillStructureTest(unittest.TestCase):
    def test_every_working_skill_has_a_checklist(self):
        names = sorted(p.parent.name for p in SKILLS.glob("pls-*/SKILL.md") if p.parent.name != "pls-kb-pleasanter")
        self.assertGreaterEqual(len(names), 10)
        bad = [n for n in names if not any(h.lower().startswith("checklist") for h in headings(n))]
        self.assertEqual(bad, [], "skills without a '## Checklist …' section")

    def test_skills_that_write_project_files_list_their_outputs(self):
        bad = [n for n in WRITES_PROJECT_FILES if not any(h.lower().startswith("output") for h in headings(n))]
        self.assertEqual(bad, [], "skills without an '## Output(s) …' section")

    def test_lifecycle_checks_skills_first_and_reports_at_the_end(self):
        text = (SKILLS / "pls-x-lifecycle" / "SKILL.md").read_text(encoding="utf-8")
        start = text.index("## 1. Find where the project is")
        self.assertIn("First run `pls skills check`", text[start:text.index("## 2.", start)])
        self.assertIn("completion report", text.lower())
        for part in ("files changed", "with its result", "decisions only the person can make", "EV-07"):
            self.assertIn(part, text)


if __name__ == "__main__":
    unittest.main()
