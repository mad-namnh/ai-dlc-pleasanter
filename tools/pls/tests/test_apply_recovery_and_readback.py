"""Failed restores, timeouts after a write, and the read-back that records what a release really left behind.

A failure must never end in a success state: a restore is "rolled-back" only when the sites read back equal to
their rollback files, an unanswered write is "uncertain" (never restored or retried blindly), and `mark-applied`
records only what the exports show. Fake Pleasanter on 127.0.0.1 only (test_http.serve).
"""
import json
import time
import unittest
from pathlib import Path

import pls
import test_http as T
from test_http import EQ, FOLDER, LO


class SlowFake(T.Fake):
    """Writes like the fake server, then answers too late for the client timeout when the path contains `hang_on`."""
    hang_on = None

    def handle(self, path, body):
        res = super().handle(path, body)
        if self.hang_on and self.hang_on in path:
            time.sleep(1.6)
        return res


def with_body(fake):
    """getsite returns Body like Pleasanter does; the read-back compares it."""
    for s in fake.sites.values():
        s.setdefault("Body", "")
    return fake


class RecoveryTest(unittest.TestCase):
    tearDown = T.HttpTest.tearDown

    def setUp(self):
        T.HttpTest.setUp(self)
        with_body(self.fake)

    def plan(self, rel="R-1"):
        """test_http's two-site plan with per-site payload files, as release-plan writes it."""
        plan, d = T.HttpTest.plan(self, rel)
        for s in plan["sites"]:
            plan["per_site"][s].update(payload_file=f"payload-{s}.json", rollback_file=f"rollback-{s}.json")
        (d / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return plan, d

    def slow(self, hang_on):
        """Swap in a fake server that hangs after writing; the dev connection times out after 1 s."""
        self.srv.shutdown()
        self.srv.server_close()
        self.fake = with_body(SlowFake())
        self.fake.hang_on = hang_on
        self.srv = T.serve(self.fake)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        conns = json.loads((self.r / ".pls/connections.json").read_text(encoding="utf-8"))
        conns["dev"].update(url=self.url, timeout=1)
        (self.r / ".pls/connections.json").write_text(json.dumps(conns), encoding="utf-8")

    def status(self, d):
        return json.loads((d / "plan.json").read_text(encoding="utf-8"))["status"]

    def updates(self):
        return [p for p, _ in self.fake.calls if p.endswith("/updatesite")]

    def exports(self):
        """Exports of both sites as `pls export` writes them; returns --export arguments."""
        out = []
        for s, sid in (("equipment", EQ), ("loans", LO)):
            p = self.r / f"exp-{s}.json"
            p.write_text(json.dumps({"Response": {"Data": self.fake.sites[sid]}}), encoding="utf-8")
            out += ["--export", f"{s}={p}"]
        return out

    def test_failed_restore_is_recovery_required_blocks_reapply_and_never_becomes_applied(self):
        plan, d = self.plan()
        self.fake.fail_update_on = LO               # loans refuses its write and its restore
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "recovery-required")
        log = json.loads((d / "apply-log.json").read_text(encoding="utf-8"))
        self.assertEqual(log["status"], "recovery-required")
        self.assertEqual(log["failed_restores"], ["loans"])
        n = len(self.updates())
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)                      # not "planned" any more
        self.assertEqual(len(self.updates()), n)
        self.assertEqual(log, json.loads((d / "apply-log.json").read_text(encoding="utf-8")))   # evidence kept
        # read back: equipment holds its rollback state, loans was never written → nothing is live
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)
        self.assertEqual(self.status(d), "rolled-back")
        self.assertFalse(list(d.glob("live-*.json")))

    def test_restore_is_rolled_back_when_the_sites_read_back_equal(self):
        plan, d = self.plan()
        for s, sid in (("equipment", EQ), ("loans", LO)):                           # rollback = the state before
            live = self.fake.sites[sid]
            (d / f"rollback-{s}.json").write_text(json.dumps({k: live[k] for k in ("Title", "ReferenceType", "SiteSettings")}),
                                                  encoding="utf-8")
        self.fake.fail_update_on = LO               # its restore fails too, but the site never changed
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "rolled-back")
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)       # nothing to mark
        self.assertEqual(self.status(d), "rolled-back")

    def test_timeout_after_a_write_is_uncertain_and_the_read_back_records_it(self):
        plan, d = self.plan()
        self.slow(f"/{LO}/updatesite")              # loans is written, the answer comes too late
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "uncertain")
        self.assertEqual(len(self.updates()), 2)                                    # no restore, no retry
        self.assertEqual(self.fake.sites[LO]["Title"], "new loans")
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 2)
        self.assertEqual(len(self.updates()), 2)
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 0)       # both sites hold the payload
        self.assertEqual(self.status(d), "applied")

    def test_timeout_on_the_first_site_reads_back_as_partly_applied(self):
        plan, d = self.plan()
        self.slow(f"/{EQ}/updatesite")              # equipment written, loans never reached
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "uncertain")
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)
        p2 = json.loads((d / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(p2["status"], "recovery-required")
        self.assertEqual(p2["readback"], {"equipment": "applied", "loans": "not applied"})
        self.assertFalse(list(d.glob("live-*.json")))                               # never a baseline

    def test_mark_applied_checks_the_site_and_that_it_was_written(self):
        plan, d = self.plan()
        p = self.r / "other.json"
        p.write_text(json.dumps({"Response": {"Data": dict(self.fake.sites[EQ], SiteId=4242)}}), encoding="utf-8")
        args = self.exports()
        args[1] = f"equipment={p}"
        self.assertEqual(pls.main(["mark-applied", "R-1", *args]), 1)                # export of another site
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)       # never applied: UpdatedTime t0
        self.assertEqual(self.status(d), "planned")

    def test_an_applied_release_is_never_marked_again(self):
        plan, d = self.plan()
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 0)
        before = json.loads((d / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(before["status"], "applied")
        self.fake.sites[LO]["SiteSettings"] = {"Changed": "in the UI"}               # drift after the release
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)
        self.assertEqual(before, json.loads((d / "plan.json").read_text(encoding="utf-8")))
        self.assertFalse(list(d.glob("live-*.json")))

    def test_applied_differs_baseline_keeps_the_permissions_the_release_wrote(self):
        plan, d = self.plan()
        for s in ("equipment", "loans"):
            (d / f"payload-{s}.json").write_text(json.dumps({"Title": f"new {s}", "ReferenceType": "Results",
                                                             "SiteSettings": {"X": 1, "Dflt": True},
                                                             "InheritPermission": EQ if s == "equipment" else LO,
                                                             "Permissions": ["User,1,511"]}), encoding="utf-8")
        self.fake.drop_on_save = "Dflt"                         # Pleasanter canonicalises on save (D8)
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "applied-differs")
        live = json.loads((d / "live-loans.json").read_text(encoding="utf-8"))
        self.assertEqual(live["Permissions"], ["User,1,511"])
        self.assertEqual(live["InheritPermission"], LO)

    def set_state(self, d, **kw):
        plan = json.loads((d / "plan.json").read_text(encoding="utf-8"))
        (d / "plan.json").write_text(json.dumps(dict(plan, **kw)), encoding="utf-8")

    def test_recovery_required_is_never_promoted_by_sites_that_differ(self):
        plan, d = self.plan()
        self.set_state(d, status="recovery-required", apply_started_at="2026-01-01T00:00:00+09:00")
        for sid in (EQ, LO):                                   # neither payload nor rollback, written since the plan
            self.fake.sites[sid].update(SiteSettings={"Repaired": "by hand"}, UpdatedTime="t9")
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)
        self.assertEqual(self.status(d), "recovery-required")
        self.assertFalse(list(d.glob("live-*.json")))

    def test_exports_older_than_the_apply_are_refused(self):
        plan, d = self.plan()
        args = self.exports()                                   # taken before the apply
        time.sleep(1.1)
        self.set_state(d, status="uncertain", apply_started_at=pls._now())
        self.assertEqual(pls.main(["mark-applied", "R-1", *args]), 1)
        self.assertEqual(self.status(d), "uncertain")

    def test_preflight_read_failure_leaves_the_release_planned(self):
        plan, d = self.plan()
        self.fake.sites.pop(LO)                                 # getsite 404 during the preflight
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.status(d), "planned")
        self.assertEqual(self.updates(), [])

    def test_browser_runner_release_is_marked_from_its_exports(self):
        plan, d = self.plan()                                   # the runner wrote; plan.json stays planned, no apply-log
        for s, sid in (("equipment", EQ), ("loans", LO)):
            pl = json.loads((d / f"payload-{s}.json").read_text(encoding="utf-8"))
            self.fake.sites[sid].update(pl, UpdatedTime="t5")
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 0)
        self.assertEqual(self.status(d), "applied")

    def test_planned_release_with_a_rolled_back_log_is_not_marked(self):
        plan, d = self.plan()
        (d / "apply-log.json").write_text(json.dumps({"status": "rolled-back"}), encoding="utf-8")
        for s, sid in (("equipment", EQ), ("loans", LO)):
            pl = json.loads((d / f"payload-{s}.json").read_text(encoding="utf-8"))
            self.fake.sites[sid].update(pl, UpdatedTime="t5")
        self.assertEqual(pls.main(["mark-applied", "R-1", *self.exports()]), 1)
        self.assertEqual(self.status(d), "planned")

    def edit_by_someone_else(self, after_write_of, site_id):
        """Someone saves `site_id` in the UI right after our write of `after_write_of` (i.e. after the preflight)."""
        real = self.fake.handle

        def handle(path, body):
            res = real(path, body)
            if path == f"/api/items/{after_write_of}/updatesite":
                self.fake.sites[site_id].update(Title="edited by someone else", UpdatedTime="t-other")
            return res
        self.fake.handle = handle

    def test_a_site_changed_between_the_preflight_and_its_write_is_not_overwritten(self):
        plan, d = self.plan()
        first, second = plan["steps"][0], plan["steps"][1]
        self.edit_by_someone_else(first["site_id"], second["site_id"])
        self.assertEqual(pls.main(["apply", "R-1", "--yes"]), 1)
        self.assertEqual(self.fake.sites[second["site_id"]]["Title"], "edited by someone else")   # their change is kept
        self.assertNotEqual(self.status(d), "applied")
        log = json.loads((d / "apply-log.json").read_text(encoding="utf-8"))
        self.assertEqual((log["status"], log["failed_site"]), ("rolled-back", second["site"]))
        self.assertIn("changed by someone else", " ".join(log["log"]))
        restored = json.loads((d / f"rollback-{first['site']}.json").read_text(encoding="utf-8"))
        self.assertEqual(self.fake.sites[first["site_id"]]["Title"], restored["Title"])           # our first write is undone

    def bootstrap_plan(self):
        d = self.r / "releases/B-1"
        d.mkdir(parents=True)
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["sites"].update({"x1": {"title": "X1"}, "x2": {"title": "X2"}})
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        steps = [{"op": "createsite", "site": s, "parent_id": FOLDER, "payload": {"Title": s, "ReferenceType": "Results", "SiteSettings": {}}}
                 for s in ("x1", "x2")]
        (d / "bootstrap.json").write_text(json.dumps({"release": "B-1", "env": "dev", "parent_id": FOLDER, "steps": steps,
                                                      "status": "planned"}), encoding="utf-8")
        return d

    def test_bootstrap_timeout_is_recorded_and_a_rerun_waits_for_a_person(self):
        d = self.bootstrap_plan()
        self.slow("/createsite")
        n = len(self.fake.sites)
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 1)
        self.assertEqual(len(self.fake.sites), n + 1)                               # x1 exists, id unknown to pls
        self.assertEqual(json.loads((d / "bootstrap.json").read_text(encoding="utf-8"))["uncertain"], "x1")
        self.fake.hang_on = None
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 2)                 # refused: never a second x1
        self.assertEqual(len(self.fake.sites), n + 1)
        # a person found x1 under the folder and binds it; the re-run creates only x2
        x1 = max(self.fake.sites)
        self.assertEqual(pls.main(["bind", "--env", "dev", "--release", "B-1", "--created", f"x1={x1}"]), 0)
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 0)
        self.assertEqual(len(self.fake.sites), n + 2)
        rec = json.loads((d / "bootstrap.json").read_text(encoding="utf-8"))
        self.assertEqual(rec["status"], "created")
        self.assertNotIn("uncertain", rec)

    def test_bootstrap_killed_after_the_server_created_a_site_never_creates_it_twice(self):
        import pls_http as H
        d = self.bootstrap_plan()
        real = H.Client.create_site

        def dies(client, parent_id, payload):
            real(client, parent_id, payload)                                        # the server created the site …
            raise KeyboardInterrupt                                                 # … and the process stopped before binding

        n = len(self.fake.sites)
        H.Client.create_site = dies
        try:
            with self.assertRaises(KeyboardInterrupt):
                pls.main(["bootstrap", "B-1", "--yes"])
        finally:
            H.Client.create_site = real
        self.assertEqual(len(self.fake.sites), n + 1)
        self.assertEqual(json.loads((d / "bootstrap.json").read_text(encoding="utf-8"))["uncertain"], "x1")
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 2)                 # refused: never a second x1
        self.assertEqual(len(self.fake.sites), n + 1)

    def test_bootstrap_answered_with_an_error_leaves_no_site_in_flight(self):
        d = self.bootstrap_plan()
        import pls_http as H
        real = H.Client.create_site
        H.Client.create_site = lambda client, parent_id, payload: (500, None, "boom")
        try:
            self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 1)
        finally:
            H.Client.create_site = real
        self.assertNotIn("uncertain", json.loads((d / "bootstrap.json").read_text(encoding="utf-8")))
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes"]), 0)                 # answered "not created": a re-run may create

    def test_bootstrap_rerun_with_absent_confirmed_creates_the_site(self):
        d = self.bootstrap_plan()
        rec = json.loads((d / "bootstrap.json").read_text(encoding="utf-8"))
        (d / "bootstrap.json").write_text(json.dumps(dict(rec, uncertain="x1")), encoding="utf-8")
        n = len(self.fake.sites)
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes", "--absent", "x2"]), 2)   # wrong site: still refused
        self.assertEqual(pls.main(["bootstrap", "B-1", "--yes", "--absent", "x1"]), 0)
        self.assertEqual(len(self.fake.sites), n + 2)
        self.assertNotIn("uncertain", json.loads((d / "bootstrap.json").read_text(encoding="utf-8")))


