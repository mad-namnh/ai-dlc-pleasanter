"""Refusals tell the person what to do next, and an unexpected error ends in one line without a Python trace
(design review C5): the release-state and stale-plan refusals name a `pls` command, a string where a list of mail
changes is expected is printed whole, and the command line prints a trace only with PLS_DEBUG=1."""
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import pls_side_effects as SE  # noqa: E402
import test_http as TH  # noqa: E402


class ReleaseStateMessageTest(unittest.TestCase):
    def test_a_release_that_wrote_is_read_back_not_applied_again(self):
        for st in pls.OPEN_STATES:
            msg = pls.not_planned_message("R-1", {"status": st, "sites": ["loans", "equipment"]})
            self.assertIn(f"has status {st!r}, not 'planned'", msg)
            self.assertIn("do not apply it again", msg)
            self.assertIn("pls mark-applied R-1 --export loans=<file> --export equipment=<file>", msg)

    def test_any_other_state_asks_for_a_new_release_plan(self):
        for st in ("applied", "rolled-back", "refused", None):
            msg = pls.not_planned_message("R-1", {"status": st, "sites": ["loans"]})
            self.assertIn("pls release-plan with a new id", msg)
            self.assertNotIn("mark-applied", msg)

    def test_stale_site_names_the_environment_and_the_next_step(self):
        msg = pls.stale_site_message("R-1", "loans", 902, "dev-x")
        self.assertIn("loans → site 902 is not a site this release may write in dev-x", msg)
        self.assertIn("envs.dev-x.sites", msg)
        self.assertIn("pls release-plan with a new id", msg)


class ApplyRefusalTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def test_apply_of_a_used_release_names_the_next_step_and_sends_nothing(self):
        plan, d = self.plan("R-USED")
        for status, next_action in (("applied", "pls release-plan with a new id"),
                                    ("applied-unverified", "pls mark-applied R-USED --export equipment=<file>")):
            (d / "plan.json").write_text(json.dumps(dict(plan, status=status)), encoding="utf-8")
            n, err = len(self.fake.calls), io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(pls.main(["apply", "R-USED", "--yes"]), 2)
            self.assertIn(f"has status '{status}', not 'planned'", err.getvalue())
            self.assertIn(next_action, err.getvalue())
            self.assertFalse(any(p.endswith("/updatesite") for p, _ in self.fake.calls[n:]))


class MailChangeDetailTest(unittest.TestCase):
    def test_a_string_value_is_one_item_not_its_characters(self):
        refusal, _ = SE.apply_refusal("dev", {"mail": "unknown", "jobs": "unknown"},
                                      {"loans": "Notifications[1] added"})
        self.assertIn("loans: Notifications[1] added", refusal)
        self.assertNotIn("N, o, t", refusal)


class CommandLineErrorTest(unittest.TestCase):
    def run_cli(self, exc, debug):
        err = io.StringIO()
        env = {k: v for k, v in os.environ.items() if k != "PLS_DEBUG"}
        if debug:
            env["PLS_DEBUG"] = "1"
        with mock.patch.dict(os.environ, env, clear=True), mock.patch.object(pls, "main", side_effect=exc), \
                contextlib.redirect_stderr(err):
            code = pls.cli(["version"])
        return code, err.getvalue()

    def test_unexpected_error_is_one_line_without_a_trace(self):
        code, out = self.run_cli(RuntimeError("boom\nsecond line"), debug=False)
        self.assertEqual(code, 3)
        self.assertNotIn("Traceback", out)
        self.assertIn("pls: unexpected error (RuntimeError: boom)", out)
        self.assertNotIn("second line", out)
        self.assertIn("PLS_DEBUG=1", out)

    def test_the_trace_is_shown_when_asked_for(self):
        code, out = self.run_cli(KeyError("x"), debug=True)
        self.assertEqual(code, 3)
        self.assertIn("Traceback", out)
        self.assertIn("pls: unexpected error (KeyError", out)

    def test_a_refusal_stays_one_line_with_exit_2(self):
        code, out = self.run_cli(pls.Fail("R-1 has no plan.json — make a release plan first"), debug=False)
        self.assertEqual(code, 2)
        self.assertEqual(out, "pls: R-1 has no plan.json — make a release plan first\n")


if __name__ == "__main__":
    unittest.main()
