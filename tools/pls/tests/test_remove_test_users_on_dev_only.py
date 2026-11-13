"""`pls test-users --env dev --remove` (TD-24; Nam 2026-11-12 "Build, dev only"): deletes only the test users this
machine proves pls created here (password file and a key file whose key the API accepts now), checks they are gone,
then removes their key and password files and the test user's own keys.<role> — never on stg, prod or a sandbox,
never without allow_write or a confirmation, never a user that is not proven, never printing a secret. Fake
Pleasanter on 127.0.0.1 only."""
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import test_test_users_on_dev_only as T  # noqa: E402

LOGIN = "zz_test_pls_demo_x_somu"


class RemoveTestUsers(unittest.TestCase):
    """Borrows the fake, the project and the helpers of the test-users tests (no inheritance: those run once)."""
    setUp_project = T.TestUsers.setUp
    tearDown = T.TestUsers.tearDown
    run_pls = T.TestUsers.run_pls
    conns = T.TestUsers.conns

    def setUp(self):
        self.setUp_project()
        rc, out = self.run_pls("--env", "dev", "--yes")                 # a test user made by pls on this machine
        self.assertEqual(rc, 0, out)
        self.uid = max(self.fake.users)
        self.pw = self.r / ".pls/test-users/dev-somu.password"
        self.key = self.r / ".pls/test-users/dev-somu.key"
        self.secrets = (self.pw.read_text(encoding="utf-8").strip(), self.key.read_text(encoding="utf-8").strip())

    def remove(self, *extra):
        return self.run_pls("--env", "dev", "--remove", *extra)

    def deletes(self, n=0):
        return [p for _, p in self.fake.calls[n:] if p.endswith("/delete")]

    def test_the_user_is_deleted_checked_gone_then_its_files_and_reference_removed(self):
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.deletes(), [f"/api/users/{self.uid}/delete"])
        self.assertNotIn(self.uid, self.fake.users)
        self.assertNotIn(f"User,{self.uid},False", self.fake.groups[374]["GroupMembers"])
        self.assertFalse(self.pw.exists() or self.key.exists())
        self.assertEqual(self.conns()["dev"]["keys"], {"admin": "env:T_ADMIN"})
        for secret in self.secrets + (T.ADMIN_KEY, "S3CRET"):
            self.assertNotIn(secret, out)
        ev = [json.loads(x) for f in sorted((self.r / "ops/log").glob("*.jsonl"))
              for x in f.read_text(encoding="utf-8").splitlines() if '"test-users"' in x][-1]
        self.assertEqual(ev["metrics"], {"test_users_delete_answered": [self.uid], "test_users_removed": [self.uid]})
        n = len(self.fake.calls)
        rc, out = self.remove("--yes")                                 # nothing left: no request writes
        self.assertEqual((rc, self.deletes(n)), (0, []), out)

    def test_stg_prod_and_sandboxes_are_refused_before_any_request(self):
        for env in ("stg", "prod", "sbx"):
            n = len(self.fake.calls)
            with self.assertRaisesRegex(pls.Fail, "only on a dev environment", msg=env):
                self.run_pls("--env", env, "--remove", "--yes")
            self.assertEqual(self.fake.calls[n:], [], env)

    def test_no_delete_without_allow_write_or_confirmation(self):
        c = self.conns()
        c["dev"]["allow_write"] = False
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "REFUSED"):
            self.remove("--yes")
        c["dev"]["allow_write"] = True
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "not confirmed"):
            self.remove()                                              # no --yes, no terminal
        self.assertEqual(self.deletes(), [])
        self.assertTrue(self.pw.exists() and self.key.exists())

    def test_a_connections_file_outside_the_project_is_refused(self):
        alt = Path(self.tmp.name) / "elsewhere.json"
        alt.write_text((self.r / ".pls/connections.json").read_text(encoding="utf-8"), encoding="utf-8")
        os.environ["PLS_CONNECTIONS"] = str(alt)
        try:
            with self.assertRaisesRegex(pls.Fail, "not the project's .pls/connections.json"):
                self.remove("--yes")
        finally:
            os.environ.pop("PLS_CONNECTIONS")
        self.assertEqual(self.deletes(), [])

    def test_a_user_without_the_password_file_is_never_deleted(self):
        self.pw.unlink()                                               # not created by pls on this machine
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1)
        self.assertIn("PERSON STEP", out)
        self.assertIn("not deleted", out)
        self.assertEqual(self.deletes(), [])
        self.assertIn(self.uid, self.fake.users)

    def remake_by_someone_else(self):
        """The test user deleted by hand (its key dies with it), then a user with the same LoginId made by another
        operator: this machine's password file is stale."""
        del self.fake.users[self.uid]
        for k in [k for k, v in self.fake.keys.items() if v == self.uid]:
            del self.fake.keys[k]
        self.fake.users[600] = {"UserId": 600, "LoginId": LOGIN, "password": "someone-elses"}

    def test_a_user_made_again_by_someone_else_is_not_deleted_on_a_stale_password_file(self):
        self.remake_by_someone_else()
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1, out)
        self.assertIn("PERSON STEP", out)
        self.assertIn("not proven", out)
        self.assertEqual(self.deletes(), [])
        self.assertIn(600, self.fake.users)
        self.assertTrue(self.pw.exists() and self.key.exists())
        self.assertIn("somu", self.conns()["dev"]["keys"])

    def test_a_user_without_a_key_file_or_with_the_operators_key_is_not_deleted(self):
        self.key.unlink()
        rc, out = self.remove("--yes")
        self.assertEqual((rc, self.deletes()), (1, []), out)
        self.assertIn("not proven", out)
        self.key.write_text(T.ADMIN_KEY, encoding="utf-8")      # the operator's key: accepted, but not the user's
        rc, out = self.remove("--yes")
        self.assertEqual((rc, self.deletes()), (1, []), out)
        self.assertNotIn(T.ADMIN_KEY, out)
        self.assertIn(self.uid, self.fake.users)
        self.assertTrue(self.pw.exists())

    def test_password_files_of_roles_no_longer_in_the_design_are_named_for_a_person(self):
        orphan = self.r / ".pls/test-users/dev-keiri.password"
        orphan.write_text("x", encoding="utf-8")
        (self.r / ".pls/test-users/devx-keiri.password").write_text("x", encoding="utf-8")   # another environment
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1, out)
        (self.r / ".pls/test-users/dev-soumu2.key").write_text("x", encoding="utf-8")     # a key file alone
        c = self.conns()
        c["dev"]["keys"]["kanri"] = "file:test-users/dev-kanri.key"                         # a reference alone
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1, out)
        self.assertIn("role 'keiri' is not a Group role in design/roles.json any more (dev-keiri.password)", out)
        self.assertIn("role 'soumu2' is not a Group role in design/roles.json any more (dev-soumu2.key)", out)
        self.assertIn("role 'kanri' is not a Group role in design/roles.json any more (keys.kanri)", out)
        self.assertNotIn("devx-keiri", out)
        self.assertTrue(orphan.exists())
        self.assertEqual(self.conns()["dev"]["keys"]["kanri"], "file:test-users/dev-kanri.key")
        self.assertFalse(self.pw.exists() or self.key.exists())          # the role still designed is removed

    def test_a_refused_delete_keeps_the_files_and_the_reference(self):
        self.fake.refuse_user_delete = True
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1)
        self.assertIn("answered HTTP 403", out)
        self.assertTrue(self.pw.exists() and self.key.exists())
        self.assertIn("somu", self.conns()["dev"]["keys"])

    def test_a_user_still_found_after_the_delete_keeps_the_files(self):
        self.fake.keep_deleted_user = True
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 1)
        self.assertIn("still found after the delete", out)
        self.assertTrue(self.pw.exists() and self.key.exists())

    def test_another_key_under_the_role_name_is_left_alone(self):
        c = self.conns()
        c["dev"]["keys"]["somu"] = "env:SOMEONE_ELSES_KEY"            # set by a person: not the test user's
        (self.r / ".pls/connections.json").write_text(json.dumps(c), encoding="utf-8")
        rc, out = self.remove("--yes")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.conns()["dev"]["keys"]["somu"], "env:SOMEONE_ELSES_KEY")
        self.assertFalse(self.pw.exists() or self.key.exists())

    def test_a_role_name_that_cannot_be_a_test_user_refuses_before_any_write(self):
        roles = json.loads((self.r / "design/roles.json").read_text(encoding="utf-8"))
        roles["roles"]["Bad-Role"] = {"principal": "Group", "group_name": "x"}
        (self.r / "design/roles.json").write_text(json.dumps(roles, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "test-users --remove: role 'Bad-Role'"):
            self.remove("--yes")
        self.assertEqual(self.deletes(), [])

    def test_two_users_with_the_test_login_refuse_before_any_write(self):
        self.fake.users[99999] = {"UserId": 99999, "LoginId": LOGIN, "password": None}
        with self.assertRaisesRegex(pls.Fail, f"2 users have the LoginId {LOGIN}"):
            self.remove("--yes")
        self.assertEqual(self.deletes(), [])

    def test_a_lookup_that_fails_after_the_delete_stops_and_keeps_the_files(self):
        from unittest import mock
        import pls_test_users as TU
        real, calls = TU.users_with_login, []

        def lookup(client, login):
            calls.append(login)
            if len(calls) > 1:                                          # the check after the delete
                raise TU.TestUsersError("looking up user answered HTTP 500 — nothing written")
            return real(client, login)
        with mock.patch.object(TU, "users_with_login", side_effect=lookup):
            with self.assertRaisesRegex(pls.Fail, "run it again: it looks every user up first"):
                self.remove("--yes")
        self.assertTrue(self.pw.exists() and self.key.exists())
        ev = [json.loads(x) for f in sorted((self.r / "ops/log").glob("*.jsonl"))
              for x in f.read_text(encoding="utf-8").splitlines() if '"test-users"' in x][-1]
        self.assertEqual(ev["metrics"], {"test_users_delete_answered": [self.uid]})   # the delete the server took

    def test_files_left_after_the_user_is_gone_are_removed_without_a_request_that_writes(self):
        del self.fake.users[self.uid]                                   # deleted by a person in Pleasanter
        n = len(self.fake.calls)
        rc, out = self.remove("--yes")
        self.assertEqual((rc, self.deletes(n)), (0, []), out)
        self.assertFalse(self.pw.exists() or self.key.exists())


if __name__ == "__main__":
    unittest.main()
