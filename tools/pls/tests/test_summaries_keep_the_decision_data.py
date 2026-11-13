"""`--summary` forms keep what a decision needs (design review G5-b): `lint --summary` has every rule with the same
counts as the full list, and `release-plan --summary` folds the scope refusal into one line per site without losing
the refusal, the count or the exit code."""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402
import test_pls as TP  # noqa: E402


def captured(argv) -> tuple[int, list[str]]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = pls.main(argv)
    return code, out.getvalue().splitlines()


class LintSummaryTest(TP.PlsTest):
    ISSUES = [{"rule": "L-REF-01", "site": s, "msg": f"id in script {i}"} for i, s in enumerate("aaabbbbcd")] + \
             [{"rule": "L-SEC-01", "site": "a", "msg": "secret-like value"}]

    def test_summary_has_every_rule_with_the_full_counts(self):
        with mock.patch.object(pls, "lint", return_value=list(self.ISSUES)):
            code_full, full = captured(["lint"])
            code_short, short = captured(["lint", "--summary"])
        self.assertEqual((code_full, code_short), (1, 1))
        self.assertEqual(full[-1], "10 issue(s)")
        self.assertEqual(short[-1], "10 issue(s)")
        rows = {x.split()[0]: x for x in short[:-1]}
        self.assertEqual(sorted(rows), ["L-REF-01", "L-SEC-01"])
        self.assertEqual(rows["L-REF-01"].split()[1], "9")
        self.assertIn("b 4", rows["L-REF-01"])                                       # the site with most issues first
        self.assertEqual(rows["L-SEC-01"].split()[1], "1")


class ReleasePlanSummaryTest(TP.PlsTest):
    def plan(self, *extra):
        sa, sb = self._two_sites()
        unverified = {f"Unverified{i}": [{"Id": 1}] for i in range(7)}
        live = json.loads(sb.read_text(encoding="utf-8"))
        live["Response"]["Data"]["SiteSettings"].update(unverified)
        sb.write_text(json.dumps(live), encoding="utf-8")
        git_b = self.r / "config/b/site.json"
        site = json.loads(git_b.read_text(encoding="utf-8"))
        site.update(unverified)
        git_b.write_text(json.dumps(site), encoding="utf-8")
        return captured(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}", *extra])

    def test_scope_refusal_is_one_line_per_site_and_still_refuses(self):
        code_full, full = self.plan()
        self.assertEqual(code_full, 1)
        self.assertEqual(len([x for x in full if x.startswith("SCOPE b:")]), 7)
        import shutil
        shutil.rmtree(self.r / "releases", ignore_errors=True)
        code_short, short = self.plan("--summary")
        self.assertEqual(code_short, 1)
        scope = [x for x in short if x.startswith("SCOPE b:")]
        self.assertEqual(len(scope), 1)
        self.assertIn("7 component(s) without round-trip evidence: Unverified0", scope[0])
        self.assertIn("…", scope[0])
        self.assertIn("run again without --summary", scope[0])
        self.assertTrue(any(x.startswith("b: REFUSED") for x in short))                 # the refusal line is kept
        self.assertEqual(short[-1], "release plan REFUSED: no files written")
        self.assertFalse((self.r / "releases/R1").exists())


# the inherited tests of PlsTest run in test_pls already
for _cls in (LintSummaryTest, ReleasePlanSummaryTest):
    for _name in [n for n in dir(TP.PlsTest) if n.startswith("test_") and n not in _cls.__dict__]:
        setattr(_cls, _name, None)

if __name__ == "__main__":
    unittest.main()
