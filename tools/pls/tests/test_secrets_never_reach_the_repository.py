"""L-SEC-01 is a refusal, not only a lint finding, wherever pls writes configuration into the repository or a payload
file (I7, ADR-0005): unpack and harvest (config/), pack, single-site plan and release-plan (payload and rollback in
releases/) stop before writing. Besides the patterns, credential fields of notifications and reminders are named
whatever their text looks like (pls_secret_fields). Fake Pleasanter on 127.0.0.1 only."""
import contextlib
import io
import json
import subprocess
import unittest

import pls
import pls_secret_fields as SF
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

    def test_harvest_checks_the_raw_export_before_values_are_mapped_back(self):
        self.prepare()
        for args in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"],
                     ["add", "config"], ["commit", "-qm", "base"]):
            subprocess.run(["git", *args], cwd=self.r, capture_output=True)
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        ev["envs"]["dev"].setdefault("values", {})["hdrs"] = '{"Authorization": "Basic zz9"}'
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        before = (self.r / "config/loans/site.json").read_text(encoding="utf-8")
        self.fake.sites[TH.LO]["SiteSettings"]["Notifications"] = [
            {"Id": 1, "Type": 9, "Address": "https://api.example/h", "Headers": '{"Authorization": "Basic zz9"}'}]
        with self.assertRaises(pls.Fail) as cm:                 # mapped, the value would read ${env:hdrs}
            pls.main(["harvest", "--env", "dev", "--site", "loans"])
        self.assertIn("credential-header", str(cm.exception))
        self.assertNotIn("zz9", str(cm.exception))
        self.assertEqual((self.r / "config/loans/site.json").read_text(encoding="utf-8"), before)


class LiveContentWritersTest(unittest.TestCase):
    """env-compare reports and the applied-differs baseline quote live content: L-SEC-01 before they are written."""
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def test_env_compare_writes_no_report_with_a_secret(self):
        import test_compare as TC
        rows = []
        for env, site_id in (("dev", 797), ("prod", 9001)):
            data = TC.site(site_id, 500)
            if env == "prod":
                data["SiteSettings"]["Notifications"] = [{"Id": 1, "Type": 3, "Token": "zz9tok", "Disabled": True}]
            f = self.r / f"{env}-x.json"
            f.write_text(json.dumps({"Response": {"Data": data}}), encoding="utf-8")
            rows.append(f"{env}={f.name}")
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        ev["envs"]["dev"].setdefault("sites", {})["anken"] = {"id": 797}
        ev["envs"].setdefault("prod", {"role": "prod", "sites": {}})["sites"]["anken"] = {"id": 9001}
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        with self.assertRaises(pls.Fail) as cm:
            pls.main(["env-compare", "--site", "anken", "--source", rows[0], "--source", rows[1]])
        self.assertIn("notification-token", str(cm.exception))
        self.assertNotIn("zz9tok", str(cm.exception))
        self.assertFalse((self.r / "ops/env-compare").exists() and list((self.r / "ops/env-compare").iterdir()))


class DiffOutputTest(unittest.TestCase):
    """diff, drift, plan and mark-applied print md_diff tables that a person copies into ops/ records: a secret-like
    value is replaced by the names of what it holds (L-SEC-01)."""

    def test_a_secret_like_value_is_withheld_and_other_values_are_shown(self):
        text = pls.md_diff([
            {"path": "settings.Notifications[1].Token", "kind": "changed", "before": "zz9a", "after": "zz9b"},
            {"path": "settings.Notifications", "kind": "added", "before": None,
             "after": [{"Id": 1, "Type": 2, "Address": "https://hooks.example/T0/B0/zz9c"}]},
            {"path": "settings.ServerScripts[1].Body", "kind": "changed", "before": "var x;", "after": f"var k = '{KEY}';"},
            {"path": "settings.GridPageSize", "kind": "changed", "before": 20, "after": 50}], {}, "t")
        self.assertNotIn("zz9", text)
        self.assertNotIn(KEY, text)
        self.assertIn("(withheld: webhook-url)", text)
        self.assertIn("| 20 | 50 |", text)
        mail = pls.md_diff([                                     # the G4 summary needs who gets mail
            {"path": "settings.Notifications[1].Address", "kind": "changed", "before": "[${principal:mgr}]",
             "after": "${env:mail_to}"},
            {"path": "settings.Notifications[2].Address", "kind": "changed", "before": "",
             "after": "https://hooks.example/T0/B0/zz9d"}], {}, "m")
        self.assertIn("[${principal:mgr}] | ${env:mail_to}", mail)
        self.assertNotIn("zz9d", mail)


class AdoptTest(unittest.TestCase):
    setUp = TH.HttpTest.setUp
    tearDown = TH.HttpTest.tearDown

    def test_adopt_refuses_a_secret_in_the_site_description(self):
        import test_adopt as TA
        TA.CliTest.add_old_site(self)
        self.fake.sites[TA.OLD]["Body"] = f"api_key = '{KEY}'"
        with self.assertRaisesRegex(pls.Fail, "secret-like"):
            pls.main(["adopt", "--env", "dev", "--site", str(TA.OLD), "--name", "anken"])
        self.assertFalse((self.r / "config/anken").exists())


