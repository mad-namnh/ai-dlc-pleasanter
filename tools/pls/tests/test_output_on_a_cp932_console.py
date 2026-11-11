"""pls prints on a console whose encoding is cp932 (a Japanese Windows console) instead of failing.

Escaped defect TD-12: "—", "✓" and other characters that cp932 cannot encode made pls stop with UnicodeEncodeError
before it printed anything. pls now switches stdout and stderr to UTF-8 when it starts. Each test starts a child
Python whose console encoding is forced to cp932, as the console does.

    python -m unittest discover -s tools/pls/tests -v
"""
import os
import subprocess
import sys
import unittest
from pathlib import Path

PLS_DIR = Path(__file__).resolve().parents[1]
NOT_IN_CP932 = "— ✓ 한글"       # an em dash, a check mark and Hangul: none of them has a cp932 code


def on_a_cp932_console(args: list[str]) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING", "PYTHONLEGACYWINDOWSSTDIO")}
    env["PYTHONIOENCODING"] = "cp932"
    return subprocess.run([sys.executable, *args], capture_output=True, env=env, cwd=PLS_DIR, timeout=60)


class Cp932ConsoleTest(unittest.TestCase):
    def test_the_characters_of_this_test_are_not_in_cp932(self):
        for ch in ("—", "✓", "한"):
            with self.assertRaises(UnicodeEncodeError):
                ch.encode("cp932")
        plain = on_a_cp932_console(["-c", f"print({NOT_IN_CP932!r})"])           # without pls: the console fails
        self.assertNotEqual(plain.returncode, 0)
        self.assertIn(b"UnicodeEncodeError", plain.stderr)

    def test_pls_output_is_utf8_whatever_the_console_encoding_is(self):
        done = on_a_cp932_console(["-c", f"import sys, pls; print({NOT_IN_CP932!r}); print({NOT_IN_CP932!r}, file=sys.stderr)"])
        self.assertEqual(done.returncode, 0, done.stderr.decode("utf-8", "replace"))
        self.assertEqual(done.stdout.decode("utf-8").strip(), NOT_IN_CP932)
        self.assertEqual(done.stderr.decode("utf-8").strip(), NOT_IN_CP932)

    def test_a_pls_command_prints_its_help_and_a_refusal(self):
        done = on_a_cp932_console(["pls.py", "--help"])
        self.assertEqual(done.returncode, 0, done.stderr.decode("utf-8", "replace"))
        self.assertIn("release-plan", done.stdout.decode("utf-8"))                # decodes as UTF-8, whole
        done = on_a_cp932_console(["pls.py", "jobs-verified", "R-none", "--by", "x", "--quote", "x"])   # no project here
        self.assertEqual(done.returncode, 2, done.stderr.decode("utf-8", "replace"))
        self.assertIn("environments.json not found", (done.stdout + done.stderr).decode("utf-8"))
        self.assertNotIn(b"UnicodeEncodeError", done.stderr)


if __name__ == "__main__":
    unittest.main()
