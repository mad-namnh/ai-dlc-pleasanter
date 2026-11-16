"""No eval dataset, rubric or expected output lives inside `skills/` (ADR-0030, Decision part 6).

Skill folders are installed into project repositories (ADR-0022) and are read by the eval runner under test. A rubric
or an expected output there would show the runner how it is graded, and a case's answer inside a skill makes the eval
measure recall instead of the skill (`skills/README.md`, "Changing a skill"). Cases and rubrics belong under
`evals/<skill>/`. Repository files are only read.
"""
import re
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

EVAL_FOLDER_NAMES = {"eval", "evals"}
EVAL_FILE_NAMES = {"expected.md", "evals.json", "eval.md", "interviewee.md"}
RUBRIC_TITLE = re.compile(r"^#\s+Rubric\b", re.M | re.I)
MUST_HEADING = re.compile(r"^##\s+Must\s*$", re.M)
MUST_NOT_HEADING = re.compile(r"^##\s+Must not\s*$", re.M)


def eval_data_in(skills: Path) -> list[str]:
    """Every folder or file under `skills` that looks like eval data, with the reason, relative to `skills`."""
    found = []
    for path in sorted(skills.rglob("*")):
        where = path.relative_to(skills).as_posix()
        name = path.name.lower()
        if path.is_dir():
            if name in EVAL_FOLDER_NAMES:
                found.append(f"{where}/: an eval folder")
            continue
        if name in EVAL_FILE_NAMES:
            found.append(f"{where}: an eval file name")
        elif path.suffix.lower() == ".md":
            text = path.read_text(encoding="utf-8", errors="replace")
            if RUBRIC_TITLE.search(text) or (MUST_HEADING.search(text) and MUST_NOT_HEADING.search(text)):
                found.append(f"{where}: rubric headings (# Rubric, or ## Must with ## Must not)")
    return found


class SkillsHoldNoEvalDataTest(unittest.TestCase):
    def test_skills_folder_holds_no_eval_data(self):
        skills = ROOT / "skills"
        self.assertTrue((skills / "pls-x-lifecycle" / "SKILL.md").is_file(), "skills/ not found")
        self.assertEqual(eval_data_in(skills), [], "eval data inside skills/ — move it under evals/<skill>/")

    def test_the_check_catches_each_shape(self):
        planted = {
            "pls-x-a/evals/case.md": "evals/: an eval folder",
            "pls-x-a/references/expected.md": "expected.md: an eval file name",
            "pls-x-a/EVAL.md": "EVAL.md: an eval file name",
            "pls-x-a/evals.json": "evals.json: an eval file name",
            "pls-x-a/references/interviewee.md": "interviewee.md: an eval file name",
            "pls-x-a/references/notes.md": "notes.md: rubric headings",
            "pls-x-a/references/score.md": "score.md: rubric headings",
        }
        contents = {
            "pls-x-a/references/notes.md": "# Rubric — case 001\n",
            "pls-x-a/references/score.md": "# Score\n\n## Must\n- a\n\n## Must not\n- b\n",
        }
        root = Path(tempfile.mkdtemp())
        try:
            for rel in planted:
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(contents.get(rel, "x\n"), encoding="utf-8")
            (root / "pls-x-a" / "SKILL.md").write_text("# Skill\n\n## Must read first\n- the KB\n", encoding="utf-8")
            found = eval_data_in(root)
            for rel, expected in planted.items():
                with self.subTest(path=rel):
                    self.assertTrue(any(expected in p for p in found), found)
            self.assertFalse(any(p.startswith("pls-x-a/SKILL.md") for p in found), found)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
