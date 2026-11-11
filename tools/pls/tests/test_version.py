"""Pleasanter version label (ADR-0009, part 1):  python -m unittest discover -s tools/pls/tests -v"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pls  # noqa: E402
import pls_version as PV  # noqa: E402
import test_http as TH  # noqa: E402

LOGIN = '<link href="/assets/css/style.min.css?v=201520" rel="stylesheet" />'
KB_INDEX = Path(__file__).resolve().parents[3] / "skills" / "pls-kb-pleasanter" / "references" / "probes" / "index.json"


def named_entries(line: str) -> set[str]:
    """The entry ids a `knowledge base: … (D33, D34) …` line names."""
    import re
    m = re.search(r"\(((?:D\w+)(?:, D\w+)*)\)", line)
    return set(m.group(1).split(", ")) if m else set()


def pending_on(app: str) -> list[str]:
    """Entries of the real KB not verified on `app` — e.g. a source-derived entry whose probe has not run (ADR-0023).
    Read from index.json directly, not through PV.kb_unverified (the function under test): an entry is verified on
    `app` when one of its `verified_on` labels is `app` or a prefix of it at a dot ("1.5.2" covers "1.5.2.0")."""
    entries = json.loads(KB_INDEX.read_text(encoding="utf-8-sig"))["entries"]
    return [k for k, e in entries.items()
            if not any(app == v or app.startswith(v + ".") for v in (e or {}).get("verified_on") or [])]


class PureTest(unittest.TestCase):
    def test_build_token_from_the_login_page(self):
        self.assertEqual(PV.build_token(LOGIN), "201520")
        self.assertIsNone(PV.build_token("<html>no stylesheet</html>"))

    def test_first_check_without_app_is_unknown(self):
        new, msgs = PV.update_record(None, "201520", 1.017, None, "2026-11-05")
        self.assertEqual(new, {"app": "unknown", "build": "201520", "schema": 1.017, "checked": "2026-11-05"})
        self.assertIn("/versions", msgs[-1])

    def test_app_label_kept_while_build_unchanged_and_reset_when_it_changes(self):
        old = {"app": "1.5.2.0", "build": "201520", "schema": 1.017, "checked": "2026-11-01"}
        same, msgs = PV.update_record(old, "201520", 1.017, None, "2026-11-05")
        self.assertEqual(same["app"], "1.5.2.0")
        self.assertEqual(msgs, [])
        moved, msgs = PV.update_record(old, "201600", 1.018, None, "2026-11-05")
        self.assertEqual(moved["app"], "unknown")
        self.assertTrue(any("build changed 201520 → 201600" in m for m in msgs))
        self.assertTrue(any("schema changed 1.017 → 1.018" in m for m in msgs))
        recorded, _ = PV.update_record(moved, "201600", 1.018, "1.5.3.0", "2026-11-05")
        self.assertEqual(recorded["app"], "1.5.3.0")

    def test_missing_build_token_never_keeps_the_label(self):
        old = {"app": "1.5.2.0", "build": "201520", "schema": 1.017}
        new, msgs = PV.update_record(old, None, 1.017, None, "d")
        self.assertEqual((new["app"], new["build"]), ("unknown", None))     # old build is not carried over as if confirmed
        self.assertTrue(any("build token not found" in m for m in msgs))

    def test_schema_change_alone_resets_the_label(self):
        old = {"app": "1.5.2.0", "build": "201520", "schema": 1.017}
        self.assertEqual(PV.update_record(old, "201520", 1.018, None, "d")[0]["app"], "unknown")

    def test_every_page_failure_becomes_page_error(self):
        import http.client

        def broken(req, timeout):
            raise http.client.IncompleteRead(b"")
        with self.assertRaises(PV.PageError):
            PV.fetch_login_page("http://x", opener=broken)
        with self.assertRaises(PV.PageError):
            PV.fetch_login_page("not a url")

    def test_compare_for_g4(self):
        dev = {"app": "1.5.2.0", "build": "201520", "schema": 1.017}
        self.assertEqual(PV.compare(dict(dev), dev, "stg", "dev"), [])
        diffs = PV.compare({"app": "1.5.1.0", "build": "201510", "schema": 1.017}, dev, "stg", "dev")
        self.assertEqual(len(diffs), 2)
        self.assertTrue(diffs[0].startswith("application: stg 1.5.1.0 ≠ dev 1.5.2.0"))
        self.assertIn("not known for stg", PV.compare({"app": "unknown", "build": "201520", "schema": 1.017}, dev, "stg", "dev")[0])
        self.assertIn("not recorded", PV.compare(None, dev, "stg", "dev")[0])

    def test_a_kb_version_label_covers_the_same_numbers_only(self):
        self.assertTrue(PV.covers("1.5.2", "1.5.2"))
        self.assertTrue(PV.covers("1.5.2", "1.5.2.0"))
        for app in ("1.5.20", "1.5.3.0", "1.6.0.0", "1.5", "11.5.2"):
            self.assertFalse(PV.covers("1.5.2", app), app)

    def test_kb_entries_not_verified_on_a_version_are_named(self):
        index = {"entries": {"D3": {"verified_on": ["1.5.2"]}, "D8": {"verified_on": ["1.5.2", "1.6.0"]}, "D9": {"verified_on": []},
                             "D10": {}}}
        self.assertEqual(PV.kb_unverified(index, "1.5.2.0"), ["D9", "D10"])
        self.assertEqual(PV.kb_unverified(index, "1.6.0.0"), ["D3", "D9", "D10"])
        self.assertIsNone(PV.kb_unverified(index, "unknown"))            # nothing can be said, and compare() says so
        self.assertIsNone(PV.kb_unverified(index, None))
        kb, msgs = PV.kb_lines(index, {"dev": "1.6.0.0", "stg": "unknown"})
        self.assertEqual(kb, {"dev": ["D3", "D9", "D10"]})
        self.assertEqual(len(msgs), 1)
        self.assertIn("3 entries not verified on dev 1.6.0.0 (D3, D9, D10)", msgs[0])
        with self.assertRaises(ValueError):
            PV.kb_unverified(["not an index"], "1.5.2")


class CliTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def run_version(self, *extra, page=LOGIN):
        orig = PV.fetch_login_page
        PV.fetch_login_page = lambda url, **kw: page
        try:
            return pls.main(["version", "--env", "dev", *extra])
        finally:
            PV.fetch_login_page = orig

    def recorded(self):
        return json.loads((self.r / "environments.json").read_text(encoding="utf-8"))["envs"]["dev"].get("pleasanter")

    def test_version_records_build_and_schema_then_the_app_label(self):
        self.fake.sites[TH.EQ]["SiteSettings"]["Version"] = 1.017
        self.assertEqual(self.run_version(), 1)                             # app unknown → the person must record it
        self.assertEqual({k: v for k, v in self.recorded().items() if k != "checked"},
                         {"app": "unknown", "build": "201520", "schema": 1.017})
        self.assertEqual(self.run_version("--app", "1.5.2.0"), 0)
        self.assertEqual(self.recorded()["app"], "1.5.2.0")
        self.assertEqual(self.run_version(), 0)                             # same build: label kept
        self.assertEqual(self.run_version(page=LOGIN.replace("201520", "201600")), 1)
        self.assertEqual(self.recorded()["app"], "unknown")
        # no token on the page: even a label given by the person is not confirmed → exit 1
        self.assertEqual(self.run_version("--app", "1.6.0.0", page="<html>login</html>"), 1)
        self.assertIsNone(self.recorded()["build"])

    def test_unknown_env_is_a_clear_error(self):
        # Fail is printed as "pls: …" with exit 2 by the CLI entry point (no traceback)
        with self.assertRaises(pls.Fail):
            pls.main(["version", "--env", "nope"])

    def test_version_check_in_release_plans(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["pleasanter"] = {"app": "1.5.2.0", "build": "201520", "schema": 1.017}
        envs["envs"]["prod"]["pleasanter"] = {"app": "1.5.1.0", "build": "201510", "schema": 1.017}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        pending = pending_on("1.5.2.0")
        diffs = pls.version_check(self.r, "dev")["differences"]
        self.assertEqual([d for d in diffs if not d.startswith("knowledge base:")], [])
        kb = [d for d in diffs if d.startswith("knowledge base:")]
        self.assertEqual(len(kb), 1 if pending else 0)                    # only entries not verified on 1.5.2
        for d in kb:
            self.assertEqual(named_entries(d), set(pending))
        envs["envs"]["dev"]["pleasanter"]["app"] = "unknown"
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        self.assertIn("not known for dev", pls.version_check(self.r, "dev")["differences"][0])
        envs["envs"]["dev"]["pleasanter"]["app"] = "1.5.2.0"
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        diffs = pls.version_check(self.r, "prod")["differences"]
        self.assertTrue(any(d.startswith("application: prod 1.5.1.0 ≠ dev 1.5.2.0") for d in diffs))

    def test_an_upgraded_dev_with_a_recorded_label_is_not_shown_as_tested(self):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["pleasanter"] = {"app": "1.6.0.0", "build": "201600", "schema": 1.018}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        check = pls.version_check(self.r, "dev")
        self.assertTrue(check["kb_unverified"]["dev"])                    # every entry is verified on 1.5.2 only
        line = [d for d in check["differences"] if d.startswith("knowledge base:")]
        self.assertEqual(len(line), 1)
        self.assertIn("not verified on dev 1.6.0.0", line[0])
        self.assertIn("D4", line[0])

    def test_pls_version_names_the_unverified_kb_entries(self):
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.run_version("--app", "1.6.0.0")
        self.assertIn("knowledge base:", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.run_version("--app", "1.5.2.0")
        pending = pending_on("1.5.2.0")
        if pending:                                                         # a probe not run yet is named, nothing else
            line = [x for x in out.getvalue().splitlines() if "knowledge base:" in x]
            self.assertEqual(len(line), 1)
            self.assertEqual(named_entries(line[0]), set(pending))
        else:
            self.assertNotIn("knowledge base:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
