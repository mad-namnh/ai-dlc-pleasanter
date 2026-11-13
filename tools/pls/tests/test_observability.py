"""Run log and token usage (ADR-0013):  python -m unittest discover -s tools/pls/tests -v"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import pls_log as LG  # noqa: E402
import pls_usage as US  # noqa: E402
import test_http as TH  # noqa: E402

KEYS = {"v", "ts", "kind", "run_id", "actor", "branch", "head", "cmd", "args", "env", "site", "release", "result",
        "exit_code", "duration_ms", "writes", "metrics", "message", "phase", "title", "session"}


def line(rid, ts, out, model="claude-x", inp=10, cr=100, cw=5, typ="assistant"):
    return json.dumps({"type": typ, "requestId": rid, "timestamp": ts, "message": {"model": model, "usage": {
        "input_tokens": inp, "cache_creation_input_tokens": cw, "cache_read_input_tokens": cr, "output_tokens": out},
        "content": [{"type": "text", "text": "SECRET CONVERSATION TEXT"}]}})


class LogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps({"envs": {"dev": {"role": "dev", "sites": {}}}}), encoding="utf-8")
        (self.r / "config").mkdir()
        self.cwd = os.getcwd()
        os.chdir(self.r)
        os.environ["PLS_ACTOR"] = "tester"
        LG._ACTOR.clear()

    def tearDown(self):
        os.chdir(self.cwd)
        os.environ.pop("PLS_ACTOR", None)
        LG._ACTOR.clear()
        self.tmp.cleanup()

    def events(self):
        return LG.read(self.r)

    def test_every_command_and_step_is_one_line_with_the_full_schema(self):
        self.assertEqual(pls.main(["step", "P1", "requirements for the label change"]), 0)
        self.assertEqual(pls.main(["lint", "--summary"]), 0)
        with self.assertRaises(pls.Fail):
            pls.main(["refs", "--site", "nowhere"])
        ev = self.events()
        self.assertEqual([e["kind"] for e in ev], ["step", "command", "command"])
        for e in ev:
            self.assertEqual(set(e), KEYS)
            self.assertEqual((e["v"], e["actor"]), (1, "tester"))
        self.assertEqual((ev[0]["phase"], ev[0]["title"]), ("P1", "requirements for the label change"))
        self.assertEqual((ev[1]["cmd"], ev[1]["result"], ev[1]["metrics"]["issues"]), ("lint", "ok", 0))
        self.assertEqual((ev[2]["cmd"], ev[2]["result"], ev[2]["site"]), ("refs", "error", "nowhere"))
        self.assertTrue(ev[2]["message"])
        self.assertTrue(list((self.r / "ops/log").glob("*-tester.jsonl")))

    def test_every_event_names_the_claude_code_session_that_ran_it(self):
        saved = os.environ.pop("CLAUDE_CODE_SESSION_ID", None)       # the suite itself may run inside Claude Code
        try:
            os.environ["CLAUDE_CODE_SESSION_ID"] = "sess-1"
            pls.main(["step", "P2", "design"])
            pls.main(["lint", "--summary"])
            os.environ.pop("CLAUDE_CODE_SESSION_ID")
            pls.main(["lint", "--summary"])                                         # outside Claude Code
        finally:
            os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
            if saved is not None:
                os.environ["CLAUDE_CODE_SESSION_ID"] = saved
        self.assertEqual([e["session"] for e in self.events()], ["sess-1", "sess-1", None])

    def test_writing_commands_are_marked(self):
        import test_write_guards as WG
        self.assertEqual(LG.WRITING, WG.WRITES)                                     # one list of writing commands

    def test_help_and_usage_errors_are_logged_with_the_shell_exit_code(self):
        with self.assertRaises(SystemExit):
            pls.main(["lint", "--no-such-option"])
        e = self.events()[-1]
        self.assertEqual((e["cmd"], e["result"], e["exit_code"]), ("lint", "error", 2))

    def test_nested_commands_log_only_their_own_metrics(self):
        def inner():
            LG.record_metric(inner=1)
            return 0

        def outer():
            LG.record_metric(outer=1)
            LG.run(lambda: self.r, ["canon", "--site", "x"], inner)
            return 0
        LG.run(lambda: self.r, ["lint"], outer)
        ev = [e for e in self.events() if e["kind"] == "command"]
        self.assertEqual([(e["cmd"], e["metrics"]) for e in ev], [("canon", {"inner": 1}), ("lint", {"outer": 1})])
        self.assertEqual(ev[0]["run_id"], ev[1]["run_id"])

    def test_bad_phase_is_refused(self):
        with self.assertRaises(SystemExit):
            pls.main(["step", "P9", "x"])

    def test_a_reading_command_runs_without_a_log_and_says_so(self):
        (self.r / "ops").mkdir()
        (self.r / "ops/log").write_text("a file where the folder should be", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(pls.main(["lint"]), 0)
        self.assertIn("run log could not be written", err.getvalue())


class WritingCommandsAndTheRunLog(unittest.TestCase):
    """A command that may write to Pleasanter leaves a log line or does not run (ADR-0013)."""
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def planned(self):
        plan, d = self.plan()
        for site in plan["per_site"]:
            plan["per_site"][site]["payload_file"] = f"payload-{site}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def events(self, cmd):
        return [e for e in LG.read(self.r) if e["cmd"] == cmd]

    def test_apply_is_refused_before_anything_is_sent_when_the_log_cannot_be_written(self):
        self.planned()
        (self.r / "ops").mkdir(exist_ok=True)
        (self.r / "ops/log").write_text("a file where the folder should be", encoding="utf-8")
        err = io.StringIO()
        n = len(self.fake.calls)
        with contextlib.redirect_stderr(err):
            self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(self.fake.calls[n:], [])                             # not even a read
        self.assertIn("run log cannot be written", err.getvalue())
        (self.r / "ops/log").unlink()
        pls.main(["apply", "R-1", "--yes"])
        self.assertTrue([p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")])

    def test_the_event_of_an_apply_names_the_environment_the_release_and_the_sites_written(self):
        self.planned()
        pls.main(["apply", "R-1", "--yes"])
        ev = self.events("apply")[-1]
        self.assertEqual((ev["env"], ev["release"], ev["writes"]), ("dev", "R-1", True))
        self.assertEqual(ev["metrics"]["written"], sorted([TH.EQ, TH.LO]))
        self.assertNotIn("_env", ev["metrics"])
        mark = self.events("mark-applied")
        self.assertTrue(mark and all(e["env"] == "dev" for e in mark))


class UsageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name) / "transcripts"
        (self.t / "s1" / "subagents").mkdir(parents=True)
        (self.t / "s1.jsonl").write_text("\n".join([
            line("r1", "2026-11-08T01:00:00Z", 5),
            line("r1", "2026-11-08T01:00:00Z", 50),                       # same response, second line: count once
            line("r2", "2026-11-08T02:30:00Z", 7),
            line("r3", "2026-11-08T02:31:00Z", 0, model="<synthetic>"),   # not a model call
            json.dumps({"type": "user", "message": {"content": "hi"}})]) + "\n", encoding="utf-8")
        (self.t / "s1/subagents/agent-a1.jsonl").write_text(line("q1", "2026-11-08T02:40:00Z", 9) + "\n", encoding="utf-8")
        (self.t / "s1/subagents/agent-a1.meta.json").write_text(json.dumps({"agentType": "general-purpose", "description": "spec"}),
                                                                encoding="utf-8")
        self.p = Path(self.tmp.name) / "proj"
        self.p.mkdir()
        self.steps = [{"kind": "step", "run_id": "A", "phase": "P1", "title": "req", "ts": "2026-11-08T10:00:00.000+09:00"},
                      {"kind": "step", "run_id": "B", "phase": "P3", "title": "build", "ts": "2026-11-08T11:00:00.000+09:00"}]

    def tearDown(self):
        self.tmp.cleanup()

    def test_requests_counted_once_and_attributed_to_the_open_step(self):
        files = US.collect(self.p, self.steps, self.t)
        self.assertEqual([f.name for f in files], ["s1.json"])
        self.assertNotIn("SECRET", files[0].read_text(encoding="utf-8"))           # numbers only
        rows = {(r["step"], r["agent"]): r for r in json.loads(files[0].read_text(encoding="utf-8"))["rows"]}
        self.assertEqual(rows[("A", "main")]["output"], 50)                         # 01:00Z = 10:00+09:00 → step A
        self.assertEqual(rows[("A", "main")]["requests"], 1)
        self.assertEqual(rows[("B", "main")]["output"], 7)                          # 02:30Z = 11:30+09:00 → step B
        self.assertEqual(rows[("B", "general-purpose a1")]["output"], 9)          # type + id, never the description
        self.assertEqual(sum(r["requests"] for r in rows.values()), 3)              # <synthetic> left out
        by_phase = {x["key"]: x for x in US.report(US.load(self.p), "phase")}
        self.assertEqual(by_phase["P3"]["output"], 16)
        self.assertEqual(by_phase["P3"]["total"], 16 + 2 * (10 + 100 + 5))

    def test_a_session_with_work_after_a_g4_is_named(self):
        def row(sid, phase, first):
            return {"session": sid, "phase": phase, "first": first, "requests": 1}
        rows = [row("one", "P3", "2026-11-08T01:00Z"), row("one", "G4", "2026-11-08T02:00Z"),
                row("one", "G1", "2026-11-08T02:10Z"), row("one", "G2", "2026-11-08T02:20Z"),   # gates asked together: fine
                row("two", "P5", "2026-11-08T01:00Z"), row("two", "G4", "2026-11-08T02:00Z"),
                row("two", "P3", "2026-11-08T03:00Z"), row("two", "P3", "2026-11-08T03:10Z"),
                row("two", "P4", "2026-11-08T04:00Z"),
                row("three", "P4", "2026-11-08T00:05Z"), row("three", "G4", "2026-11-08T00:10Z")]  # P4 before the G4
        self.assertEqual(US.sessions_with_several_change_requests(rows), {"two": ["P5", "G4", "P3", "P4"]})
        untimed = [row("four", "G4", "2026-11-08T02:00Z"), {"session": "four", "phase": "P1", "requests": 1}]
        self.assertEqual(US.sessions_with_several_change_requests(untimed), {})          # order unknown: not reported

    def test_usage_report_warns_about_a_session_with_two_change_requests(self):
        import contextlib
        import io as _io
        import os as _os
        (self.p / "environments.json").write_text('{"envs": {}}', encoding="utf-8")
        (self.p / "ops/usage").mkdir(parents=True)
        (self.p / "ops/usage/s9.json").write_text(json.dumps({"v": 1, "session": "s9", "rows": [
            {"phase": "G4", "title": "a", "first": "2026-11-08T01:00Z", "requests": 1},
            {"phase": "P1", "title": "b", "first": "2026-11-08T02:00Z", "requests": 1}]}), encoding="utf-8")
        cwd, err, out = _os.getcwd(), _io.StringIO(), _io.StringIO()
        _os.chdir(self.p)
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                self.assertEqual(pls.main(["usage", "report", "--by", "step"]), 0)
        finally:
            _os.chdir(cwd)
        self.assertIn("WARNING: session s9 did P1 work after a G4 (G4 → P1)", err.getvalue())
        self.assertIn("one Claude Code session per change request", err.getvalue())
        self.assertNotIn("WARNING", out.getvalue())                                   # the table stays clean

    def test_collect_is_idempotent(self):
        US.collect(self.p, self.steps, self.t)
        US.collect(self.p, self.steps, self.t)
        self.assertEqual(sum(r["requests"] for r in US.load(self.p)), 3)

    def test_requests_outside_an_open_step_are_kept_apart(self):
        req = {"model": "m", "agent": "main", "input": 1, "cache_creation": 0, "cache_read": 0, "output": 1}
        rows = US.attribute([dict(req, ts="2026-11-08T00:00:00Z"),            # before the first step
                             dict(req, ts="2026-11-12T00:00:00Z")], self.steps)  # days after the last one
        self.assertEqual([(r["step"], r["title"]) for r in rows], [(None, "(no open step)")])
        self.assertEqual(rows[0]["requests"], 2)

    def test_naive_timestamps_do_not_break_collect(self):
        steps = self.steps + [{"kind": "step", "run_id": "C", "phase": "P4", "title": "t", "ts": "2026-11-08T12:00:00"}]
        self.assertTrue(US.collect(self.p, steps, self.t))

    def test_since_selects_sessions_and_never_drops_earlier_requests(self):
        US.collect(self.p, self.steps, self.t)
        US.collect(self.p, self.steps, self.t, since="2026-11-08T02:00")
        self.assertEqual(sum(r["requests"] for r in US.load(self.p)), 3)
        self.assertEqual(US.collect(self.p, self.steps, self.t, since="2026-11-09"), [])

    def test_only_my_steps_claim_my_tokens(self):
        import os as _os
        root = self.p
        (root / "environments.json").write_text('{"envs": {}}', encoding="utf-8")
        (root / "ops/log").mkdir(parents=True)
        later = {"v": 1, "kind": "step", "run_id": "Z", "actor": "someone-else", "phase": "P6", "title": "theirs",
                 "ts": "2026-11-08T11:20:00.000+09:00"}
        mine = dict(self.steps[1], actor="me", v=1)
        (root / "ops/log/2026-11-08-x.jsonl").write_text(json.dumps(mine) + chr(10) + json.dumps(later) + chr(10),
                                                         encoding="utf-8")
        cwd = _os.getcwd()
        _os.chdir(root)
        _os.environ["PLS_ACTOR"] = "me"
        LG._ACTOR.clear()
        try:
            self.assertEqual(pls.main(["usage", "collect", "--transcripts", str(self.t)]), 0)
        finally:
            _os.chdir(cwd)
            _os.environ.pop("PLS_ACTOR", None)
            LG._ACTOR.clear()
        self.assertNotIn("Z", {r["step"] for r in US.load(root)})

    def test_a_session_started_in_another_folder_counts_only_while_it_worked_on_this_project(self):
        # The session was opened in the framework folder and worked on this project between 10:00 and 10:30 (+09:00):
        # its transcript lies under another project folder; work before the first step and after the last logged
        # command of that session is not this project's.
        base = Path(self.tmp.name) / "claude"
        other = base / "projects" / "C--elsewhere"
        other.mkdir(parents=True)
        (other / "s9.jsonl").write_text("\n".join([
            line("f1", "2026-11-08T00:50:00Z", 100),        # 09:50 — framework work before the first step
            line("p1", "2026-11-08T01:05:00Z", 3),          # 10:05 — inside
            line("p2", "2026-11-08T01:29:00Z", 4),          # 10:29 — inside
            line("f2", "2026-11-08T01:45:00Z", 200)]) + "\n", encoding="utf-8")   # 10:45 — after its last event
        root = self.p
        (root / "environments.json").write_text('{"envs": {}}', encoding="utf-8")
        (root / "ops/log").mkdir(parents=True)
        ev = [{"v": 1, "kind": "step", "run_id": "S", "actor": "me", "phase": "P2", "title": "design",
               "ts": "2026-11-08T10:00:00.000+09:00", "session": "s9"},
              {"v": 1, "kind": "command", "run_id": "L", "actor": "me", "cmd": "lint",
               "ts": "2026-11-08T10:30:00.000+09:00", "session": "s9"}]
        (root / "ops/log/2026-11-08-me.jsonl").write_text("".join(json.dumps(e) + chr(10) for e in ev), encoding="utf-8")
        cwd = os.getcwd()
        os.chdir(root)
        os.environ.update(PLS_ACTOR="me", CLAUDE_CONFIG_DIR=str(base))
        LG._ACTOR.clear()
        try:
            self.assertEqual(pls.main(["usage", "collect"]), 0)         # no transcript folder of its own: still found
        finally:
            os.chdir(cwd)
            for k in ("PLS_ACTOR", "CLAUDE_CONFIG_DIR"):
                os.environ.pop(k, None)
            LG._ACTOR.clear()
        rows = US.load(root)
        self.assertEqual(sorted(r["output"] for r in rows), [7])               # p1 + p2, both in step S
        self.assertEqual({(r["step"], r["session"]) for r in rows}, {("S", "s9")})

    def test_a_session_of_the_project_folder_is_counted_whole_even_when_the_run_log_names_it(self):
        # s1 lies in the project's own transcript folder (and, as a copy, under another folder): it is not windowed,
        # so r1 (10:00, before the session's only step here at 11:00) is still counted.
        base = Path(self.tmp.name) / "claude"
        (base / "projects" / "C--elsewhere").mkdir(parents=True)
        (base / "projects" / "C--elsewhere" / "s1.jsonl").write_text((self.t / "s1.jsonl").read_text(encoding="utf-8"),
                                                                     encoding="utf-8")
        events = [dict(self.steps[1], session="s1")]
        os.environ["CLAUDE_CONFIG_DIR"] = str(base)
        try:
            foreign = US.foreign_sessions(events, self.t)
            US.collect(self.p, self.steps, self.t, None, foreign)
        finally:
            os.environ.pop("CLAUDE_CONFIG_DIR", None)
        self.assertEqual(foreign, {})
        self.assertEqual(sum(r["requests"] for r in US.load(self.p)), 3)

    def test_no_transcripts_anywhere_is_still_a_clear_error(self):
        root = self.p
        (root / "environments.json").write_text('{"envs": {}}', encoding="utf-8")
        cwd = os.getcwd()
        os.chdir(root)
        os.environ["CLAUDE_CONFIG_DIR"] = str(Path(self.tmp.name) / "empty-claude")
        try:
            with self.assertRaises(pls.Fail):
                pls.main(["usage", "collect"])
        finally:
            os.chdir(cwd)
            os.environ.pop("CLAUDE_CONFIG_DIR", None)

    def test_transcript_folder_name(self):
        self.assertEqual(US.transcripts_dir(Path("C:/Workspace/MADLAB/01. Project/demo")).name,
                         US.re.sub(r"[^A-Za-z0-9]", "-", str(Path("C:/Workspace/MADLAB/01. Project/demo").resolve())))


if __name__ == "__main__":
    unittest.main()