class CredentialFieldsTest(unittest.TestCase):
    """Fields that hold a credential whatever it looks like (Pleasanter_1.5.2.0 Notification / Reminder, source-derived):
    the pattern checks alone let a short token or a webhook URL through."""

    def test_each_credential_field_is_named_and_mail_is_not(self):
        cases = [
            ({"Notifications": [{"Id": 1, "Type": 3, "Address": "123", "Token": "abc1"}]}, ["notification-token"]),
            ({"Notifications": [{"Id": 1, "Type": 2, "Address": "https://hooks.example/T0/B0/x"}]}, ["webhook-url"]),
            ({"Notifications": [{"Id": 1, "Type": "6", "Address": "https://teams.example/w"}]}, ["webhook-url"]),
            ({"Notifications": [{"Id": 1, "Type": 9, "Address": "https://api.example/h",
                                 "Headers": '{"Authorization": "Basic x"}'}]}, ["credential-header"]),
            ({"Notifications": [{"Id": 1, "Type": 9, "Address": "https://api.example/h?a=1&sig=x"}]}, ["credential-in-url"]),
            ({"Reminders": [{"Id": 1, "ReminderType": 9, "To": "https://works.example/b"}]}, ["webhook-url"]),
            ({"Reminders": [{"Id": 1, "ReminderType": 3, "To": "55", "Token": "t"}]}, ["reminder-token"]),
            ({"Processes": [{"Id": 1, "Notifications": [{"Id": 1, "Type": 4, "Token": "x"}]}]}, ["notification-token"]),
            ({"Notifications": [{"Id": 1, "Type": 9, "Address": "https://api.example/h",
                                 "Headers": '{"Ocp-Apim-Subscription-Key": "x"}'}]}, ["credential-header"]),
            ({"Notifications": [{"Id": 1, "Type": 9, "Address": "https://api.example/h?client_secret=x"}]},
             ["credential-in-url"]),
            ({"Notifications": [{"Id": 1, "Type": 9, "Address": "https://hooks.slack.com/services/T0/B0/x"}]},
             ["credential-in-url"]),
            ({"Notifications": [{"Id": 1, "Type": float("inf"), "Token": ""}]}, []),          # no traceback
            # not credentials: mail addresses, an HttpClient URL without a credential, a plain header, empty fields
            ({"Notifications": [{"Id": 1, "Type": 1, "Address": "[Manager]", "Token": ""},
                                {"Id": 2, "Type": 9, "Address": "https://api.example/h?id=5",
                                 "Headers": '{"Content-Type": "application/json", "X-Source": "token-service"}'},
                                {"Id": 3, "Type": 9, "Address": "https://api.example/h?design=1"}],
              "Reminders": [{"Id": 1, "ReminderType": 1, "To": "[Owner]"}]}, []),
        ]
        for ss, want in cases:
            with self.subTest(ss=ss):
                self.assertEqual(SF.secret_fields(ss), want)
                self.assertEqual(SF.secret_fields(json.dumps({"SiteSettings": ss})), want)   # as JSON text, nested
                for n in want:
                    self.assertIn(n, pls.secrets_in({"settings": ss}))

    def test_unpack_refuses_a_webhook_url_and_names_no_value(self):
        exp = self.r / "dev.json"
        data = TP.export(101, 102, "http://dev.internal")
        data["Response"]["Data"]["SiteSettings"]["Notifications"] = [
            {"Id": 1, "Type": 2, "Address": "https://hooks.example/T0/B0/zz9", "Disabled": True}]
        exp.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(pls.Fail) as cm:
            pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"])
        self.assertIn("webhook-url", str(cm.exception))
        self.assertNotIn("zz9", str(cm.exception))
        self.assertFalse((self.r / "config/a").exists())

    def test_lint_reports_a_token_written_into_config(self):
        self.unpack_dev()
        f = self.r / "config/a/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site.setdefault("Reminders", []).append(
            {"Id": 1, "ReminderType": 3, "To": "55", "Token": "short"})
        f.write_text(json.dumps(site), encoding="utf-8")
        issues = pls.lint(self.r)
        self.assertTrue(any(i["rule"] == "L-SEC-01" and "reminder-token" in i["msg"] for i in issues), issues)

    def test_pack_and_lint_refuse_a_credential_kept_as_an_environment_value(self):
        self.unpack_dev()
        f = self.r / "config/a/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site["Notifications"] = [{"Id": 1, "Type": 9, "Address": "https://api.example/h", "Headers": "${env:hdrs}",
                                  "Disabled": True}]
        f.write_text(json.dumps(site), encoding="utf-8")
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        for ec in ev["envs"].values():
            ec.setdefault("values", {})["hdrs"] = '{"Authorization": "Basic zz9"}'
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        out = self.r / "x.json"
        with self.assertRaises(pls.Fail) as cm:
            pls.main(["pack", "--env", "dev", "--site", "a", "--out", str(out)])
        self.assertIn("credential-header", str(cm.exception))
        self.assertIn("ADR-0005", str(cm.exception))
        self.assertNotIn("zz9", str(cm.exception))
        self.assertFalse(out.exists())
        issues = pls.lint(self.r)
        self.assertTrue(any(i["rule"] == "L-SEC-01" and "credential-header" in i["msg"] and "env 'dev'" in i["msg"]
                            for i in issues), issues)

    def test_single_site_plan_refuses_a_webhook_on_the_live_site(self):
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        live = json.loads(self._stg_live().read_text(encoding="utf-8"))
        live["Response"]["Data"]["SiteSettings"]["Notifications"] = [
            {"Id": 1, "Type": 2, "Address": "https://hooks.example/T0/B0/zz9", "Disabled": True}]
        lp = self.r / "stg-live-webhook.json"
        lp.write_text(json.dumps(live), encoding="utf-8")
        args = ["plan", str(lp), "--env", "stg", "--site", "a", "--release", "R1"]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(args), 1)
        self.assertIn("webhook-url", out.getvalue())
        self.assertNotIn("zz9", out.getvalue())
        self.assertFalse((self.r / "releases/R1").exists())
        self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 0)

    def test_single_site_plan_refuses_a_token_in_config(self):
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        f = self.r / "config/a/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site["Reminders"] = [{"Id": 1, "ReminderType": 3, "To": "55", "Token": "zz9", "Disabled": True}]
        f.write_text(json.dumps(site), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 1)
        self.assertIn("payload (config/): ", out.getvalue())
        self.assertIn("reminder-token", out.getvalue())
        self.assertNotIn("zz9", out.getvalue())
        self.assertFalse((self.r / "releases/R1").exists())

    def test_lint_runs_when_an_environment_lacks_a_site_or_a_principal_has_no_id(self):
        self.unpack_dev()
        f = self.r / "config/a/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site["Processes"] = [{"Id": 1, "Name": "p", "View": {}, "Groups": ["${principal:mgr}"]}]
        f.write_text(json.dumps(site), encoding="utf-8")
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        ev["envs"]["stg"]["sites"].pop("a")                      # adopted on dev only
        ev["envs"]["dev"].setdefault("principals", {})["mgr"] = "Group,<id>"   # setup placeholder
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        issues = pls.lint(self.r)                                # no exception: every rule still runs
        self.assertTrue(any(i["rule"] == "L-SEC-01" and "not checked for env 'dev'" in i["msg"] for i in issues), issues)
        self.assertFalse(any("env 'stg'" in i["msg"] for i in issues if i["rule"] == "L-SEC-01"), issues)

    def test_unpack_refuses_a_credential_equal_to_an_environment_value(self):
        ev = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        ev["envs"]["dev"].setdefault("values", {})["hdrs"] = '{"Authorization": "Basic zz9"}'
        (self.r / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        data = TP.export(101, 102, "http://dev.internal")
        data["Response"]["Data"]["SiteSettings"]["Notifications"] = [
            {"Id": 1, "Type": 9, "Address": "https://api.example/h", "Headers": '{"Authorization": "Basic zz9"}'}]
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(pls.Fail) as cm:
            pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"])
        self.assertIn("credential-header", str(cm.exception))
        self.assertNotIn("zz9", str(cm.exception))
        self.assertFalse((self.r / "config/a").exists())

    def test_pack_refuses_an_unmapped_principal_in_an_access_list(self):
        self.unpack_dev()
        f = self.r / "config/a/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))
        site["Processes"] = [{"Id": 1, "Name": "p", "View": {}, "Groups": ["${principal:nobody}"]}]
        f.write_text(json.dumps(site), encoding="utf-8")
        with self.assertRaisesRegex(pls.Fail, r"unresolved reference \$\{principal:nobody\}"):
            pls.main(["pack", "--env", "dev", "--site", "a"])

    def test_numbers_and_enum_names_are_read_as_pleasanter_reads_them(self):
        self.assertEqual(SF.secret_fields({"Notifications": [{"Id": 1, "Type": "Slack", "Address": "x"},
                                                             {"Id": 2, "Type": 3, "Token": 123456789},
                                                             {"Id": 3, "Type": 9, "Address": "https://u:p@api.example/h"}],
                                           "Reminders": [{"Id": 1, "ReminderType": "LineWorks", "To": "x"}]}),
                         ["credential-in-url", "notification-token", "webhook-url"])

    setUp = TP.PlsTest.setUp
    tearDown = TP.PlsTest.tearDown
    unpack_dev = TP.PlsTest.unpack_dev
    _ledger = TP.PlsTest._ledger
    _stg_live = TP.PlsTest._stg_live


if __name__ == "__main__":
    unittest.main()
