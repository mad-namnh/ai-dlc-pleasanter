"""Outside dev, `pls test` changes records only with the person's word (the G4 approval of the release under test, or
their confirmation of the run), and a typed confirmation counts only at a terminal (I4):
python -m unittest discover -s tools/pls/tests -v"""
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
import pls_gate as GT  # noqa: E402
import test_gate as TG  # noqa: E402
import test_http as TH  # noqa: E402

R = "R-20261108-01"
TEST = ["test", "s.json", "--env", "stg", "--site", "equipment", "--out", "x.json"]


class Terminal(io.StringIO):
    """Stdin of a person at a terminal who types `text`."""

    def isatty(self):
        return True


def typed(text):
    return mock.patch("sys.stdin", Terminal(text + "\n"))


def piped(text):
    return mock.patch("sys.stdin", io.StringIO(text + "\n"))       # isatty() is False


class TestsOutsideDev(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    stg = TG.StgWriteTest.stg

    def spec(self, *steps):
        steps = steps or ({"op": "create", "site": "${site:equipment}", "save": "e", "data": {"Title": "smoke"}},
                          {"op": "delete", "record": "$e"})
        (self.r / "s.json").write_text(json.dumps([{"id": "T-1", "steps": list(steps)}]), encoding="utf-8")

    def sent(self, n):
        return [p for p, _ in self.fake.calls[n:] if p.rsplit("/", 1)[-1] in ("create", "update", "delete")]

    def test_writing_tests_on_stg_without_the_person_send_nothing(self):
        self.stg()
        self.spec()
        n = len(self.fake.calls)
        with piped("stg"):
            self.assertNotEqual(pls.main(TEST), 0)
        self.assertEqual(self.sent(n), [])

    def test_the_g4_of_the_release_under_test_allows_them(self):
        self.stg()
        self.spec()
        n = len(self.fake.calls)
        with piped(""):
            self.assertEqual(pls.main(TEST + ["--release", R]), 2)                 # no G4 recorded yet
            self.assertEqual(self.sent(n), [])
            GT.record(self.r, "G4", "approved", "Nam", "G4 approved, apply", [], [R], "2026-11-08")
            self.assertEqual(pls.main(TEST + ["--release", R]), 0)
        self.assertTrue(self.sent(n))

    def test_a_g4_of_a_release_for_another_environment_does_not_count(self):
        self.stg()
        self.plan("R-1")                                                           # a dev release
        GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], ["R-1"], "2026-11-08")
        self.spec()
        n = len(self.fake.calls)
        with piped(""):
            self.assertEqual(pls.main(TEST + ["--release", "R-1"]), 2)
        self.assertEqual(self.sent(n), [])

    def test_the_environment_name_typed_at_a_terminal_or_yes_allows_them(self):
        self.stg()
        self.spec()
        n = len(self.fake.calls)
        with typed("dev"):                                                         # not the name asked for
            self.assertEqual(pls.main(TEST), 1)
        self.assertEqual(self.sent(n), [])
        with typed("stg"):
            self.assertEqual(pls.main(TEST), 0)
        self.assertTrue(self.sent(n))
        n = len(self.fake.calls)
        with piped(""):
            self.assertEqual(pls.main(TEST + ["--yes"]), 0)
        self.assertTrue(self.sent(n))

    def test_read_only_tests_on_stg_and_writing_tests_on_dev_ask_nothing(self):
        self.stg()
        self.spec({"op": "list", "site": "${site:equipment}", "expect": {}})
        with piped(""):
            code = pls.main(TEST)
            self.spec()
            n = len(self.fake.calls)
            self.assertEqual(pls.main(["test", "s.json", "--env", "dev", "--site", "equipment", "--out", "y.json"]), 0)
        self.assertNotEqual(code, 1)                                               # never the "not confirmed" exit
        self.assertTrue(self.sent(n))


class TypedConfirmationNeedsATerminal(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan

    def planned(self):
        plan, d = self.plan()
        for site in plan["per_site"]:
            plan["per_site"][site]["payload_file"] = f"payload-{site}.json"
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def test_a_release_id_piped_into_apply_is_not_a_confirmation(self):
        self.planned()
        with piped("R-1"):
            self.assertEqual(pls.main(["apply", "R-1"]), 1)
        self.assertEqual(self.fake.sites[TH.EQ]["Title"], "eq")                    # nothing written

    def test_a_release_id_typed_at_a_terminal_still_confirms(self):
        self.planned()
        n = len(self.fake.calls)
        with typed("R-1"):
            pls.main(["apply", "R-1"])
        self.assertTrue([p for p, _ in self.fake.calls[n:] if p.endswith("/updatesite")])


if __name__ == "__main__":
    unittest.main()
