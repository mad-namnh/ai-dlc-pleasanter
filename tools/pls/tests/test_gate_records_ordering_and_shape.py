"""Which gate decision counts: ordered by the instant in `at` (not the recorder's local date), a rejection wins a tie,
a future-dated record is refused, and a record of the wrong shape stops every gate check instead of being read
loosely (a `releases` string would approve ids by substring). Fake Pleasanter on 127.0.0.1 only."""
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import test_gate as TG  # noqa: E402
import test_http as TH  # noqa: E402

R = "R-20261108-01"


def hand_record(root: Path, name: str, **fields) -> Path:
    """A record as it could arrive from another machine or branch (not written by `pls gate` here)."""
    rec = {"gate": "G4", "decision": "approved", "approver": "Nam", "date": "2026-11-08", "quote": "q",
           "items": [], "releases": [R], "recorded_by": "pls gate"}
    rec.update(fields)
    d = root / "gates"
    d.mkdir(exist_ok=True)
    p = d / f"{name}.json"
    p.write_text(json.dumps(rec), encoding="utf-8")
    return p


class OrderingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "CLAUDE.md").write_text(TG.PROFILE, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_later_rejection_from_an_earlier_local_date_still_wins(self):
        # approved at 00:30 on the 9th in UTC+9; rejected at 23:00 on the 8th in UTC+7 = 01:00 on the 9th in UTC+9
        hand_record(self.r, "2026-11-09-G4-a", date="2026-11-09", at="2026-11-09T00:30:00.000000+09:00")
        hand_record(self.r, "2026-11-08-G4-b", date="2026-11-08", at="2026-11-08T23:00:00.000000+07:00",
                    decision="rejected", quote="stop")
        self.assertEqual(GT.latest(self.r, "G4", release=R)["decision"], "rejected")
        with self.assertRaisesRegex(GT.GateError, "last decision: rejected"):
            GT.require(self.r, "G4", R, "applying to stg")

    def test_on_the_same_instant_a_rejection_wins_whatever_the_file_names(self):
        at = "2026-11-08T10:00:00.000000+09:00"
        for first, second in (("a", "b"), ("b", "a")):
            with self.subTest(order=first):
                for p in (self.r / "gates").glob("*.json") if (self.r / "gates").exists() else []:
                    p.unlink()
                # same instant written in two zones; the approval's text sorts later, the rejection must still win
                hand_record(self.r, f"x-{first}", at="2026-11-08T01:00:00.000000+00:00", decision="rejected", quote="stop")
                hand_record(self.r, f"x-{second}", at=at)
                self.assertEqual(GT.latest(self.r, "G4", release=R)["decision"], "rejected")

    def test_a_future_dated_record_is_refused(self):
        future = (datetime.now().astimezone() + timedelta(days=1)).isoformat(timespec="microseconds")
        hand_record(self.r, "forged", at=future)
        with self.assertRaisesRegex(GT.GateError, "in the future"):
            GT.require(self.r, "G4", R, "applying to stg")
        with self.assertRaisesRegex(GT.GateError, "in the future"):     # and it cannot pile up behind new records
            GT.record(self.r, "G4", "rejected", "Nam", "stop", [], [R], "2026-11-08")

    def test_a_record_a_few_minutes_ahead_is_accepted(self):
        ahead = (datetime.now().astimezone() + timedelta(minutes=2)).isoformat(timespec="microseconds")
        hand_record(self.r, "skewed", at=ahead)
        self.assertEqual(GT.latest(self.r, "G4", release=R)["decision"], "approved")
        later = GT.record(self.r, "G4", "rejected", "Nam", "stop", [], [R], "2026-11-08")   # still sorts after it
        self.assertEqual(GT.latest(self.r, "G4", release=R)["quote"], json.loads(later.read_text(encoding="utf-8"))["quote"])


class ShapeTest(unittest.TestCase):
    setUp = OrderingTest.setUp
    tearDown = OrderingTest.tearDown
    AT = "2026-11-08T10:00:00.000000+09:00"

    def test_wrong_shapes_refuse_every_gate_check(self):
        cases = {
            "releases string": {"releases": "R-20261108-01X"},           # would match R by substring
            "items of numbers": {"items": [1]},
            "approver null": {"approver": None},
            "unknown decision": {"decision": "ok"},
            "unknown gate": {"gate": "G5"},
            "at without offset": {"at": "2026-11-08T10:00:00"},
            "at missing": {"at": None},
        }
        for label, fields in cases.items():
            with self.subTest(label):
                for p in (self.r / "gates").glob("*.json") if (self.r / "gates").exists() else []:
                    p.unlink()
                hand_record(self.r, "bad", **dict({"at": self.AT}, **fields))
                with self.assertRaisesRegex(GT.GateError, "gates/bad.json"):
                    GT.require(self.r, "G4", R, "applying to stg")

    def test_a_string_releases_never_approves_a_shorter_id(self):
        hand_record(self.r, "g4-r30", at=self.AT, releases="R-30")
        with self.assertRaises(GT.GateError):
            GT.require(self.r, "G4", "R-3", "applying to stg")

    def test_a_record_with_a_bom_is_read(self):
        p = hand_record(self.r, "bom", at=self.AT, gate="G1", items=["REQ-001"], releases=[])
        p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())
        self.assertEqual(GT.latest(self.r, "G1", item="REQ-001")["decision"], "approved")

    def test_bad_json_is_a_refusal_and_a_lint_finding_not_a_traceback(self):
        (self.r / "gates").mkdir()
        (self.r / "gates/broken.json").write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "gates/broken.json"):
            GT.require(self.r, "G4", R, "applying to stg")
        issues = GT.lint(self.r)
        self.assertEqual([i["rule"] for i in issues], ["L-GATE-01"])
        self.assertIn("gates/broken.json", issues[0]["msg"])


class ApplyAfterRejectionTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    stg = TG.StgWriteTest.stg
    writes = TG.StgWriteTest.writes

    def test_apply_on_stg_stops_after_a_later_rejection_from_another_time_zone(self):
        self.stg()
        g4 = GT.record(self.r, "G4", "approved", "Nam", "G4 approved", [], [R], "2026-11-08")
        at = datetime.fromisoformat(json.loads(g4.read_text(encoding="utf-8"))["at"])
        later_utc7 = (at + timedelta(seconds=1)).astimezone(timezone(timedelta(hours=7)))
        hand_record(self.r, "rejection-from-utc7", date="2000-01-01", decision="rejected", quote="stop",
                    at=later_utc7.isoformat(timespec="microseconds"))      # earliest local date of all records
        n = len(self.fake.calls)
        self.assertEqual(pls.main(["apply", R, "--yes"]), 2)
        self.assertEqual(self.writes(n), [])


if __name__ == "__main__":
    unittest.main()
