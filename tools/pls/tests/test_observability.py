"""Run log and token usage (ADR-0013):  python -m unittest discover -s tools/pls/tests -v"""
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

KEYS = {"v", "ts", "kind", "run_id", "actor", "branch", "head", "cmd", "args", "env", "site", "release", "result",
        "exit_code", "duration_ms", "writes", "metrics", "message", "phase", "title"}


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

    def test_log_failure_never_breaks_a_command(self):
        (self.r / "ops").mkdir()
        (self.r / "ops/log").write_text("a file where the folder should be", encoding="utf-8")
        self.assertEqual(pls.main(["lint"]), 0)


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

    def test_transcript_folder_name(self):
        self.assertEqual(US.transcripts_dir(Path("C:/Workspace/MADLAB/01. Project/demo")).name,
                         US.re.sub(r"[^A-Za-z0-9]", "-", str(Path("C:/Workspace/MADLAB/01. Project/demo").resolve())))


if __name__ == "__main__":
    unittest.main()
