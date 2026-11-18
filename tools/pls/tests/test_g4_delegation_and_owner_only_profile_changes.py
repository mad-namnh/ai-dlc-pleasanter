"""A team approves gates (ADR-0020): every dev may approve G1–G3, G4 stays with its owner, who delegates it only for
a stated time. Only a G4 approver without an end date changes the rows that decide who may release outside dev —
Approvers, Operators and an environment's role — so nobody widens their own rights."""
import json
import sys
import time
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import pls_profile_records as PR  # noqa: E402
import test_pls as TP  # noqa: E402

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
NEXT_WEEK = (TODAY + timedelta(days=7)).isoformat()
TEAM = "G1–G3: Nam, Taro, Hana; G4: Nam"


def row(value: str) -> str:
    return f"| Approvers | {value} |"


class DelegationParseTest(unittest.TestCase):
    def test_a_delegation_counts_up_to_its_last_day_and_not_after(self):
        text = row(f"{TEAM}; G4 until {NEXT_WEEK}: Taro")
        self.assertEqual(GT.approvers(text)["Taro"], {"G1", "G2", "G3", "G4"})
        last = date.fromisoformat(NEXT_WEEK)
        self.assertIn("G4", GT.approvers(text, on=last)["Taro"])                         # the last day is included
        self.assertEqual(GT.approvers(text, on=last + timedelta(days=1))["Taro"], {"G1", "G2", "G3"})
        self.assertEqual(GT.owners(text), {"Nam"})

    def test_the_name_form_takes_an_end_date_too(self):
        text = row(f"Nam (all gates), Taro (G4 until {NEXT_WEEK})")
        self.assertEqual(GT.grants(text)["Taro"], {"G4": date.fromisoformat(NEXT_WEEK)})
        self.assertEqual(GT.owners(text), {"Nam"})

    def test_an_until_without_a_date_grants_nothing(self):
        # never read as a grant without an end date (that would make the delegate an owner)
        for value in ("G4 until next week: Taro", "Taro (G4 until Friday)", "G4 until 2026-13-40: Taro"):
            with self.subTest(value=value):
                self.assertNotIn("Taro", GT.grants(row(f"Nam (all gates); {value}")))

    def test_a_name_left_without_any_gate_is_not_an_approver(self):
        text = row(f"G4: Nam; G4 until {YESTERDAY}: Taro")
        self.assertNotIn("Taro", GT.approvers(text))
        self.assertIn("Taro", GT.grants(text))          # still a name the row holds (lint of past approvals)

    def test_an_end_date_written_after_the_name_grants_nothing(self):
        # "Taro until <date>" must not become a name holding G4 without an end date
        text = row(f"G1–G3: Nam, Taro; G4: Nam, Taro until {NEXT_WEEK}")
        self.assertEqual(GT.owners(text), {"Nam"})
        self.assertNotIn(f"Taro until {NEXT_WEEK}", GT.grants(text))

    def test_the_longer_grant_counts(self):
        self.assertEqual(GT.grants(row(f"G4: Nam; G4 until {NEXT_WEEK}: Nam"))["Nam"], {"G4": GT.PERMANENT})


class TeamProfile:
    """A project whose owner Nam recorded the team row: G1–G3 for every dev, G4 for himself."""
    tearDown = TP.PlsTest.tearDown

    def setUp(self):
        TP.PlsTest.setUp(self)
        (self.r / "CLAUDE.md").write_text("| Item | Value |\n|---|---|\n| Origin | `new` |\n| Approvers | Nam (all gates) |\n"
                                          "| Operators | dev: Nam; stg: Nam |\n", encoding="utf-8")
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "every dev approves G1 to G3, G4 stays with me")


