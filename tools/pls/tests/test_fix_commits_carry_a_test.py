"""tools/dev/check_fix_commits.py reports a `fix` commit that changes pls code without changing a pls test.

Each test builds a small git repository in a temporary folder (skipped when git is not installed). The last test
runs the check on this repository's own history after the start commit of the rule.

    python -m unittest discover -s tools/pls/tests -v
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(FRAMEWORK / "tools" / "dev"))
import check_fix_commits as CF  # noqa: E402

WHO = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid", "GIT_COMMITTER_NAME": "t",
       "GIT_COMMITTER_EMAIL": "t@example.invalid", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class FixCommitsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git("init", "-q")
        self.commit("chore: start", {"README.md": "x"})

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        res = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, env={**os.environ, **WHO})
        self.assertEqual(res.returncode, 0, res.stderr)
        return res.stdout.strip()

    def commit(self, subject, files):
        for rel, text in files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text, encoding="utf-8")
            self.git("add", "--", rel)
        self.git("commit", "-q", "-m", subject)
        return self.git("rev-parse", "--short", "HEAD")

    def test_a_fix_of_pls_code_without_a_test_is_reported(self):
        start = self.git("rev-parse", "HEAD")
        self.commit("feat(pls): new command", {"tools/pls/pls.py": "1"})                       # not a fix
        with_test = self.commit("fix(pls): guard", {"tools/pls/pls.py": "2", "tools/pls/tests/test_x.py": "t"})
        bare = self.commit("fix(pls): another guard", {"tools/pls/pls_http.py": "3"})
        self.commit("fix: wording", {"docs/architecture.md": "d"})                             # no pls code
        self.commit("fix(pls): test only", {"tools/pls/tests/test_x.py": "t2"})                # no pls code
        plain = self.commit("fix: also without scope", {"tools/pls/pls.py": "4"})
        found = CF.fix_commits_without_a_test(self.repo, start)
        self.assertEqual(sorted(found), sorted([(bare, "fix(pls): another guard"), (plain, "fix: also without scope")]))
        self.assertNotIn(with_test, [short for short, _ in found])

    def test_commits_before_the_start_are_not_checked(self):
        self.commit("fix(pls): old, without a test", {"tools/pls/pls.py": "1"})
        start = self.git("rev-parse", "HEAD")
        self.assertEqual(CF.fix_commits_without_a_test(self.repo, start), [])
        self.commit("fix(pls): with its test", {"tools/pls/pls.py": "2", "tools/pls/tests/test_y.py": "t"})
        self.assertEqual(CF.fix_commits_without_a_test(self.repo, start), [])

    def test_an_unknown_start_is_an_error_not_an_empty_result(self):
        with self.assertRaises(CF.GitError):
            CF.fix_commits_without_a_test(self.repo, "no-such-revision")

    def test_this_repository_has_no_fix_commit_without_a_test_after_the_start_of_the_rule(self):
        if not (FRAMEWORK / ".git").exists():
            self.skipTest("not a git checkout")
        try:
            found = CF.fix_commits_without_a_test(FRAMEWORK, CF.RULE_SINCE)
        except CF.GitError as ex:                                   # a copy or a shallow clone without the start commit
            self.skipTest(f"history not readable from here: {ex}")
        self.assertEqual(found, [], "fix commits that change tools/pls without a test — add the regression test")


if __name__ == "__main__":
    unittest.main()
