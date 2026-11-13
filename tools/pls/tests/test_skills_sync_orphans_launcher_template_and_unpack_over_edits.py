"""`pls skills check|sync` report skills the framework dropped, folders pls did not install, a stale launcher and
changed template files (sync removes only what pls installed and never copies a template file over the project's);
the launcher explains a missing framework path instead of a traceback; `pls unpack` never replaces a site folder
that holds uncommitted edits."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
from test_scripts import ENVS, export  # noqa: E402


class SkillsSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fw = Path(self.tmp.name) / "fw"
        for name in ("pls-a", "pls-b"):
            (self.fw / "skills" / name).mkdir(parents=True)
            (self.fw / "skills" / name / "SKILL.md").write_text(name, encoding="utf-8")
        (self.fw / "skills/README.md").write_text("| `pls-a` | P1 | 0.1 | x |\n| `pls-b` | P2 | 0.1 | x |\n",
                                                  encoding="utf-8")
        (self.fw / "templates/project").mkdir(parents=True)
        (self.fw / "templates/project/CLAUDE.md").write_text("rules v1\n", encoding="utf-8")
        self.proj = Path(self.tmp.name) / "p"
        (self.proj / ".claude").mkdir(parents=True)
        (self.proj / ".claude/framework.lock").write_text("{}", encoding="utf-8")
        (self.proj / "CLAUDE.md").write_text("rules v1 + this project's profile\n", encoding="utf-8")
        pls.sync_skills(self.proj, self.fw)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self):
        return pls.skills_check(self.proj, self.fw)

    def test_a_synced_project_is_clean_and_has_the_launcher(self):
        self.assertEqual(self.check(), [])
        self.assertEqual((self.proj / "pls.py").read_text(encoding="utf-8"), pls.LAUNCHER)

    def test_a_skill_the_framework_dropped_is_reported_then_removed(self):
        for f in sorted((self.fw / "skills/pls-b").rglob("*"), reverse=True):
            f.unlink()
        (self.fw / "skills/pls-b").rmdir()
        self.assertIn("pls-b: no longer in the framework - `pls skills sync` removes it", self.check())
        lock = pls.sync_skills(self.proj, self.fw)
        self.assertFalse((self.proj / ".claude/skills/pls-b").exists())
        self.assertNotIn("pls-b", lock["skills"])
        self.assertEqual(self.check(), [])

    def test_an_edited_copy_of_a_dropped_skill_is_named_before_the_sync_deletes_it(self):
        (self.proj / ".claude/skills/pls-b/SKILL.md").write_text("local notes", encoding="utf-8")
        for f in sorted((self.fw / "skills/pls-b").rglob("*"), reverse=True):
            f.unlink()
        (self.fw / "skills/pls-b").rmdir()
        self.assertIn("pls-b: no longer in the framework - `pls skills sync` removes it (its project copy was edited",
                      "\n".join(self.check()))

    def test_a_link_inside_the_skills_folder_is_never_followed_by_a_sync(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("not the project's", encoding="utf-8")
        link = self.proj / ".claude/skills/pls-b"
        for f in sorted(link.rglob("*"), reverse=True):
            f.unlink()
        link.rmdir()
        try:
            if sys.platform == "win32":
                import _winapi
                _winapi.CreateJunction(str(outside), str(link))      # no privilege needed, unlike a symlink
            else:
                os.symlink(outside, link, target_is_directory=True)
        except OSError as ex:
            self.skipTest(f"cannot create a link here: {ex}")
        with self.assertRaisesRegex(pls.Fail, "is a link or points outside .claude/skills"):
            pls.sync_skills(self.proj, self.fw)
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "not the project's")
        os.rmdir(link) if sys.platform == "win32" else link.unlink()

    def test_a_folder_pls_did_not_install_is_reported_and_left_alone(self):
        own = self.proj / ".claude/skills/team-notes"
        own.mkdir()
        (own / "SKILL.md").write_text("ours", encoding="utf-8")
        self.assertTrue(any(p.startswith("team-notes: in .claude/skills but not installed by pls") for p in self.check()))
        pls.sync_skills(self.proj, self.fw)
        self.assertEqual((own / "SKILL.md").read_text(encoding="utf-8"), "ours")

    def test_a_changed_or_missing_launcher_is_reported_and_rewritten(self):
        (self.proj / "pls.py").write_text("# old launcher\n", encoding="utf-8")
        self.assertIn("pls.py: the launcher differs", self.check()[0])
        pls.sync_skills(self.proj, self.fw)
        self.assertEqual(self.check(), [])
        (self.proj / "pls.py").unlink()
        self.assertIn("pls.py: the launcher differs from the framework's (or is missing)", self.check()[0])
        (self.proj / "pls.py").write_bytes(pls.LAUNCHER.replace("\n", "\r\n").encode("utf-8"))   # git autocrlf
        self.assertEqual(self.check(), [])

    def test_changed_and_new_template_files_are_reported_and_never_copied(self):
        (self.fw / "templates/project/CLAUDE.md").write_text("rules v2\n", encoding="utf-8")
        (self.fw / "templates/project/new.md").write_text("new\n", encoding="utf-8")
        problems = self.check()
        self.assertIn("templates/project/CLAUDE.md: changed in the framework since the last sync", "\n".join(problems))
        self.assertIn("templates/project/new.md: added in the framework since the last sync", "\n".join(problems))
        (self.proj / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        os.chdir(self.proj)
        out = io.StringIO()
        try:
            with mock_framework(self.fw), contextlib.redirect_stdout(out):
                self.assertEqual(pls.main(["skills", "sync"]), 0)
        finally:
            os.chdir(Path(__file__).resolve().parent)
        self.assertIn("templates/project/CLAUDE.md: changed", out.getvalue())          # the sync says it too
        self.assertEqual((self.proj / "CLAUDE.md").read_text(encoding="utf-8"), "rules v1 + this project's profile\n")
        self.assertFalse((self.proj / "new.md").exists())
        self.assertEqual(self.check(), [])

    def test_a_lock_from_before_template_hashes_reports_no_template_change(self):
        lock = json.loads((self.proj / ".claude/framework.lock").read_text(encoding="utf-8"))
        del lock["template"]
        (self.proj / ".claude/framework.lock").write_text(json.dumps(lock), encoding="utf-8")
        (self.fw / "templates/project/CLAUDE.md").write_text("rules v2\n", encoding="utf-8")
        self.assertEqual(self.check(), [])


def mock_framework(fw):
    from unittest import mock
    return mock.patch.object(pls, "FRAMEWORK", fw)


class Launcher(unittest.TestCase):
    def test_a_missing_lock_without_pls_home_is_a_clear_message(self):
        with tempfile.TemporaryDirectory() as d:
            launcher = Path(d) / "pls.py"
            launcher.write_text(pls.LAUNCHER, encoding="utf-8")
            env = {k: v for k, v in os.environ.items() if k != "PLS_HOME"}
            for lock in (None, "{}", "not json", '{"path": null}'):
                if lock is not None:
                    (Path(d) / ".claude").mkdir(exist_ok=True)
                    (Path(d) / ".claude/framework.lock").write_text(lock, encoding="utf-8")
                res = subprocess.run([sys.executable, str(launcher), "lint"], cwd=d, env=env, capture_output=True,
                                     text=True)
                self.assertNotEqual(res.returncode, 0, lock)
                self.assertIn("framework.lock", res.stderr, lock)
                self.assertIn("PLS_HOME", res.stderr, lock)
                self.assertNotIn("Traceback", res.stderr, lock)


class UnpackOverEdits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        (self.r / "design").mkdir()
        self.exp = self.r / "dev.json"
        self.exp.write_text(json.dumps(export([{"Id": 1, "Title": "lib", "All": True, "Body": "var a = 1;\n"}])),
                            encoding="utf-8")
        self.cwd = os.getcwd()
        os.chdir(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.r, check=True, capture_output=True)

    def unpack(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = pls.main(["unpack", str(self.exp), "--env", "dev", "--site", "anken"])
        return rc, out.getvalue()

    def commit_all(self):
        self.git("init", "-q")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "base")

    def test_uncommitted_edits_or_new_files_in_the_site_folder_are_never_replaced(self):
        self.assertEqual(self.unpack()[0], 0)
        self.commit_all()
        self.assertEqual(self.unpack()[0], 0)                                   # clean tree: unpack again
        site = self.r / "config/anken/site.json"
        site.write_text(site.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "config/anken has uncommitted changes"):
            self.unpack()
        self.assertTrue(site.read_text(encoding="utf-8").endswith(" "))
        self.git("checkout", "--", "config/anken")
        extra = self.r / "config/anken/scripts/new-script.js"
        extra.write_text("var b = 2;\n", encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "uncommitted changes"):
            self.unpack()
        self.assertTrue(extra.exists())

    def test_outside_a_git_repository_unpack_says_so_and_goes_on(self):
        rc, out = self.unpack()
        self.assertEqual(rc, 0)
        self.assertIn("not a git repository", out)
        self.assertTrue((self.r / "config/anken/site.json").exists())


if __name__ == "__main__":
    unittest.main()