class OwnerOnlyChangesTest(TeamProfile, unittest.TestCase):
    def test_a_g1_to_g3_approver_cannot_widen_their_rights(self):
        with self.assertRaisesRegex(GT.GateError, "changed only by a G4 approver without an end date"):
            PR.set_field(self.r, "Approvers", "G1–G3: Nam, Taro, Hana; G4: Nam, Taro", "Taro", "I approve G4 too")
        with self.assertRaisesRegex(GT.GateError, "changed only by a G4 approver"):
            PR.set_field(self.r, "Operators", "dev: Nam; stg: Taro", "Taro", "I deploy stg")
        # a stg that counts as dev would need no G4 at all
        with self.assertRaisesRegex(pls.Fail, "changed only by a G4 approver"):
            pls.main(["profile", "set", "role", "dev", "--env", "stg", "--approver", "Taro", "--quote", "stg is dev now"])
        self.assertEqual(json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["stg"]["role"], "stg")

    def test_the_owner_delegates_g4_for_a_stated_time_only(self):
        with self.assertRaisesRegex(GT.GateError, "new G4 approver needs an end date"):
            PR.set_field(self.r, "Approvers", f"{TEAM}, Taro", "Nam", "Taro approves G4")
        with self.assertRaisesRegex(GT.GateError, "already past"):
            PR.set_field(self.r, "Approvers", f"{TEAM}; G4 until {YESTERDAY}: Taro", "Nam", "Taro while I am away")
        PR.set_field(self.r, "Approvers", f"{TEAM}; G4 until {NEXT_WEEK}: Taro", "Nam", "Taro approves G4 while I am away")
        self.assertEqual(GT._approver_for(self.r, "Taro", "G4"), "Taro")
        # the delegate cannot delegate further, name stg operators or make stg count as dev
        with self.assertRaisesRegex(GT.GateError, "changed only by a G4 approver"):
            PR.set_field(self.r, "Approvers", f"{TEAM}; G4 until {NEXT_WEEK}: Taro, Hana", "Taro", "Hana too")
        with self.assertRaisesRegex(GT.GateError, "changed only by a G4 approver"):
            PR.set_field(self.r, "Operators", "dev: Nam; stg: Taro", "Taro", "I deploy stg")
        with self.assertRaisesRegex(pls.Fail, "changed only by a G4 approver"):
            pls.main(["profile", "set", "role", "dev", "--env", "stg", "--approver", "Taro", "--quote", "stg is dev now"])
        # the owner ends the delegation early by recording the row without it
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "Taro's G4 ends now, I am back")
        with self.assertRaisesRegex(GT.GateError, "not G4"):
            GT._approver_for(self.r, "Taro", "G4")

    def test_a_first_value_with_the_end_date_after_the_name_makes_no_owner_of_it(self):
        (self.r / "CLAUDE.md").write_text("| Approvers | G1, G4: <name>; G2, G3: <name> |\n", encoding="utf-8")
        for p in (self.r / "gates/profile").glob("*.json"):
            p.unlink()
        PR.set_field(self.r, "Approvers", f"G1–G3: Nam, Taro; G4: Nam, Taro until {NEXT_WEEK}", "Nam", "Taro for a week")
        self.assertEqual(GT.owners(PR.effective_profile_text(self.r)), {"Nam"})

    def test_the_row_keeps_an_owner(self):
        with self.assertRaisesRegex(GT.GateError, "names no G4 approver without an end date"):
            PR.set_field(self.r, "Approvers", f"G1–G3: Nam, Taro; G4 until {NEXT_WEEK}: Taro", "Nam", "Taro takes over")

    def test_the_first_value_makes_its_author_the_owner(self):
        (self.r / "CLAUDE.md").write_text("| Approvers | G1, G4: <name>; G2, G3: <name> |\n", encoding="utf-8")
        for p in (self.r / "gates/profile").glob("*.json"):
            p.unlink()
        with self.assertRaisesRegex(GT.GateError, "first Approvers value names the person who states it as a G4"):
            PR.set_field(self.r, "Approvers", "G1–G3: Nam; G4: Taro", "Nam", "Taro releases")
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "every dev approves G1 to G3, G4 stays with me")
        self.assertEqual(GT.owners(PR.effective_profile_text(self.r)), {"Nam"})


class NamesAndFirstValueTest(TeamProfile, unittest.TestCase):
    """Names with digits stay names; only a template placeholder with no record lets a first value be stated."""
    def test_a_name_with_digits_is_a_name(self):
        self.assertEqual(GT.approvers(row("dev01 (all gates)")), {"dev01": set(GT.GATES)})
        self.assertEqual(GT.approvers(row("G1, G4: user1; G2, G3: user2")),
                         {"user1": {"G1", "G4"}, "user2": {"G2", "G3"}})

    def test_a_recorded_value_is_never_replaced_as_a_first_value(self):
        PR.set_field(self.r, "Approvers", "G1–G3: dev01, dev02; G4: Nam", "Nam", "dev01 and dev02 approve G1 to G3")
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            PR.set_field(self.r, "Approvers", "Mallory (all gates)", "Mallory", "me")

    def test_a_row_whose_grants_have_all_ended_is_not_a_first_value(self):
        (self.r / "CLAUDE.md").write_text(f"| Approvers | G4 until {YESTERDAY}: Taro |\n", encoding="utf-8")
        for p in (self.r / "gates/profile").glob("*.json"):
            p.unlink()
        with self.assertRaisesRegex(GT.GateError, "names no approver today"):
            PR.set_field(self.r, "Approvers", "Mallory (all gates)", "Mallory", "me")


