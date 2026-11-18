"""The framework version a project pinned (ADR-0022, team rollout phase 4): writes outside dev run only the pinned,
committed framework; dev writes warn; the session-start hook tells the agent and the person. The framework's git state
is given to the checks (`FP.state` patched), so the tests never depend on this checkout's own state."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_framework_pin as FP  # noqa: E402
import pls_gate as GT  # noqa: E402
import pls_hooks as HK  # noqa: E402
import test_gate as TG  # noqa: E402

PINNED = {"commit": "abc1234", "tag": "v0.3.0", "dirty": False, "latest_tag": "v0.3.0"}


def lock(root: Path, **kw) -> None:
    p = root / ".claude" / "framework.lock"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"framework": "ai-dlc-pleasanter", "commit": "abc1234", "tag": "v0.3.0", "dirty": False, **kw}),
                 encoding="utf-8")


class ProblemTest(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_pinned_committed_checkout_has_no_problem(self):
        lock(self.r)
        self.assertIsNone(FP.problem(self.r, self.r, PINNED))
        self.assertIsNone(FP.problem(self.r, self.r, dict(PINNED, commit="abc1234ff")))   # short hashes of two lengths

    def test_another_commit_uncommitted_changes_or_a_dirty_sync_are_problems(self):
        lock(self.r)
        self.assertIn("project pinned abc1234 (v0.3.0)", FP.problem(self.r, self.r, dict(PINNED, commit="def5678", tag=None)))
        self.assertIn("uncommitted changes", FP.problem(self.r, self.r, dict(PINNED, dirty=True)))
        self.assertIn("cannot be read with git", FP.problem(self.r, self.r, dict(PINNED, commit=None)))
        for dirty in (True, None):                       # had changes, or git could not tell: never taken as clean
            lock(self.r, dirty=dirty)
            self.assertIn("does not record a clean framework", FP.problem(self.r, self.r, PINNED))
        p = self.r / ".claude" / "framework.lock"
        p.write_text(json.dumps({"commit": "abc1234", "tag": "v0.3.0"}), encoding="utf-8")      # an older pls's lock
        self.assertIn("does not record a clean framework", FP.problem(self.r, self.r, PINNED))

    def test_only_a_project_without_a_lock_is_not_checked(self):
        self.assertIsNone(FP.problem(self.r, self.r, dict(PINNED, commit="def5678")))       # no framework.lock at all
        for bad in ("unknown", None, "c"):              # git could not read it, missing, too short to name a commit
            lock(self.r, commit=bad)
            self.assertIn("names no framework commit", FP.problem(self.r, self.r, PINNED), bad)

    def test_a_malformed_lock_is_a_refusal_message_never_a_traceback(self):
        p = self.r / ".claude" / "framework.lock"
        p.parent.mkdir(parents=True, exist_ok=True)
        for doc in ([], {"commit": 1234567, "dirty": False}, {"commit": "abc1234", "tag": 5, "dirty": False}, "text"):
            p.write_text(json.dumps(doc), encoding="utf-8")
            got = FP.problem(self.r, self.r, dict(PINNED, commit="def5678"))
            self.assertIsInstance(got, str, doc)                  # a reason the person can act on, never an exception

    def test_a_tag_of_the_wrong_type_is_never_pinned_even_at_the_pinned_commit(self):
        p = self.r / ".claude" / "framework.lock"
        p.parent.mkdir(parents=True, exist_ok=True)
        for tag in (5, ["x"], {"v": 1}):
            p.write_text(json.dumps({"commit": "abc1234", "tag": tag, "dirty": False}), encoding="utf-8")
            self.assertIn("names no framework commit", FP.problem(self.r, self.r, PINNED), tag)

    def test_a_failed_rev_parse_is_unknown_never_its_output(self):
        for code, out in ((128, "HEAD\n"), (0, "HEAD\n"), (0, "")):
            with mock.patch("subprocess.run", return_value=mock.Mock(returncode=code, stdout=out)):
                self.assertEqual(pls._framework_commit(self.r), "unknown", (code, out))

    def test_the_dirty_check_sees_untracked_files_whatever_the_git_config_says(self):
        calls = []

        def fake_git(fw, *args):
            calls.append(args)
            return ""
        with mock.patch.object(FP, "_git", side_effect=fake_git):
            FP.state(self.r)
        status = [a for a in calls if a[:1] == ("status",)]
        self.assertEqual(len(status), 1)
        self.assertIn("--untracked-files=all", status[0])

    def test_a_lock_that_is_not_an_object_is_rewritten_by_sync_and_reported_by_check(self):
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        p = self.r / ".claude" / "framework.lock"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("[]", encoding="utf-8")
        self.assertIn("not a JSON object", pls.skills_check(self.r, pls.FRAMEWORK)[0])
        with mock.patch.object(FP, "state", return_value=PINNED):
            got = pls.sync_skills(self.r, pls.FRAMEWORK)
        self.assertIsInstance(json.loads(p.read_text(encoding="utf-8")), dict)
        self.assertIn("skills", got)

    def test_skills_sync_warns_for_an_unknown_commit_even_when_the_tree_is_clean(self):
        import os
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        out, old = io.StringIO(), os.getcwd()
        os.chdir(self.r)
        try:
            with mock.patch.object(FP, "state", return_value=PINNED),                     mock.patch.object(pls, "_framework_commit", return_value="unknown"), contextlib.redirect_stdout(out):
                pls.main(["skills", "sync"])
        finally:
            os.chdir(old)
        self.assertIn("WARNING: the framework had uncommitted changes, or git could not read it", out.getvalue())

    def test_skills_sync_warns_when_the_result_cannot_pin(self):
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        import os
        out, old = io.StringIO(), os.getcwd()
        os.chdir(self.r)
        try:
            with mock.patch.object(FP, "state", return_value={"commit": None, "tag": None, "dirty": None, "latest_tag": None}),                     contextlib.redirect_stdout(out):
                pls.main(["skills", "sync"])
        finally:
            os.chdir(old)
        self.assertIn("WARNING: the framework had uncommitted changes, or git could not read it", out.getvalue())

    def test_unreadable_git_is_never_recorded_as_clean(self):
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        with mock.patch.object(FP, "state", return_value={"commit": None, "tag": None, "dirty": None, "latest_tag": None}):
            got = pls.sync_skills(self.r, pls.FRAMEWORK)
        self.assertIsNone(got["dirty"])
        self.assertIsNotNone(FP.problem(self.r, self.r, PINNED))

    def test_skills_sync_records_the_tag_and_whether_the_framework_had_changes(self):
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        with mock.patch.object(FP, "state", return_value=dict(PINNED, dirty=True)):
            got = pls.sync_skills(self.r, pls.FRAMEWORK)
        self.assertEqual((got["tag"], got["dirty"]), ("v0.3.0", True))
        saved = json.loads((self.r / ".claude" / "framework.lock").read_text(encoding="utf-8"))
        self.assertEqual((saved["tag"], saved["dirty"]), ("v0.3.0", True))

    def test_a_newer_release_is_named_only_when_it_comes_after_the_pin(self):
        lock(self.r)
        self.assertIsNone(FP.newer_release(self.r, PINNED, self.r))                     # the pinned tag is the latest
        newer = dict(PINNED, latest_tag="v0.3.1")
        with mock.patch.object(FP, "_git", return_value="fff0000fff0000"),                 mock.patch.object(FP.subprocess, "run", return_value=mock.Mock(returncode=0)):
            self.assertIn("v0.3.1 is available", FP.newer_release(self.r, newer, self.r))  # pin is an ancestor of it
        with mock.patch.object(FP, "_git", return_value="fff0000fff0000"),                 mock.patch.object(FP.subprocess, "run", return_value=mock.Mock(returncode=1)):
            self.assertIsNone(FP.newer_release(self.r, newer, self.r))                   # pin is ahead of the tag
        with mock.patch.object(FP, "_git", return_value="abc1234ffff"):
            self.assertIsNone(FP.newer_release(self.r, newer, self.r))                   # the tag is the pinned commit


class WriteGuardTest(unittest.TestCase):
    """apply outside dev refuses on any pin problem before any write; dev only warns."""
    setUp = TG.StgWriteTest.setUp
    tearDown = TG.StgWriteTest.tearDown
    plan = TG.StgWriteTest.plan
    stg = TG.StgWriteTest.stg
    writes = TG.StgWriteTest.writes

    def test_stg_apply_is_refused_when_the_framework_is_not_the_pinned_version(self):
        self.stg()
        lock(self.r)
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved, apply", [], ["R-20261108-01"], "2026-11-08")
        n = len(self.fake.calls)
        out = io.StringIO()
        with mock.patch.object(FP, "state", return_value=dict(PINNED, dirty=True)), contextlib.redirect_stderr(out),                 contextlib.redirect_stdout(out):
            self.assertNotEqual(pls.main(["apply", "R-20261108-01", "--yes"]), 0)
        self.assertEqual(self.writes(n), [])
        self.assertIn("uncommitted changes", out.getvalue())
        self.assertEqual(json.loads((self.r / "releases/R-20261108-01/plan.json").read_text(encoding="utf-8"))["status"],
                         "planned")                                         # refused before writing: still planned
        with mock.patch.object(FP, "state", return_value=PINNED):         # the pinned version: the release goes on
            pls.main(["apply", "R-20261108-01", "--yes"])
        self.assertTrue(self.writes(n))

    def test_stg_bootstrap_and_record_changing_tests_are_refused_before_the_confirmation(self):
        self.stg()
        lock(self.r)
        b = self.r / "releases/B-20261108-stg"
        b.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["stg"]["sites"]["x1"] = {"title": "stg_X1"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (b / "bootstrap.json").write_text(json.dumps({"release": "B-20261108-stg", "env": "stg", "parent_id": TG.TH.FOLDER,
                                                      "status": "planned", "steps": [{"op": "createsite", "site": "x1",
                                                      "parent_id": TG.TH.FOLDER, "payload": {"Title": "stg_X1",
                                                      "ReferenceType": "Results", "SiteSettings": {}}}]}), encoding="utf-8")
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-20261108-01", "B-20261108-stg"], "2026-11-08")
        spec = self.r / "s.json"
        spec.write_text(json.dumps([{"id": "T", "steps": [{"op": "create", "site": "${site:equipment}", "data": {}}]}]),
                        encoding="utf-8")
        n = len(self.fake.calls)
        with mock.patch.object(FP, "state", return_value=dict(PINNED, commit="def5678")),                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()),                 mock.patch.object(pls, "_confirm", side_effect=AssertionError("asked before the pin check")):
            self.assertNotEqual(pls.main(["bootstrap", "B-20261108-stg"]), 0)
            self.assertNotEqual(pls.main(["apply", "R-20261108-01"]), 0)
            try:
                code = pls.main(["test", str(spec), "--env", "stg", "--site", "equipment", "--release", "R-20261108-01"])
            except pls.Fail:
                code = 2
            self.assertNotEqual(code, 0)
        self.assertEqual([p for p, _ in self.fake.calls[n:] if p.endswith(("/createsite", "/updatesite", "/create"))], [])

    def test_a_migration_write_on_stg_is_refused_by_the_shared_guard(self):
        self.stg()
        lock(self.r)
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-20261108-01"], "2026-11-08")
        import pls_http as H
        with mock.patch.object(FP, "state", return_value=dict(PINNED, dirty=True)):
            with self.assertRaisesRegex(H.TransportError, "REFUSED: the framework has uncommitted changes"):
                pls.write_guard_now(self.r, "stg", "R-20261108-01", "migrating")

    def test_a_dev_apply_writes_and_warns_once(self):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            plan["per_site"][s]["payload_file"] = f"payload-{s}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        lock(self.r)
        pls._PIN_WARNED.clear()
        n, out = len(self.fake.calls), io.StringIO()
        with mock.patch.object(FP, "state", return_value=dict(PINNED, commit="def5678")), contextlib.redirect_stdout(out):
            pls.main(["apply", plan["release"], "--yes"])
        self.assertTrue(self.writes(n))
        self.assertEqual(out.getvalue().count("WARNING: the framework checkout is def5678"), 1)

    def test_http_check_names_the_pin_difference(self):
        lock(self.r)
        out = io.StringIO()
        with mock.patch.object(FP, "state", return_value=dict(PINNED, commit="def5678")), contextlib.redirect_stdout(out):
            pls.main(["http-check", "--env", "dev"])
        self.assertIn("framework: the framework checkout is def5678", out.getvalue())
        self.assertIn("a warning on dev", out.getvalue())

    def test_dev_writes_only_warn(self):
        lock(self.r)
        out = io.StringIO()
        with mock.patch.object(FP, "state", return_value=dict(PINNED, commit="def5678")), contextlib.redirect_stdout(out):
            pls._PIN_WARNED.clear()
            pls.pin_guard(self.r, {"role": "dev"}, "dev")
            pls.pin_guard(self.r, {"role": "dev"}, "dev")
        self.assertEqual(out.getvalue().count("WARNING:"), 1)              # once per run


class SessionStartHookTest(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")
        self.old = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.r)

    def tearDown(self):
        import os
        if self.old is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = self.old
        self.tmp.cleanup()

    def run_hook(self, now) -> str:
        out = io.BytesIO()
        with mock.patch.object(FP, "state", return_value=now):
            self.assertEqual(pls.hook("start", stdin=io.BytesIO(b'{"source": "startup"}'), stdout=out), 0)
        return out.getvalue().decode("utf-8")

    def test_the_hook_tells_the_session_about_the_pin_and_newer_releases(self):
        lock(self.r)
        self.assertEqual(self.run_hook(PINNED), "")
        text = self.run_hook(dict(PINNED, commit="def5678", latest_tag="v0.3.1"))
        self.assertIn("pls framework version:", text)
        self.assertIn("project pinned abc1234", text)

    def test_the_hook_never_fails_the_session(self):
        lock(self.r)
        with mock.patch.object(FP, "state", side_effect=RuntimeError("git broken")):
            self.assertEqual(pls.hook("start", stdin=io.BytesIO(b"{}"), stdout=io.BytesIO()), 0)

    def test_the_hook_is_installed_for_startup_and_resume_and_never_blocks(self):
        start = HK.SETTINGS["SessionStart"][0]
        self.assertEqual(start["matcher"], "startup|resume")
        self.assertTrue(start["hooks"][0]["command"].endswith("hook start || true"))


if __name__ == "__main__":
    unittest.main()
