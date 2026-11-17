"""Claude Code hooks of a project repository (ADR-0029 C1): paths only pls writes and the hooks' own settings are
refused to file edits, keys are not read, `pls --yes` asks the person, lint follows a config edit, and the stop hook only
informs; the installed command never exits 2."""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_hooks as HK  # noqa: E402

# the shell Claude Code runs hook commands in: Git Bash on Windows (the bash.exe of System32 is WSL, not it)
_GIT_BASH = Path(r"C:/Program Files/Git/bin/bash.exe")
BASH = str(_GIT_BASH) if _GIT_BASH.exists() else (shutil.which("bash") if os.name != "nt" else None)


class PureTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)

    def tearDown(self):
        self.t.cleanup()

    def ev(self, tool, **inp):
        return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}

    def test_edits_of_paths_only_pls_writes_are_denied(self):
        for rel in ("releases/R1/plan.json", "gates/2026-11-16-G1-x.json", "ops/log/2026-11-16.jsonl", ".pls/connections.json"):
            with self.subTest(rel=rel):
                out = HK.pre(self.root, self.ev("Write", file_path=str(self.root / rel), content="x"))
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertIn("written only by pls", out["hookSpecificOutput"]["permissionDecisionReason"])
        for rel in ("config/a/site.json", "design/decisions/DES-001.md", "ops/onboarding/summary.md", "gatesx/a"):
            with self.subTest(rel=rel):
                self.assertIsNone(HK.pre(self.root, self.ev("Edit", file_path=str(self.root / rel))))
        self.assertIsNone(HK.pre(self.root, self.ev("Write", file_path="/elsewhere/releases/x")))   # outside the project

    def test_pls_with_yes_asks_the_person(self):
        for cmd in ("python pls.py apply --env dev --release R1 --yes", "pls kb-verify --env dev --yes",
                    "cd x && python3 ./pls.py migrate --env dev --yes", "python pls.py apply R1 --ye",
                    "python pls.py apply R1 --y", './pls.py apply R1 "--yes"', "py pls.py apply R1 --yes",
                    "python -u pls.py apply R1 --yes"):
            with self.subTest(cmd=cmd):
                self.assertEqual(HK.pre(self.root, self.ev("Bash", command=cmd))["hookSpecificOutput"]
                                 ["permissionDecision"], "ask")
        for cmd in ("python pls.py apply --env dev --release R1", "git commit -m 'remove --yes from docs'",
                    "grep -- --yes README.md"):
            with self.subTest(cmd=cmd):
                self.assertIsNone(HK.pre(self.root, self.ev("Bash", command=cmd)))

    def test_protected_paths_ignore_case_and_bypassed_permissions_deny_yes(self):
        for rel in (".claude/Settings.Local.json", ".PLS/connections.json", "Gates/x.json", "PLS.py"):
            with self.subTest(rel=rel):
                out = HK.pre(self.root, self.ev("Write", file_path=str(self.root / rel), content="x"))
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        ev = dict(self.ev("Bash", command="python pls.py apply R1 --yes"), permission_mode="bypassPermissions")
        self.assertEqual(HK.pre(self.root, ev)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_keys_are_not_read_and_the_hooks_do_not_edit_themselves(self):
        out = HK.pre(self.root, self.ev("Read", file_path=str(self.root / ".pls/connections.json")))
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(HK.pre(self.root, self.ev("Read", file_path=str(self.root / "gates/x.json"))))
        for rel in (".claude/settings.json", ".claude/settings.local.json", "pls.py"):
            with self.subTest(rel=rel):
                out = HK.pre(self.root, self.ev("Edit", file_path=str(self.root / rel)))
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_lint_issues_of_the_edited_site_go_back_to_the_agent(self):
        ev = {"tool_name": "Edit", "tool_input": {"file_path": str(self.root / "config/loans/site.json")}}
        self.assertEqual(HK.edited_site(self.root, ev), "loans")
        issues = [{"rule": "L-SEC-01", "site": "loans", "msg": "secret-like value"},
                  {"rule": "L-REF-01", "site": "other", "msg": "x"}]
        out = HK.post(issues, "loans")
        self.assertEqual(out["decision"], "block")
        self.assertIn("L-SEC-01  loans", out["reason"])
        self.assertNotIn("other", out["reason"])
        self.assertIsNone(HK.post(issues[1:], "loans"))
        self.assertIsNone(HK.edited_site(self.root, {"tool_input": {"file_path": str(self.root / "README.md")}}))

    def test_the_stop_hook_informs_and_never_keeps_the_agent_going(self):
        found = [{"phase": "p1", "item": "REQ-001", "msg": "x"}, {"phase": "p2", "item": "DES-001", "msg": "y"}]
        out = HK.stop({"stop_hook_active": False}, found)
        self.assertEqual(set(out), {"systemMessage"})
        self.assertIn("p1 1, p2 1", out["systemMessage"])
        self.assertIsNone(HK.stop({"stop_hook_active": True}, found))
        self.assertIsNone(HK.stop({}, []))

    def test_install_reads_a_bom_refuses_wrong_shapes_and_leaves_an_unchanged_file_alone(self):
        f = self.root / ".claude/settings.json"
        f.parent.mkdir()
        f.write_bytes(b"\xef\xbb\xbf" + json.dumps({"permissions": {}}).encode())
        self.assertEqual(HK.install(f), ["PreToolUse", "PostToolUse", "Stop"])
        before = f.read_bytes()
        self.assertEqual(HK.install(f), [])
        self.assertEqual(f.read_bytes(), before)
        for bad in ('{"hooks": []}', '{"hooks": {"Stop": {}}}', "{"):
            with self.subTest(bad=bad):
                f.write_text(bad, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "settings.json"):
                    HK.install(f)

    def test_install_replaces_an_older_pls_hook_entry_and_keeps_other_hooks(self):
        f = self.root / ".claude/settings.json"
        f.parent.mkdir()
        old = {"matcher": "Edit|Write", "hooks": [{"type": "command", "command": 'python "${CLAUDE_PROJECT_DIR}/pls.py" hook pre'}]}
        other = {"matcher": "Bash", "hooks": [{"type": "command", "command": "my-own-check"}]}
        f.write_text(json.dumps({"hooks": {"PreToolUse": [old, other]}}), encoding="utf-8")
        self.assertEqual(HK.install(f), ["PreToolUse", "PostToolUse", "Stop"])
        pre = json.loads(f.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        self.assertIn(other, pre)
        self.assertNotIn(old, pre)
        self.assertIn(HK.SETTINGS["PreToolUse"][0], pre)
        self.assertEqual(HK.install(f), [])
        mixed = {"matcher": "Bash", "hooks": [old["hooks"][0], {"type": "command", "command": "my-second-check"}]}
        f.write_text(json.dumps({"hooks": {"PreToolUse": [mixed]}}), encoding="utf-8")
        self.assertIn("PreToolUse", HK.install(f))
        pre = json.loads(f.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
        self.assertIn({"matcher": "Bash", "hooks": [{"type": "command", "command": "my-second-check"}]}, pre)
        self.assertIn(HK.SETTINGS["PreToolUse"][0], pre)
        self.assertEqual(HK.install(f), [])

    def test_install_adds_the_hooks_once_and_keeps_what_is_there(self):
        f = self.root / ".claude/settings.json"
        f.parent.mkdir()
        f.write_text(json.dumps({"permissions": {"allow": ["Read"]},
                                 "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "x"}]}]}}),
                     encoding="utf-8")
        self.assertEqual(HK.install(f), ["PreToolUse", "PostToolUse", "Stop"])
        self.assertEqual(HK.install(f), [])
        data = json.loads(f.read_text(encoding="utf-8"))
        self.assertEqual(data["permissions"], {"allow": ["Read"]})
        self.assertEqual(len(data["hooks"]["PreToolUse"]), 2)


class ProjectHookTest(unittest.TestCase):
    """The hooks as Claude Code runs them: `pls hook <event>` with the event on stdin, in a project made by pls init."""

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.r = Path(self.t.name) / "p"
        pls.init_project(self.r, "project", "stg", "Nam", origin="new")
        self.cwd = os.getcwd()
        os.chdir(self.r)
        self.addCleanup(os.environ.pop, "CLAUDE_PROJECT_DIR", None)
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.r)

    def tearDown(self):
        os.chdir(self.cwd)
        self.t.cleanup()

    def run_hook(self, event, payload):
        out = io.StringIO()
        self.assertEqual(pls.hook(event, io.StringIO(json.dumps(payload)), out), 0)
        return json.loads(out.getvalue()) if out.getvalue().strip() else None

    def test_init_installs_the_hooks(self):
        data = json.loads((self.r / ".claude/settings.json").read_text(encoding="utf-8"))
        self.assertEqual(set(data["hooks"]), {"PreToolUse", "PostToolUse", "Stop"})
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(["hook", "install"]), 0)
        self.assertIn("hooks already there", out.getvalue())

    def test_pre_denies_a_gate_record_edit_and_allows_a_design_edit(self):
        out = self.run_hook("pre", {"tool_name": "Write", "tool_input": {"file_path": str(self.r / "gates/x.json")}})
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(self.run_hook("pre", {"tool_name": "Write",
                                                "tool_input": {"file_path": str(self.r / "design/x.md")}}))

    def test_post_returns_lint_of_the_edited_site(self):
        (self.r / "config/a").mkdir(parents=True)
        (self.r / "config/a/site.json").write_text(json.dumps({"Notifications": [{"Id": 1, "Type": 3, "Token": "abc"}]}),
                                                   encoding="utf-8")
        (self.r / "config/a/meta.json").write_text(json.dumps({"ReferenceType": "Results"}), encoding="utf-8")
        out = self.run_hook("post", {"tool_name": "Write", "tool_input": {"file_path": str(self.r / "config/a/site.json")}})
        self.assertEqual(out["decision"], "block")
        self.assertIn("L-SEC-01", out["reason"])

    def test_stop_shows_check_findings_and_a_broken_input_stays_silent(self):
        (self.r / "requirements/REQ-001-x.md").write_text("# REQ-001\n", encoding="utf-8")
        out = self.run_hook("stop", {"hook_event_name": "Stop", "stop_hook_active": False})
        self.assertIn("pls check: p1", out["systemMessage"])
        self.assertIsNone(self.run_hook("stop", {"stop_hook_active": True}))
        o = io.StringIO()
        self.assertEqual(pls.hook("pre", io.StringIO("{not json"), o), 0)
        self.assertEqual(o.getvalue(), "")

    def test_a_project_path_with_japanese_characters_is_read_as_utf8(self):
        proj = Path(self.t.name) / "プロジェクト"
        pls.init_project(proj, "project", "stg", "Nam", origin="new")
        os.environ["CLAUDE_PROJECT_DIR"] = str(proj)
        event = {"session_id": "s", "cwd": str(proj), "hook_event_name": "PreToolUse", "tool_name": "Write",
                 "tool_input": {"file_path": str(proj / "gates" / "決定.json"), "content": "x"}, "tool_use_id": "t"}
        out = io.BytesIO()
        self.assertEqual(pls.hook("pre", io.BytesIO(json.dumps(event, ensure_ascii=False).encode("utf-8")), out), 0)
        answer = json.loads(out.getvalue().decode("utf-8"))
        self.assertEqual(answer["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("gates/決定.json", answer["hookSpecificOutput"]["permissionDecisionReason"])

    @unittest.skipUnless(BASH, "no bash (Git Bash on Windows)")
    def test_the_installed_command_never_exits_2(self):
        cmd = json.loads((self.r / ".claude/settings.json").read_text(encoding="utf-8"))["hooks"]["Stop"][0]["hooks"][0]["command"]
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.r).replace("\\", "/"))
        (self.r / "pls.py").rename(self.r / "pls.py.away")                    # launcher missing
        res = subprocess.run([BASH, "-c", cmd], input=b"{}", capture_output=True, env=env, timeout=60)
        self.assertEqual(res.returncode, 0, res.stderr)
        env.pop("CLAUDE_PROJECT_DIR")                                        # variable not set
        res = subprocess.run([BASH, "-c", cmd], input=b"{}", capture_output=True, env=env, timeout=60)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_install_refuses_a_settings_file_that_is_not_an_object(self):
        f = self.r / ".claude/settings.json"
        f.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not a JSON object"):
            HK.install(f)
        f.write_text('{"hooks": null}', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(pls.Fail, "settings.json"):
            pls.main(["hook", "install"])


if __name__ == "__main__":
    unittest.main()
