"""A `file:` key reference is read only from the project's `.pls/` or the machine-profile folder
(ADR-0021 option B, ADR-0014 TB-11, TD-34): any other path — `..`, an absolute path elsewhere — is refused before the
file is read. Local files only; no server."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls_http as H  # noqa: E402


class KeyFileHomesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.pls_dir, self.profiles, self.elsewhere = base / "proj/.pls", base / "profiles", base / "elsewhere"
        for d in (self.pls_dir / "test-users", self.profiles, self.elsewhere):
            d.mkdir(parents=True)
        (self.pls_dir / "admin.key").write_text("K-IN-PLS\n", encoding="utf-8")
        (self.pls_dir / "test-users/dev-staff.key").write_text("K-TEST-USER\n", encoding="utf-8")
        (self.profiles / "dev.key").write_text("K-PROFILE\n", encoding="utf-8")
        (self.elsewhere / "stolen.key").write_text("K-ELSEWHERE\n", encoding="utf-8")
        env = mock.patch.dict(os.environ, {"PLS_PROFILE_DIR": str(self.profiles)})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(self.tmp.cleanup)

    def key(self, ref):
        return H.resolve_key({"_dir": str(self.pls_dir), "keys": {"k": ref}}, "k")

    def test_keys_in_the_two_homes_are_read(self):
        self.assertEqual(self.key("file:admin.key"), "K-IN-PLS")
        self.assertEqual(self.key("file:test-users/dev-staff.key"), "K-TEST-USER")      # pls test-users
        self.assertEqual(self.key(f"file:{(self.profiles / 'dev.key').as_posix()}"), "K-PROFILE")   # pls setup

    def test_any_other_path_is_refused_before_it_is_read(self):
        outside = [f"file:{(self.elsewhere / 'stolen.key').as_posix()}",           # absolute, elsewhere
                   "file:../../elsewhere/stolen.key",                               # relative, escapes .pls/
                   "file:test-users/../../../elsewhere/stolen.key",                 # escapes after a valid prefix
                   f"file:{(self.profiles / '..' / 'elsewhere' / 'stolen.key').as_posix()}"]   # escapes the profiles
        for ref in outside:
            with mock.patch.object(Path, "read_text", side_effect=AssertionError("read")):
                with self.assertRaisesRegex(H.TransportError, "points outside the project's .pls/", msg=ref):
                    self.key(ref)

    def test_a_connection_file_elsewhere_does_not_widen_where_keys_may_live(self):
        shared = self.elsewhere                                                   # PLS_CONNECTIONS=<elsewhere>/c.json
        (shared / "c.json").write_text('{"dev": {"url": "http://127.0.0.1:1", "keys": {"k": "file:stolen.key"}}}',
                                       encoding="utf-8")
        with mock.patch.dict(os.environ, {"PLS_CONNECTIONS": str(shared / "c.json")}):
            conn = H.load_connection(self.pls_dir.parent, "dev")
        with self.assertRaisesRegex(H.TransportError, "points outside the project's .pls/"):
            H.resolve_key(conn, "k")
        conn["keys"]["k"] = f"file:{(self.pls_dir / 'admin.key').as_posix()}"   # the project's own .pls/ still works
        self.assertEqual(H.resolve_key(conn, "k"), "K-IN-PLS")

    def test_a_malformed_reference_is_a_refusal_not_a_crash(self):
        for ref in ("file:", "file:.", "file:a\x00b"):
            with self.assertRaises(H.TransportError, msg=repr(ref)):
                self.key(ref)

    def test_an_unreadable_key_file_is_a_refusal(self):
        with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(H.TransportError, "cannot be read \\(PermissionError\\)"):
                self.key("file:admin.key")

    def test_a_missing_file_inside_a_home_is_still_reported_as_missing(self):
        with self.assertRaisesRegex(H.TransportError, "not found"):
            self.key("file:nope.key")

    def test_pls_and_pls_http_name_the_same_profile_folder(self):
        import pls
        self.assertEqual(pls.profile_dir(), H.profile_dir())


if __name__ == "__main__":
    unittest.main()
