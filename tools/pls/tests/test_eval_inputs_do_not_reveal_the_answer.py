"""An eval case's `input.md` holds only what the runner may read: the request and its premises.

The eval runner gets a copy of `input.md` (`request.md` in its scratch folder). Notes for whoever builds the scratch state — a
reference answer, what an earlier run missed, what the case measures, what the agent must find, another case's input,
a real project repository whose later state holds the answer, the behaviour id under test — would let the runner
pass by recall. They belong in the case's `setup.md`, which the runner never opens (`evals/README.md`; the eval-case brief form).
Repository files are only read.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVALS = ROOT / "evals"

# (pattern, what it reveals) — case-insensitive, matched against the whole input.
REVEALING = [
    (r"evals/|\bresults/|\.\./(?:\.\./)*(?:case-|pls-)", "a path into evals/ (another case, a result or a rubric)"),
    (r"expected\.md|setup\.md|\brubric", "the rubric or the setup notes"),
    (r"reference answer", "a reference answer"),
    (r"\bruns? \d\b|\b(?:first|second|third|earlier|previous|last) runs?\b", "what an earlier run did"),
    (r"must find", "what the agent must find"),
    (r"\b(?:cases?|runs?|evals?)\b[^.\n]{0,40}\bmeasur|\bto measure\b|\bcase tests\b|\btests whether\b|\bgraders?\b",
     "what the case measures"),
    (r"\bEV-\d", "the behaviour id under test"),
    (r"\bcase[ -]\d{3}\b", "the case number (and with it other cases)"),
    (r"\bslice\b", "the slice the case was taken from"),
    (r"contaminat|\bleak", "notes about earlier contaminated runs"),
    (r"git archive|\bcommit `?[0-9a-f]{7}", "how the scratch state is rebuilt from a repository"),
    (r"\bpls-(?:demo|trial|onboard|adopt)-[a-z0-9]|\bdemo-equipment\b", "a real project repository next to the framework"),
]


def case_folders() -> list[Path]:
    return sorted(p for p in EVALS.glob("pls-*/*") if p.is_dir())


def revealing_notes(text: str) -> list[str]:
    return [why for pattern, why in REVEALING if re.search(pattern, text, re.I)]


class EvalInputsTest(unittest.TestCase):
    def test_every_case_folder_has_an_input(self):
        folders = case_folders()
        self.assertGreaterEqual(len(folders), 20, "fewer eval cases than the framework has")
        self.assertEqual([f.relative_to(ROOT).as_posix() for f in folders if not (f / "input.md").is_file()], [])

    def test_no_input_reveals_the_answer(self):
        found = []
        for folder in case_folders():
            text = (folder / "input.md").read_text(encoding="utf-8")
            found += [f"{folder.relative_to(ROOT).as_posix()}/input.md: {why}" for why in revealing_notes(text)]
        self.assertEqual(found, [], "move these notes to the case's setup.md")

    def test_the_patterns_catch_what_they_name(self):
        samples = {
            "Reference answer: the config after the release.": "a reference answer",
            "the release folder, which must be included (run 1 left it out)": "what an earlier run did",
            "as in `evals/pls-p1-requirements-analyst/case-001/input.md`": "a path into evals/",
            "## What the agent must find in config/": "what the agent must find",
            "the case now measures the skill and KB together": "what the case measures",
            "# Input — lifecycle case 004 = EV-01": "the behaviour id under test",
            "The scratch project is `pls-demo-equipment` at the end of G2.": "a real project repository",
            "rebuilt with `git archive 547f549`": "how the scratch state is rebuilt",
            "Scratch project as in `../case-001-new-app-to-g1/input.md`.": "a path into evals/",
            "See `../../pls-p1-requirements-analyst/case-001-escalation/input.md`.": "a path into evals/",
            "Validity note: `results/pls-p2-solution-designer/2026-11-11-v07.md`.": "a path into evals/",
            "the case-004 folder": "the case number",
            "This case tests whether the agent refuses the apply.": "what the case measures",
            "These runs measure the probe rule.": "what the case measures",
            "Earlier evals measured lift.": "what the case measures",
            "Graders check that the agent stops at G1.": "what the case measures",
            "Taken from slice 2.": "the slice",
            "The second run left it out.": "what an earlier run did",
        }
        for text, expected in samples.items():
            with self.subTest(text=text[:40]):
                self.assertTrue(any(expected in why for why in revealing_notes(text)), revealing_notes(text))
        clean = "Prompt: the owner says \"Build the app for this request.\" Today is 2026-11-11. Measurement devices are lent."
        self.assertEqual(revealing_notes(clean), [])


if __name__ == "__main__":
    unittest.main()
