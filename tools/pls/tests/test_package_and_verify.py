"""A release package for the customer's operator (ADR-0003; review criteria J1/J2): built only from a G4-approved
release, deterministic, without business data, and its stdlib verify.py refuses an altered byte, an added file, a
wrong target or release, and content the G4 record did not approve. Fake Pleasanter on 127.0.0.1 only."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import pls
import pls_gate as GT
import test_gate as TG
import test_http as TH

R = "R-20261108-01"


class PackageTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown
    plan = TH.HttpTest.plan
    stg = TG.StgWriteTest.stg

    def g4(self, quote="G4 approved for stg"):
        GT.record(self.r, "G4", "approved", "Nam", quote, [], [R], "2026-11-08")

    def package(self) -> Path:
        self.assertEqual(pls.main(["package", R]), 0)
        return self.r / "dist" / f"{R}-stg.zip"

    def unzip(self, z: Path) -> Path:
        d = Path(tempfile.mkdtemp(dir=self.r))
        with zipfile.ZipFile(z) as f:
            f.extractall(d)
        return d

    def verify(self, d: Path, env="stg", release=R) -> tuple[int, str]:
        p = subprocess.run([sys.executable, str(d / "verify.py"), "--env", env, "--release", release],
                           capture_output=True, text=True, encoding="utf-8", cwd=d,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        return p.returncode, p.stdout + p.stderr

    def test_only_a_release_approved_for_this_content_is_packaged(self):
        self.stg()
        with self.assertRaisesRegex(pls.Fail, "G4"):
            pls.main(["package", R])
        self.g4()
        p = self.r / "releases" / R / "payload-loans.json"
        p.write_text(p.read_text(encoding="utf-8").replace("new loans", "new loanz"), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, "changed since G4"):
            pls.main(["package", R])
        self.assertFalse((self.r / "dist").exists())

    def test_the_package_verifies_and_is_deterministic(self):
        self.stg()
        self.g4()
        z = self.package()
        first = hashlib.sha256(z.read_bytes()).hexdigest()
        self.assertEqual(hashlib.sha256(self.package().read_bytes()).hexdigest(), first)
        rec = json.loads((self.r / "releases" / R / "package-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["zip_sha256"], first)
        names = zipfile.ZipFile(z).namelist()
        for want in ("manifest.json", "verify.py", "pls_release_digest.py", "g4.json", "CHECKLIST.md",
                     f"releases/{R}/plan.json", f"releases/{R}/payload-loans.json", f"releases/{R}/rollback-loans.json"):
            self.assertIn(want, names)
        code, out = self.verify(self.unzip(z))
        self.assertEqual(code, 0, out)
        self.assertIn("VERIFIED", out)
        self.assertIn(rec["digest"]["sha256"], out)

    def test_verify_refuses_every_altered_package(self):
        self.stg()
        self.g4()
        z = self.package()

        def altered(change):
            d = self.unzip(z)
            change(d)
            return self.verify(d)

        def payload_byte(d):
            p = d / "releases" / R / "payload-loans.json"
            p.write_bytes(p.read_bytes().replace(b"new loans", b"new loanz"))

        def payload_and_manifest(d):                     # the manifest is re-hashed too: G4 still does not cover it
            payload_byte(d)
            m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            m["files"][f"releases/{R}/payload-loans.json"] = hashlib.sha256(
                (d / "releases" / R / "payload-loans.json").read_bytes()).hexdigest()
            (d / "manifest.json").write_text(json.dumps(m), encoding="utf-8")

        def extra_file(d):
            (d / "releases" / R / "payload-extra.json").write_text("{}", encoding="utf-8")

        def no_rollback(d):
            (d / "releases" / R / "rollback-loans.json").unlink()

        def other_approval(d):
            g = json.loads((d / "g4.json").read_text(encoding="utf-8"))
            g["decision"] = "rejected"
            (d / "g4.json").write_text(json.dumps(g), encoding="utf-8")

        for label, change, why in (
                ("payload byte", payload_byte, "changed since the package was built"),
                ("payload and manifest", payload_and_manifest, "G4 approval does not cover this content"),
                ("extra file", extra_file, "not part of the package"),
                ("no rollback", no_rollback, "rollback-loans.json: missing"),
                ("G4 rejected", other_approval, "not a G4 approval of this release")):
            with self.subTest(label):
                code, out = altered(change)
                self.assertEqual(code, 1, out)
                self.assertIn("NOT VERIFIED", out)
                self.assertIn(why, out)
        d = self.unzip(z)
        self.assertIn("targets 'stg', not 'prod'", self.verify(d, env="prod")[1])                  # wrong target
        self.assertIn("not 'R-20261108-02'", self.verify(d, release="R-20261108-02")[1])           # wrong release

    def test_migration_backups_are_never_shipped_and_not_part_of_the_approval(self):
        self.stg()
        mig = self.r / "migrations" / "m1"
        (mig / "backup").mkdir(parents=True)
        (mig / "backup" / "records.json").write_text('{"records": [{"ClassA": "business data"}]}', encoding="utf-8")
        (mig / "migration.json").write_text(json.dumps({"site": "equipment", "keys": ["ClassA"], "data": [{"ClassA": "x"}],
                                                        "rollback": {"data": [{"ClassA": "x"}]}}), encoding="utf-8")
        (mig / "dry-run.md").write_text("ok\n", encoding="utf-8")
        p = self.r / "releases" / R / "plan.json"
        p.write_text(json.dumps(dict(json.loads(p.read_text(encoding="utf-8")), migration=["migrations/m1"])), encoding="utf-8")
        self.g4()
        (mig / "backup" / "records.json").write_text('{"records": []}', encoding="utf-8")   # a new backup on the target
        names = zipfile.ZipFile(self.package()).namelist()                                 # G4 still holds
        self.assertIn("migrations/m1/migration.json", names)
        self.assertFalse([n for n in names if "backup" in n])
        self.assertEqual(self.verify(self.unzip(self.r / "dist" / f"{R}-stg.zip"))[0], 0)


if __name__ == "__main__":
    unittest.main()