class JobsVerifiedJudgedAtItsTimeTest(TeamProfile, unittest.TestCase):
    def test_a_delegate_confirmation_counts_after_the_delegation_is_removed(self):
        PR.set_field(self.r, "Approvers", f"{TEAM}; G4 until {NEXT_WEEK}: Ken", "Nam", "Ken releases while I am away")
        time.sleep(1.05)                                   # the confirmation's `at` has whole seconds
        during = datetime.now().astimezone().isoformat(timespec="seconds")
        time.sleep(1.05)                                   # the confirmation's `at` has whole seconds
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "I am back")
        time.sleep(1.05)
        after = datetime.now().astimezone().isoformat(timespec="seconds")
        v = {"by": "Ken", "role": "g4-approver", "env": "stg", "quote": "copied and checked"}
        self.assertTrue(pls._jobs_verified_holds(self.r, {**v, "at": during}, "stg"))
        self.assertFalse(pls._jobs_verified_holds(self.r, {**v, "at": after}, "stg"))


class RoleFileAndRecordTest(TeamProfile, unittest.TestCase):
    def test_a_hand_edited_role_stops_every_command_that_reads_it(self):
        # stg edited to dev by hand would need no G4: the role record wins, the commands refuse
        self.assertEqual(pls.main(["profile", "set", "role", "stg", "--env", "stg", "--approver", "Nam",
                                   "--quote", "stg is MADLAB's stg"]), 0)
        p = self.r / "environments.json"
        envs = json.loads(p.read_text(encoding="utf-8"))
        envs["envs"]["stg"]["role"] = "dev"
        p.write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "edited by hand"):
            pls.env_conf(self.r, "stg")
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design" / "roles.json").write_text(json.dumps({"roles": {}}), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "edited by hand"):          # groups are never created on it either
            pls.bind_principals(self.r, "stg", None, create=True)
        with self.assertRaisesRegex(pls.Fail, "edited by hand"):          # nor are group ids bound into it
            pls.bind_principals(self.r, "stg", None)
        envs["envs"]["stg"]["role"] = "stg"
        p.write_text(json.dumps(envs), encoding="utf-8")
        self.assertEqual(pls.env_conf(self.r, "stg")["role"], "stg")


class HandEditedRowTest(TeamProfile, unittest.TestCase):
    def test_a_backdated_record_is_judged_by_the_first_record_not_the_row(self):
        # a hand edit of the row plus a hand-written record dated before the first Approvers record
        p = self.r / "CLAUDE.md"
        p.write_text(PR._row("Approvers").sub("| Approvers | Taro (all gates) |", p.read_text(encoding="utf-8"), count=1),
                     encoding="utf-8")
        with self.assertRaisesRegex(GT.GateError, "not G4"):
            GT._approver_for(self.r, "Taro", "G4", at=datetime(2020, 1, 1).astimezone())


class StatusLinesTest(TeamProfile, unittest.TestCase):
    def test_a_status_line_by_a_removed_delegate_is_not_a_finding(self):
        PR.set_field(self.r, "Approvers", f"{TEAM}; G2 until {NEXT_WEEK}: Ken", "Nam", "Ken designs while I am away")
        time.sleep(0.05)
        d = self.r / "design" / "decisions"
        d.mkdir(parents=True, exist_ok=True)
        (d / "DES-001-loans.md").write_text("# DES-001\n\nStatus: G2 approved by Ken\n", encoding="utf-8")
        GT.record(self.r, "G2", "approved", "Ken", "approved", ["DES-001"], [], TODAY.isoformat())
        time.sleep(0.05)
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "I am back")
        msgs = [i["msg"] for i in GT.lint(self.r) if i["rule"] == "L-GATE-01"]
        self.assertFalse([m for m in msgs if "Ken" in m], msgs)
        # a name that never approved it stays a finding
        (d / "DES-001-loans.md").write_text("# DES-001\n\nStatus: G2 approved by Mallory\n", encoding="utf-8")
        self.assertTrue(any("Mallory" in i["msg"] for i in GT.lint(self.r) if i["rule"] == "L-GATE-01"))


