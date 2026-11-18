"""The framework's CI workflow runs what a commit needs locally (HANDOFF.md "How we work"): the Python suite on the
minimum Python of pls and on a current one, the node runner suite, and the impact-rules freshness check.

Read as text (the suite has no YAML parser), comments dropped and each check scoped to its job: a dropped or
commented-out command, Python version or full-history checkout fails here.

    python -m unittest discover -s tools/pls/tests -v
"""
import re
import unittest
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[3]
WORKFLOW = FRAMEWORK / ".github" / "workflows" / "framework-ci.yml"
PLS = FRAMEWORK / "tools" / "pls" / "pls.py"


class FrameworkCiWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(WORKFLOW.is_file(), f"missing {WORKFLOW.relative_to(FRAMEWORK).as_posix()}")
        # whole-line and trailing comments dropped, so a commented-out command does not count
        lines = [line.split(" #", 1)[0].rstrip() for line in WORKFLOW.read_text(encoding="utf-8").splitlines()]
        self.text = "\n".join(line for line in lines if not line.lstrip().startswith("#"))

    def job(self, name):
        """The text of one job: from `  <name>:` to the next key at the same indent."""
        jobs = self.text.split("\njobs:", 1)[1]
        parts = re.split(r"(?m)^  (?=[\w-]+:\s*$)", jobs)
        found = [p for p in parts if p.startswith(f"{name}:")]
        self.assertEqual(len(found), 1, f"job {name} not found exactly once")
        return found[0]

    def test_runs_both_suites_and_the_freshness_check_each_in_its_job(self):
        for job, command in (
                ("python-suite", "python -m unittest discover -s tools/pls/tests"),
                ("node-suite", "node --test tools/pls/tests/test_runner.mjs"),
                ("impact-rules-fresh", "python tools/pls/pls_impact_rules.py --write"),
                ("impact-rules-fresh",
                 "git diff --exit-code -- skills/pls-p2-solution-designer/references/impact-rules.md")):
            with self.subTest(command=command):
                self.assertIn(command, self.job(job))

    def test_the_python_suite_runs_on_the_minimum_python_of_pls_and_on_3_12(self):
        found = re.search(r"sys\.version_info < \((\d+), (\d+)\)", PLS.read_text(encoding="utf-8"))
        self.assertIsNotNone(found, "pls.py no longer checks a minimum Python at start-up")
        minimum = f"{found.group(1)}.{found.group(2)}"
        versions = set(re.findall(r'python:\s*"(\d+\.\d+)"', self.job("python-suite")))
        self.assertIn(minimum, versions)
        self.assertIn("3.12", versions)

    def test_the_python_suite_runs_on_windows_and_linux(self):
        python_job = self.job("python-suite")
        self.assertIn("os: windows-latest", python_job)
        self.assertIn("os: ubuntu-latest", python_job)

    def test_python_jobs_have_node_and_the_full_history(self):
        python_job = self.job("python-suite")
        self.assertIn("actions/setup-node", python_job, "without node the script syntax tests skip")
        self.assertRegex(python_job, r"fetch-depth:\s*0", "on a shallow clone the fix-commit check skips")

    def test_runs_on_push_pull_request_and_tags_with_read_only_permissions(self):
        self.assertRegex(self.text, r"(?m)^  push:")
        self.assertRegex(self.text, r"(?m)^  pull_request:")
        self.assertRegex(self.text, r'tags:\s*\["v\*"\]')
        self.assertRegex(self.text, r"(?m)^permissions:\s*\n\s+contents:\s*read")


if __name__ == "__main__":
    unittest.main()