class ClientErrorBodyTest(unittest.TestCase):
    def test_an_unreadable_error_body_is_an_uncertain_outcome(self):
        import io
        import urllib.error
        import pls_http as H

        class Broken(io.BytesIO):
            def read(self, *a):
                raise TimeoutError("timed out")

        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 500, "boom", {}, Broken())
        with self.assertRaises(H.UncertainOutcome):
            H.Client("http://127.0.0.1:9", "K", opener=opener).call("/api/items/1/updatesite", {})


class EnvValueTypesTest(unittest.TestCase):
    def test_a_number_in_values_is_never_substituted_and_resolves_as_text(self):
        e = {"sites": {}, "values": {"kb_probe_parent": 44708, "host": "dev.example"}}
        ids, vals = pls.id_maps(e)
        self.assertEqual(pls.to_refs("id 44708 on dev.example", ids, vals), "id 44708 on ${env:host}")
        self.assertEqual(pls.from_refs("${env:kb_probe_parent}", e), "44708")


class EnvValueReverseMappingTest(unittest.TestCase):
    """unpack maps an environment value back to ${env:x} as a whole value, or inside longer text only when the value
    is distinctive and stands as a whole token — never as a chance substring."""

    def refs(self, text, **values):
        ids, vals = pls.id_maps({"sites": {}, "values": values})
        return pls.to_refs(text, ids, vals)

    def test_a_short_or_numeric_value_never_rewrites_text_that_contains_it(self):
        self.assertEqual(self.refs("Item 4123", n="12"), "Item 4123")
        self.assertEqual(self.refs("Room 12", n="12"), "Room 12")
        self.assertEqual(self.refs("var limit = 120000;", n="120000"), "var limit = 120000;")     # all digits: never embedded
        self.assertEqual(self.refs("dev team", tag="dev"), "dev team")

    def test_the_whole_value_always_maps_back(self):
        self.assertEqual(self.refs("12", n="12"), "${env:n}")
        self.assertEqual(self.refs("dev", tag="dev"), "${env:tag}")

    def test_a_distinctive_value_maps_back_inside_text_as_a_whole_token_only(self):
        url = "http://dev.internal"
        self.assertEqual(self.refs("var u = 'http://dev.internal/api';", URL=url), "var u = '${env:URL}/api';")
        self.assertEqual(self.refs("[Manager],soumu@dev.example", MAIL="soumu@dev.example"), "[Manager],${env:MAIL}")
        self.assertEqual(self.refs("http://dev.internals.example", URL=url), "http://dev.internals.example")
        self.assertEqual(self.refs("xsoumu@dev.example", MAIL="soumu@dev.example"), "xsoumu@dev.example")

    def test_round_trip_to_another_environment_keeps_unrelated_text(self):
        dev = {"sites": {}, "values": {"n": "12", "URL": "http://dev.internal"}}
        stg = {"sites": {}, "values": {"n": "77", "URL": "http://stg.internal"}}
        live = {"Label": "Item 4123", "Count": "12", "Body": "fetch('http://dev.internal/x')"}
        ids, vals = pls.id_maps(dev)
        self.assertEqual(pls.from_refs(pls.to_refs(live, ids, vals), stg),
                         {"Label": "Item 4123", "Count": "77", "Body": "fetch('http://stg.internal/x')"})


