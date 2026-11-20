"""`pls drift-watch` (team rollout A1, N19, N20, N25): a UI edit on a project site is reported to the task owner
without them asking — read only, results kept on the machine, never while the folder lacks a shared release."""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_drift_watch as DW  # noqa: E402
import pls_drift_watch_schedule as DS  # noqa: E402
from test_http import EQ, FOLDER, LO, Fake, serve  # noqa: E402

NS = {"t": DS.TASK_NS}
WRITES = ("/updatesite", "/createsite", "/deletesite", "/bulkupsert", "/create", "/update", "/delete")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=str(cwd),
                          check=True, capture_output=True, text=True).stdout


def watch(action="run", env=None, quiet=False, shared=None):
    return Namespace(action=action, env=env or [], quiet=quiet, shared_branch=shared)


class DriftWatchTest(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.srv = serve(self.fake)
        url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name) / "p"
        self.r.mkdir()
        envs = {"managed_sites": ["equipment", "loans"], "envs": {
            "dev": {"role": "dev", "parent_id": FOLDER, "sites": {"equipment": {"id": EQ, "title": "dev_E"},
                                                                   "loans": {"id": LO, "title": "dev_L"}}},
            "dev-an": {"role": "dev", "connection": "dev", "sandbox_of": "dev", "parent_id": FOLDER,
                       "sites": {"equipment": {"id": EQ, "title": "an_E", "sandbox": True},
                                 "loans": {"id": LO, "title": "dev_L", "shared_from": "dev"}}},
            "stg": {"role": "stg", "sites": {"equipment": {"id": EQ}}},
            "prod": {"role": "prod", "sites": {"equipment": {"id": EQ}}}}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (self.r / ".pls").mkdir()
        self.conns = {"dev": {"url": url, "keys": {"admin": "env:T_ADMIN"}, "allow_write": False},
                      "prod": {"url": url, "keys": {"admin": "env:T_ADMIN"}}}
        (self.r / ".pls/connections.json").write_text(json.dumps(self.conns), encoding="utf-8")
        (self.r / "pls.py").write_text(pls.LAUNCHER, encoding="utf-8")
        os.environ["T_ADMIN"] = "K-ADMIN"
        self.cwd = os.getcwd()
        os.chdir(self.r)
        for site in ("equipment", "loans"):                  # git holds what dev has now: the baseline
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pls.main(["export", "--env", "dev", "--site", site]), 0)
            exp = sorted((self.r / ".pls/exports").glob(f"dev-{site}-*.json"))[-1]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", site]), 0)
        self.told = []

    def tearDown(self):
        os.chdir(self.cwd)
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()
        os.environ.pop("T_ADMIN", None)

    def run_watch(self, *args, **kw):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = pls.drift_watch(self.r, watch(*args, **kw), notify=self.told.append)
        return code, out.getvalue()

    def envs(self):
        return pls.envs(self.r)["envs"]

    # ---------------------------------------------------------------- scope (N20)

    def test_a_machine_checks_its_own_dev_and_stg_connections_never_prod_or_another_sandbox(self):
        self.assertEqual(DW.scope(self.r, self.envs()), {"dev": ["equipment", "loans"]})
        self.conns["stg"] = {"url": "http://x", "keys": {}}                   # Nam's machine: the stg key is there
        (self.r / ".pls/connections.json").write_text(json.dumps(self.conns), encoding="utf-8")
        self.assertEqual(DW.scope(self.r, self.envs()), {"dev": ["equipment", "loans"], "stg": ["equipment"]})

    def test_a_named_sandbox_checks_only_its_own_copies(self):
        self.assertEqual(DW.scope(self.r, self.envs(), ["dev", "dev-an"]), {"dev": ["equipment", "loans"],
                                                                             "dev-an": ["equipment"]})

    def test_prod_and_unknown_environments_are_refused(self):
        with self.assertRaisesRegex(DW.WatchError, "dev and stg environments only"):
            DW.scope(self.r, self.envs(), ["prod"])
        with self.assertRaisesRegex(DW.WatchError, "unknown environment 'nope'"):
            DW.scope(self.r, self.envs(), ["nope"])
        code, out = self.run_watch(env=["prod"])
        self.assertEqual(code, 2)
        self.assertIn("dev and stg environments only", out)

    def test_nothing_in_scope_is_refused(self):
        (self.r / ".pls/connections.json").write_text(json.dumps({"prod": self.conns["prod"]}), encoding="utf-8")
        code, out = self.run_watch()
        self.assertEqual(code, 2)
        self.assertIn("nothing to check on this machine", out)

    def test_a_run_that_stops_early_is_shown_and_not_restarted_at_every_session(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["values"] = {"x": [1]}                            # a value guards refuse by name
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaises(pls.Fail):
            self.run_watch(quiet=True)
        self.assertIn("the check stopped: environments.json envs.dev.values", DW.problems(DW.load(self.r))[0])
        started = []
        notes = DS.session_notes(self.r, {"dev": ["equipment"]}, start=started.append)
        self.assertEqual(started, [])                                         # recorded just now: not restarted
        self.assertIn("the check stopped", notes[1])

    # ---------------------------------------------------------------- one run

    def test_a_ui_edit_is_reported_with_its_classification_and_the_two_ways_on_without_any_write(self):
        before = {p: p.read_bytes() for p in self.r.rglob("*") if p.is_file() and ".pls" not in p.parts}
        code, out = self.run_watch()
        self.assertEqual(code, 0, out)
        self.assertIn("Every site checked matches its last release.", out)
        self.assertEqual(self.told, [])
        self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"] = True      # someone edits on the screen
        n = len(self.fake.calls)
        code, out = self.run_watch()
        self.assertEqual(code, 1, out)
        self.assertIn("dev/equipment: 1 difference(s) from the last release — reverting would be config-only", out)
        self.assertIn("pls harvest --env dev --site equipment", out)
        self.assertIn("--accept-drift ops/drift/", out)
        self.assertNotIn("dev/loans", out.split("## ")[0])
        self.assertTrue(all(p.endswith("/getsite") for p, _ in self.fake.calls[n:]), self.fake.calls[n:])
        self.assertFalse(any(p.endswith(WRITES) for p, _ in self.fake.calls))
        last = json.loads((self.r / ".pls/drift-watch/last.json").read_text(encoding="utf-8"))
        self.assertEqual(last["envs"]["dev"]["sites"]["equipment"]["state"], "drift")
        self.assertEqual(last["envs"]["dev"]["sites"]["loans"]["state"], "clean")
        self.assertTrue((self.r / ".pls/drift-watch/exports/dev-equipment.json").exists())
        self.assertEqual(len(self.told), 1)
        self.assertIn("dev/equipment", self.told[0])
        after = {p: p.read_bytes() for p in self.r.rglob("*") if p.is_file() and ".pls" not in p.parts}
        self.assertEqual(after, before)                                       # nothing outside .pls/, no run log
        code, shown = self.run_watch("show")
        self.assertEqual((code, shown), (1, DW.report(last)))

    def test_the_person_is_told_once_per_new_finding(self):
        self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"] = True
        self.run_watch(quiet=True)
        self.run_watch(quiet=True)
        self.assertEqual(len(self.told), 1)                                   # same drift: not again
        self.fake.sites[LO]["SiteSettings"]["NoDisplayIfReadOnly"] = True
        self.run_watch(quiet=True)
        self.assertEqual(len(self.told), 2)                                   # a new one: told
        del self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"]
        del self.fake.sites[LO]["SiteSettings"]["NoDisplayIfReadOnly"]
        self.assertEqual(self.run_watch(quiet=True), (0, ""))
        self.assertEqual(len(self.told), 2)                                   # clean again: no alert

    def test_a_site_that_cannot_be_read_is_reported_and_the_others_are_checked(self):
        del self.fake.sites[LO]
        code, out = self.run_watch()
        self.assertEqual(code, 1)
        self.assertIn("dev/loans: not read — TransportError: getsite 902: HTTP 404", out)
        last = DW.load(self.r)
        self.assertEqual(last["envs"]["dev"]["sites"]["equipment"]["state"], "clean")

    def test_a_second_run_while_one_is_going_reads_nothing(self):
        self.assertTrue(DW.take_lock(self.r))
        n = len(self.fake.calls)
        code, out = self.run_watch()
        self.assertEqual(code, 0)
        self.assertIn("another drift check is running", out)
        self.assertEqual(len(self.fake.calls), n)
        old = (datetime.now().astimezone() - timedelta(hours=1)).isoformat(timespec="seconds")
        (self.r / ".pls/drift-watch/running.json").write_text(json.dumps({"pid": 1, "started": old}), encoding="utf-8")
        self.assertEqual(self.run_watch(quiet=True)[0], 0)                    # an abandoned lock is taken over
        self.assertGreater(len(self.fake.calls), n)
        self.assertFalse((self.r / ".pls/drift-watch/running.json").exists())

    def test_the_job_leaves_no_run_log(self):
        def log():
            return {p: p.read_bytes() for p in (self.r / "ops/log").rglob("*") if p.is_file()}
        before = log()                                       # setUp's export / unpack are logged
        self.assertTrue(before)
        self.assertEqual(pls.main(["drift-watch", "run", "--quiet"]), 0)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.main(["drift-watch", "show"]), 0)
        self.assertEqual(log(), before)

    # ---------------------------------------------------------------- baseline current (D3)

    def test_an_environment_is_not_reported_while_the_folder_lacks_a_shared_release(self):
        origin = Path(self.tmp.name) / "origin.git"
        git(Path(self.tmp.name), "init", "--bare", "-b", "main", str(origin))
        git(self.r, "init", "-b", "main")
        git(self.r, "add", "environments.json", "config", "pls.py")
        git(self.r, "commit", "-m", "start")
        git(self.r, "remote", "add", "origin", str(origin))
        git(self.r, "push", "-u", "origin", "main")
        git(self.r, "remote", "set-head", "origin", "main")
        code, out = self.run_watch()
        self.assertEqual(code, 0, out)
        self.assertIn("baseline compared with origin/main", out)
        other = Path(self.tmp.name) / "other"                                 # a teammate releases to dev
        git(Path(self.tmp.name), "clone", str(origin), str(other))
        (other / "releases/R-9").mkdir(parents=True)
        (other / "releases/R-9/plan.json").write_text(json.dumps(
            {"release": "R-9", "env": "dev", "site": "equipment", "status": "applied", "applied_at": "2026-11-19T10:00:00"}),
            encoding="utf-8")
        git(other, "add", "releases")
        git(other, "commit", "-m", "release")
        git(other, "push")
        self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"] = True      # what R-9 wrote, not a UI edit
        n = len(self.fake.calls)
        code, out = self.run_watch()
        self.assertEqual(code, 1, out)
        self.assertIn("dev: not checked — this folder lacks the applied release(s) R-9 of the shared branch", out)
        self.assertEqual(len(self.fake.calls), n)                             # not even read
        self.assertNotIn("dev/equipment", out)

    def test_a_failed_fetch_reports_no_shared_environment(self):
        git(self.r, "init", "-b", "main")
        git(self.r, "remote", "add", "origin", str(Path(self.tmp.name) / "missing.git"))
        code, out = self.run_watch()
        self.assertEqual(code, 1)
        self.assertIn("dev: not checked — git fetch failed", out)

    def test_an_unknown_or_wrong_shared_branch_reports_no_shared_environment(self):
        def fake_git(answers):
            def g(args):
                return answers.get(args[0], (0, ""))
            return g
        no_head = fake_git({"remote": (0, "origin\n"), "rev-parse": (128, "")})
        with self.assertRaisesRegex(DW.WatchError, "origin/HEAD is not set"):
            DW.behind(self.r, no_head, None)
        wrong = fake_git({"remote": (0, "origin\n"), "diff": (128, "")})
        with self.assertRaisesRegex(DW.WatchError, "git diff against origin/nope failed"):
            DW.behind(self.r, wrong, "origin/nope")

    def test_without_a_remote_the_report_says_what_the_baseline_is(self):
        code, out = self.run_watch()
        self.assertIn("no git remote: the baseline is this folder's releases/", out)

    # ---------------------------------------------------------------- session start (N25)

    def test_the_session_start_shows_the_last_result_and_refreshes_a_stale_one(self):
        started = []
        targets = DW.scope(self.r, self.envs())
        self.assertEqual(DS.session_notes(self.r, {}, start=started.append), [])          # nothing in scope: silent
        notes = DS.session_notes(self.r, targets, start=started.append)
        self.assertEqual(started, [self.r])                                                 # never ran: started
        self.assertIn("started in the background", notes[-1])
        self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"] = True
        self.run_watch(quiet=True)
        now = datetime.now().astimezone()
        notes = DS.session_notes(self.r, targets, start=started.append, now=now)
        self.assertEqual(len(started), 1)                                                   # fresh: not again
        self.assertIn("1 item(s) — `python pls.py drift-watch show`", notes[0])
        self.assertIn("dev/equipment: 1 difference(s)", notes[1])
        DS.session_notes(self.r, targets, start=started.append, now=now + timedelta(hours=3))
        self.assertEqual(len(started), 2)                                                   # stale: refreshed
        DW.take_lock(self.r, now + timedelta(hours=3))
        DS.session_notes(self.r, targets, start=started.append, now=now + timedelta(hours=3, minutes=5))
        self.assertEqual(len(started), 2)                                                   # one is running

    def test_the_hook_prints_the_drift_lines(self):
        self.fake.sites[EQ]["SiteSettings"]["NoDisplayIfReadOnly"] = True
        self.run_watch(quiet=True)
        out = io.BytesIO()
        with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.r)}), \
                mock.patch.object(DS, "start_background", side_effect=AssertionError("fresh result: no start")):
            self.assertEqual(pls.hook("start", stdin=io.BytesIO(b"{}"), stdout=out), 0)
        self.assertIn("pls drift check (", out.getvalue().decode("utf-8"))
        self.assertIn("dev/equipment: 1 difference(s)", out.getvalue().decode("utf-8"))

    # ---------------------------------------------------------------- the job (D6)

    def test_the_task_runs_the_project_launcher_mon_to_fri_every_two_hours_while_logged_on(self):
        x = ET.fromstring(DS.task_xml(self.r, r"C:\py\pythonw.exe", self.r / "pls.py", "2026-11-19")
                          .replace('encoding="UTF-16"', ""))
        trig = x.find("t:Triggers/t:CalendarTrigger", NS)
        self.assertEqual(trig.find("t:StartBoundary", NS).text, "2026-11-19T09:00:00")
        self.assertEqual(trig.find("t:Repetition/t:Interval", NS).text, "PT2H")
        self.assertEqual(trig.find("t:Repetition/t:Duration", NS).text, "PT10H")
        days = [d.tag.split("}")[1] for d in trig.find("t:ScheduleByWeek/t:DaysOfWeek", NS)]
        self.assertEqual(days, ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        self.assertEqual(x.find("t:Principals/t:Principal/t:LogonType", NS).text, "InteractiveToken")
        self.assertEqual(x.find("t:Settings/t:MultipleInstancesPolicy", NS).text, "IgnoreNew")
        self.assertEqual(x.find("t:Settings/t:ExecutionTimeLimit", NS).text, "PT30M")
        ex = x.find("t:Actions/t:Exec", NS)
        self.assertEqual(ex.find("t:Command", NS).text, r"C:\py\pythonw.exe")
        self.assertEqual(ex.find("t:Arguments", NS).text, f'"{self.r / "pls.py"}" drift-watch run --quiet')
        self.assertEqual(ex.find("t:WorkingDirectory", NS).text, str(self.r.resolve()))

    def test_install_records_the_scope_and_registers_the_xml_remove_deletes_it(self):
        calls = []
        name = DS.install(self.r, ["dev", "dev-an"], "origin/main", run=lambda a: calls.append(a) or (0, "OK"),
                          python=sys.executable, today="2026-11-19", os_name="nt")
        xml = self.r / ".pls/drift-watch/task.xml"
        self.assertEqual(calls, [["schtasks", "/create", "/tn", name, "/xml", str(xml), "/f"]])
        self.assertTrue(xml.read_bytes().startswith(b"\xff\xfe"))                          # UTF-16 with its BOM
        self.assertEqual(DW.settings(self.r), {"envs": ["dev", "dev-an"], "shared_branch": "origin/main"})
        self.assertEqual(DW.scope(self.r, self.envs()), {"dev": ["equipment", "loans"], "dev-an": ["equipment"]})
        self.assertEqual(DS.remove(self.r, run=lambda a: calls.append(a) or (0, "")), name)
        self.assertEqual(calls[-1], ["schtasks", "/delete", "/tn", name, "/f"])
        self.assertTrue(name.startswith("pls drift-watch p "))
        with self.assertRaisesRegex(DW.WatchError, "could not register"):
            DS.install(self.r, ["dev"], None, run=lambda a: (1, "ERROR: access denied"), os_name="nt")
        with self.assertRaisesRegex(DW.WatchError, "could not delete"):
            DS.remove(self.r, run=lambda a: (1, "ERROR: not found"))

    def test_install_is_refused_off_windows_and_without_the_launcher(self):
        with self.assertRaisesRegex(DW.WatchError, "from cron"):
            DS.install(self.r, ["dev"], None, run=lambda a: (0, ""), os_name="posix")
        (self.r / "pls.py").unlink()
        with self.assertRaisesRegex(DW.WatchError, "pls.py not found"):
            DS.install(self.r, ["dev"], None, run=lambda a: (0, ""), os_name="nt")

    def test_install_through_the_command_names_the_task(self):
        calls = []
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch.object(DS, "OS_NAME", "nt"):
            code = pls.drift_watch(self.r, watch("install"), schtasks=lambda a: calls.append(a) or (0, "OK"))
        self.assertEqual(code, 0)
        self.assertIn("every 2 hours", out.getvalue())
        self.assertEqual(DW.settings(self.r)["envs"], ["dev"])
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pls.drift_watch(self.r, watch("remove"), schtasks=lambda a: (0, "")), 0)

    def test_show_before_any_run_is_refused(self):
        code, out = self.run_watch("show")
        self.assertEqual(code, 2)
        self.assertIn("no drift check has run on this machine yet", out)

    @unittest.skipUnless(os.name == "nt", "the balloon is shown on Windows only")
    def test_the_message_reaches_the_balloon_through_the_environment_not_the_command(self):
        with mock.patch.object(DS.subprocess, "Popen") as popen:
            DS.notify("dev/equipment'; Remove-Item x; '")
        argv, kw = popen.call_args
        self.assertNotIn("Remove-Item", " ".join(argv[0]))
        self.assertEqual(kw["env"]["PLS_DRIFT_MESSAGE"], "dev/equipment'; Remove-Item x; '")


if __name__ == "__main__":
    unittest.main()