class NoOwnerTest(unittest.TestCase):
    tearDown = TP.PlsTest.tearDown

    def setUp(self):
        TP.PlsTest.setUp(self)
        (self.r / "CLAUDE.md").write_text("| Item | Value |\n|---|---|\n| Approvers | G1–G3: Nam, Taro |\n"
                                          "| Operators | dev: Nam; stg: Nam |\n", encoding="utf-8")

    def test_without_an_owner_nobody_takes_g4(self):
        with self.assertRaisesRegex(GT.GateError, "names no G4 approver without an end date, so nobody may change"):
            PR.set_field(self.r, "Approvers", "G1–G3: Nam; G4: Taro", "Taro", "I take G4")
        with self.assertRaisesRegex(GT.GateError, "nobody may change Operators"):
            PR.set_field(self.r, "Operators", "dev: Nam; stg: Taro", "Nam", "Taro deploys stg")
        self.assertTrue(any("names no G4 approver without an end date" in i["msg"] for i in PR.lint(self.r)))


class ApprovalJudgedByTheProfileOfItsTimeTest(unittest.TestCase):
    tearDown = TP.PlsTest.tearDown

    def setUp(self):
        TP.PlsTest.setUp(self)
        (self.r / "CLAUDE.md").write_text("| Item | Value |\n|---|---|\n| Approvers | Nam (all gates) |\n", encoding="utf-8")
        PR.set_field(self.r, "Approvers", f"{TEAM}; G3 until {NEXT_WEEK}: Ken", "Nam", "Ken approves G3 while I am away")
        time.sleep(0.05)

    def test_a_delegate_approval_survives_the_end_of_the_delegation_in_the_row(self):
        GT.record(self.r, "G3", "approved", "Ken", "approved", [], ["R-1"], TODAY.isoformat())
        time.sleep(0.05)
        PR.set_field(self.r, "Approvers", TEAM, "Nam", "I am back; Ken's delegation ends")
        GT.require(self.r, "G3", "R-1", "a release plan for stg")          # made under the delegation: still counts
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            GT.validate(self.r, "G3", "approved", "Ken", "approved", [], ["R-2"])   # a new approval does not

    def test_an_approval_is_undone_by_a_later_decision(self):
        GT.record(self.r, "G3", "approved", "Ken", "approved", [], ["R-1"], TODAY.isoformat())
        time.sleep(0.05)
        GT.record(self.r, "G3", "changes-requested", "Nam", "not this one", [], ["R-1"], TODAY.isoformat())
        with self.assertRaisesRegex(GT.GateError, "last decision: changes-requested"):
            GT.require(self.r, "G3", "R-1", "a release plan for stg")


class DelegateApprovalOutlivesTheDelegationTest(unittest.TestCase):
    tearDown = TP.PlsTest.tearDown

    def setUp(self):
        TP.PlsTest.setUp(self)
        (self.r / "CLAUDE.md").write_text(f"| Item | Value |\n|---|---|\n| Approvers | {TEAM}; G3 until {YESTERDAY}: Ken |\n",
                                          encoding="utf-8")
        (self.r / "gates").mkdir(exist_ok=True)

    def write_g3(self, at: datetime) -> None:
        rec = {"gate": "G3", "decision": "approved", "approver": "Ken", "date": at.date().isoformat(),
               "at": at.isoformat(timespec="microseconds"), "quote": "approved", "items": [], "releases": ["R-1"]}
        (self.r / "gates" / f"{at.date().isoformat()}-G3-x.json").write_text(json.dumps(rec), encoding="utf-8")

    def test_an_approval_made_inside_the_delegation_still_counts(self):
        self.write_g3(datetime.now().astimezone() - timedelta(days=2))
        GT.require(self.r, "G3", "R-1", "a release plan for stg")

    def test_an_approval_dated_after_the_delegation_does_not(self):
        self.write_g3(datetime.now().astimezone())
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            GT.require(self.r, "G3", "R-1", "a release plan for stg")
        with self.assertRaisesRegex(GT.GateError, "not an approver"):
            GT.validate(self.r, "G3", "approved", "Ken", "approved", [], ["R-1"])


if __name__ == "__main__":
    unittest.main()