class EnvValueLoadTest(unittest.TestCase):
    setUp = T.HttpTest.setUp
    tearDown = T.HttpTest.tearDown

    def set_values(self, values):
        envs = json.loads((self.r / "environments.json").read_text(encoding="utf-8"))
        envs["envs"]["dev"]["values"] = values
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")

    def test_a_value_that_is_not_text_or_a_number_is_refused_by_name(self):
        for bad in (["a"], {"a": 1}, True):
            self.set_values({"ok": "text", "broken": bad})
            with self.assertRaises(pls.Fail) as cm:
                pls.env_conf(self.r, "dev")
            self.assertIn("values.broken", str(cm.exception))
        self.set_values({"ok": "text", "n": 950, "later": None})
        self.assertEqual(pls.env_conf(self.r, "dev")["values"]["n"], 950)

    def test_lint_reports_a_weak_value_written_inside_longer_text(self):
        exp = self.r / "eq.json"
        pls.wj(exp, {"Response": {"Data": dict(self.fake.sites[EQ], Body="", SiteSettings={})}})
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "equipment"]), 0)
        f = self.r / "config/equipment/site.json"
        site = json.loads(f.read_text(encoding="utf-8"))

        def rules(grid_guide):
            f.write_text(json.dumps(dict(site, GridGuide=grid_guide), ensure_ascii=False), encoding="utf-8")
            return {i["rule"] for i in pls.lint(self.r)}

        self.set_values({"n": "12", "URL": "http://dev.internal"})
        self.assertIn("L-REF-04", rules("up to ${env:n} items"))                 # short value inside text
        self.assertNotIn("L-REF-04", rules("${env:n}"))                          # the whole value
        self.assertNotIn("L-REF-04", rules("see ${env:URL}/help"))               # distinctive value inside text


if __name__ == "__main__":
    unittest.main()
