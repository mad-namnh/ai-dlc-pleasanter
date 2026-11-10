"""L-SEC-01 is a refusal, not only a lint finding, wherever pls writes configuration into the repository (I7,
ADR-0005): unpack and harvest (config/) and release-plan (payload and rollback in releases/) stop before writing.
Fake Pleasanter on 127.0.0.1 only."""
import json
import subprocess
import unittest

import pls
import test_http as TH
import test_pls as TP
import test_sandbox_merge as SM

KEY = "sk-ant-abcdefghijklmnop"
SECRET_SCRIPT = {"Id": 9, "Name": "mail", "Body": f"var k = '{KEY}';"}


class UnpackAndReleasePlanTest(unittest.TestCase):
    setUp = TP.PlsTest.setUp
    tearDown = TP.PlsTest.tearDown
    unpack_dev = TP.PlsTest.unpack_dev
    _two_sites = TP.PlsTest._two_sites

    def test_unpack_of_an_export_with_a_secret_writes_nothing(self):
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(TP.export(101, 102, "http://dev.internal", scripts=[SECRET_SCRIPT])), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "anthropic-key.*nothing written"):
            pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"])
        self.assertFalse((self.r / "config/a").exists())

    def test_release_plan_refuses_a_secret_in_the_live_site_or_in_config(self):
        sa, sb = self._two_sites()
        live = json.loads(sa.read_text(encoding="utf-8"))
        live["Response"]["Data"]["SiteSettings"]["ServerScripts"].append(SECRET_SCRIPT)   # the rollback would carry it
        sa.write_text(json.dumps(live), encoding="utf-8")
        rp = ["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]
        self.assertEqual(pls.main(rp), 1)
        self.assertEqual(self.written(), [])
        live["Response"]["Data"]["SiteSettings"]["ServerScripts"].pop()                 # live is clean again
        sa.write_text(json.dumps(live), encoding="utf-8")
        f = next((self.r / "config/a").rglob("*.js"))                                     # a hand edit of config/
        f.write_text(f.read_text(encoding="utf-8") + f"\nvar k = '{KEY}';\n", encoding="utf-8")
        self.assertEqual(pls.main(rp), 1)
        self.assertEqual(self.written(), [])
        f.write_text(f.read_text(encoding="utf-8").replace(f"\nvar k = '{KEY}';\n", ""), encoding="utf-8")
        self.assertEqual(pls.main(rp), 0)                                                 # control: clean plans
        self.assertTrue((self.r / "releases/R1/plan.json").exists())

    def written(self):
        d = self.r / "releases/R1"
        return sorted(p.name for p in d.iterdir()) if d.exists() else []


class HarvestTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    prepare = SM.SandboxTest.prepare

    def test_harvest_of_a_site_with_a_secret_leaves_config_unchanged(self):
        self.prepare()

        def git(*a):
            return subprocess.run(["git", *a], cwd=self.r, capture_output=True, text=True, encoding="utf-8")
        git("init", "-q")
        git("config", "user.email", "t@example.com")
        git("config", "user.name", "t")
        git("add", "config")
        git("commit", "-qm", "base")
        self.fake.sites[TH.LO]["SiteSettings"]["ServerScripts"] = [dict(SECRET_SCRIPT, Body=f"var password = \"{KEY}\";")]
        with self.assertRaisesRegex(pls.Fail, "secret-like.*nothing written"):
            pls.main(["harvest", "--env", "dev", "--site", "loans"])
        self.assertEqual(git("status", "--porcelain", "--", "config").stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
