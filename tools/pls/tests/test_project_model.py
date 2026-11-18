"""Every phase of a project runs on the model its skills were evaluated on (ADR-0031, team rollout N13): the project's
`.claude/settings.json` names it, and a PreModelSwitch hook denies a switch to another model; the developer does not
choose. Event shapes follow the Claude Code hooks reference (`to_model` is a model ID)."""
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
import pls  # noqa: E402
import pls_hooks as HK  # noqa: E402


class ModelSwitchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / ".claude").mkdir()
        (self.r / "environments.json").write_text(json.dumps({"envs": {}}), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def settings(self, **kw):
        (self.r / ".claude" / "settings.json").write_text(json.dumps(kw), encoding="utf-8")

    def decide(self, to_model):
        return HK.model_switch(self.r, {"hook_event_name": "PreModelSwitch", "from_model": "claude-opus-5-5",
                                        "to_model": to_model, "requested_model": None, "source": "command"})

    def test_an_alias_allows_its_family_and_denies_any_other_model(self):
        self.settings(model="opus")
        for ok in ("claude-opus-5-5", "claude-opus-5", "claude-opus-5-5[1m]"):
            self.assertIsNone(self.decide(ok), ok)
        for other in ("claude-sonnet-5-5", "claude-haiku-5-5", "claude-fable-5-2"):       # stronger ones too (N13, 3a)
            out = self.decide(other)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny", other)
            self.assertIn("settings.json", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_a_model_id_allows_only_itself(self):
        self.settings(model="claude-opus-5-5")
        self.assertIsNone(self.decide("claude-opus-5-5"))
        self.assertIsNone(self.decide("claude-opus-5-5[1m]"))
        self.assertEqual(self.decide("claude-opus-5")["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_context_suffix_is_the_same_model_and_a_shorter_id_is_not_a_family(self):
        self.settings(model="opus[1m]")
        self.assertIsNone(self.decide("claude-opus-5-5[1m]"))
        self.assertIsNone(self.decide("claude-opus-5-5"))
        self.assertEqual(self.decide("claude-sonnet-5-5")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.settings(model="claude-opus-5")                  # an ID names one model, not every longer ID after it
        self.assertEqual(self.decide("claude-opus-5-5")["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIsNone(self.decide("claude-opus-5-20260101"))

    def test_a_setting_the_check_cannot_read_never_locks_the_project(self):
        for value in ("opusplan", "best", "my-gateway-model"):
            self.settings(model=value)
            self.assertIsNone(self.decide("claude-opus-5-5"), value)
            self.assertIsNone(self.decide("claude-sonnet-5-5"), value)

    def test_nothing_configured_or_an_unreadable_event_lets_the_switch_go(self):
        self.assertIsNone(self.decide("claude-sonnet-5-5"))                 # no settings file
        self.settings(hooks={})
        self.assertIsNone(self.decide("claude-sonnet-5-5"))                 # no model in it
        self.settings(model="opus")
        self.assertIsNone(HK.model_switch(self.r, {}))                       # no target model in the event

    def test_the_hook_command_answers_with_json_and_never_fails(self):
        self.settings(model="opus")
        old = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.r)
        try:
            out = io.BytesIO()
            self.assertEqual(pls.hook("model", stdin=io.BytesIO(json.dumps({"to_model": "claude-sonnet-5-5"}).encode()),
                                      stdout=out), 0)
            self.assertEqual(json.loads(out.getvalue())["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(pls.hook("model", stdin=io.BytesIO(b"not json"), stdout=io.BytesIO()), 0)
        finally:
            if old is None:
                os.environ.pop("CLAUDE_PROJECT_DIR", None)
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = old


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.f = Path(self.tmp.name) / "settings.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_sets_the_project_model_once_and_keeps_a_chosen_one(self):
        HK.install(self.f)
        data = json.loads(self.f.read_text(encoding="utf-8"))
        self.assertEqual(data["model"], "opus")
        self.assertTrue(data["hooks"]["PreModelSwitch"][0]["hooks"][0]["command"].endswith("hook model || true"))
        data["model"] = "claude-opus-5-5"                                   # the project chose by a commit
        self.f.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(HK.install(self.f), [])
        self.assertEqual(json.loads(self.f.read_text(encoding="utf-8"))["model"], "claude-opus-5-5")
        for empty in ("", None, 5):                                          # an empty value would switch the check off
            data["model"] = empty
            self.f.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(HK.install(self.f), ["model"])
            self.assertEqual(json.loads(self.f.read_text(encoding="utf-8"))["model"], "opus")


if __name__ == "__main__":
    unittest.main()
