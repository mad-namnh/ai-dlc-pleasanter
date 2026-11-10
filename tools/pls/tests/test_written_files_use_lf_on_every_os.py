"""Files pls writes have LF line endings on every operating system, so a re-run on another OS does not rewrite
whole files in git; script bodies keep the line endings Pleasanter stores:
python -m unittest discover -s tools/pls/tests -v"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import pls  # noqa: E402
import pls_gate as GT  # noqa: E402
import test_http as TH  # noqa: E402

PROFILE = "# Project\n\n| Field | Value |\n|---|---|\n| Approvers | G1: Nam; G2: Nam; G3: Nam; G4: Nam |\n"


class LineEndings(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def lf_only(self, path):
        data = Path(path).read_bytes()
        self.assertGreater(data.count(b"\n"), 0, path)
        self.assertNotIn(b"\r", data, path)

    def test_json_and_reports_are_written_with_lf(self):
        body = "context.Log('a');\r\ncontext.Log('b');\r\n"                      # stored with CRLF by Pleasanter
        pls.wj(self.r / "lo.json", {"Response": {"Data": dict(self.fake.sites[TH.LO], Body="", SiteSettings={
            "ServerScripts": [{"Id": 1, "Name": "s", "Body": body}]})}})
        self.lf_only(self.r / "lo.json")
        self.assertEqual(pls.main(["unpack", "lo.json", "--env", "dev", "--site", "loans"]), 0)
        for f in (self.r / "config/loans").glob("*.json"):
            self.lf_only(f)
        script = next((self.r / "config/loans").rglob("*.js"))
        self.assertEqual(script.read_bytes(), body.encode("utf-8"))                # the body is byte for byte

    def test_gate_records_are_written_with_lf(self):
        (self.r / "CLAUDE.md").write_text(PROFILE, encoding="utf-8")
        self.lf_only(GT.record(self.r, "G1", "approved", "Nam", "ok", ["REQ-001"], [], "2026-11-10"))


class MinimumPython(unittest.TestCase):
    def test_the_documented_minimum_is_the_one_the_guard_checks(self):
        setup = (HERE.parents[3] / "docs/setup.md").read_text(encoding="utf-8")
        self.assertIn("Python 3.10+", setup)
        self.assertIn("sys.version_info < (3, 10)", (HERE.parents[1] / "pls.py").read_text(encoding="utf-8"))

    def test_no_backslash_inside_an_f_string_expression(self):
        """The construct that silently raised the minimum to 3.12 (PEP 701). The suite itself runs on 3.10 before a
        release; this catches the common case on any version."""
        import io
        import tokenize
        if sys.version_info < (3, 12):
            self.skipTest("an older Python refuses the construct at import time already")
        for f in sorted(HERE.parents[1].glob("pls*.py")):
            depth = 0
            for tok in tokenize.generate_tokens(io.StringIO(f.read_text(encoding="utf-8")).readline):
                if tok.type == tokenize.FSTRING_START:
                    depth += 1
                elif tok.type == tokenize.FSTRING_END:
                    depth -= 1
                elif "\\" in tok.string and ((depth and tok.type == tokenize.STRING)                 # "…" inside {…}
                                             or (depth > 1 and tok.type == tokenize.FSTRING_MIDDLE)):  # f"…" inside {…}
                    self.fail(f"{f.name}:{tok.start[0]}: backslash inside an f-string expression needs Python 3.12")


if __name__ == "__main__":
    unittest.main()
