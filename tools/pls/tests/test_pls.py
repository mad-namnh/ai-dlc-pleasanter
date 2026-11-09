"""Unit tests for pls (stdlib only):  python -m unittest discover -s tools/pls/tests -v"""
import json
import os
import sys
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pls  # noqa: E402

ENVS = {"managed_sites": ["a"], "envs": {
    "dev": {"role": "dev", "sites": {"a": {"id": 101, "title": "dev_A"}, "b": {"id": 102, "title": "dev_B"}},
            "values": {"URL": "http://dev.internal"}},
    "stg": {"role": "stg", "sites": {"a": {"id": 201, "title": "stg_A"}, "b": {"id": 202, "title": "stg_B"}},
            "values": {"URL": "http://stg.internal"}}}}


def export(site_id, b_id, url, extra_cols=(), scripts=None):
    cols = [{"ColumnName": "ClassA", "LabelText": "No"}, {"ColumnName": "ClassB", "ChoicesText": f"[[{b_id}]]"}] + list(extra_cols)
    ss = {"Version": 1.017, "Columns": cols, "Links": [{"SiteId": b_id, "ColumnName": "ClassB"}],
          "ServerScripts": scripts if scripts is not None else
          [{"Id": 1, "Name": "env", "Shared": True, "Body": f"var U = '{url}';"},
           {"Id": 2, "Name": "s1", "BeforeCreate": True, "Body": f"items.Get({b_id}, '{{}}');"}]}
    return {"StatusCode": 200, "Response": {"Data": {"SiteId": site_id, "Title": "x", "ReferenceType": "Results",
                                                      "Body": "", "UpdatedTime": "t", "SiteSettings": ss}}}


class PlsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.r = Path(self.tmp.name)
        (self.r / "environments.json").write_text(json.dumps(ENVS), encoding="utf-8")
        self.cwd = os.getcwd()
        os.environ["PLS_PROFILE_DIR"] = str(self.r / "_profiles")     # never the person's real profile
        os.chdir(self.r)
        # a stg release plan needs a recorded G3 of its release (I4); the fixture release R1 has one
        (self.r / "CLAUDE.md").write_text("| Approvers | Nam (all gates) |\n", encoding="utf-8")
        assert pls.main(["gate", "G3", "--approver", "Nam", "--release", "R1", "--quote", "G3 approved"]) == 0

    def tearDown(self):
        os.chdir(self.cwd)
        os.environ.pop("PLS_PROFILE_DIR", None)
        self.tmp.cleanup()

    def unpack_dev(self, **kw):
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(export(101, 102, "http://dev.internal", **kw)), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]), 0)
        return exp

    def test_unpack_uses_references_and_pack_resolves_per_env(self):
        self.unpack_dev()
        site = json.loads((self.r / "config/a/site.json").read_text(encoding="utf-8"))
        self.assertEqual(site["Links"][0]["SiteId"], "${site:b}")
        self.assertEqual(site["Columns"][1]["ChoicesText"], "[[${site:b}]]")
        self.assertIn("${env:URL}", (self.r / "config/a/server-scripts/env.js").read_text(encoding="utf-8"))
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["stg"], "a")
        self.assertEqual(p["Title"], "stg_A")
        self.assertEqual(p["SiteSettings"]["Links"][0]["SiteId"], 202)
        self.assertEqual(p["SiteSettings"]["Columns"][1]["ChoicesText"], "[[202]]")
        self.assertIn("items.Get(202", p["SiteSettings"]["ServerScripts"][1]["Body"])
        self.assertIn("http://stg.internal", p["SiteSettings"]["ServerScripts"][0]["Body"])

    def test_pack_dev_reproduces_export(self):
        exp = self.unpack_dev()
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["dev"], "a")
        self.assertEqual(p["SiteSettings"], json.loads(exp.read_text(encoding="utf-8"))["Response"]["Data"]["SiteSettings"])

    def test_drift_detects_ui_change(self):
        self.unpack_dev()
        changed = export(201, 202, "http://stg.internal",
                         extra_cols=[{"ColumnName": "ClassZ", "LabelText": "added in UI"}])
        (self.r / "stg.json").write_text(json.dumps(changed), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(self.r / "stg.json"), "--env", "stg", "--site", "a"]), 1)

    def test_no_drift_across_envs_when_equal(self):
        self.unpack_dev()
        (self.r / "stg.json").write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(self.r / "stg.json"), "--env", "stg", "--site", "a"]), 0)

    def test_lint_rules(self):
        scripts = [{"Id": 1, "Name": "env", "Shared": True, "Body": "const U = 'x';"},
                   {"Id": 2, "Name": "s1", "Body": "var k = 'sk-ant-abcdefghijklmnop'; items.Get(202, '{}');"}]
        self.unpack_dev(scripts=scripts)
        rules = sorted({i["rule"] for i in pls.lint(self.r)})
        # 202 is a stg id → not converted by dev unpack → hard-coded reference
        self.assertEqual(rules, ["L-LAD-01", "L-REF-01", "L-SCR-01", "L-SEC-01"])

    def job_files(self, jobs: dict, entries: list | None = None):
        import pls_side_effects as SE
        d = self.r / SE.JOBS_DIR
        d.mkdir(parents=True, exist_ok=True)
        for f in d.iterdir():
            f.unlink()
        for name, body in jobs.items():
            (d / f"{name}.js").write_text(body, encoding="utf-8")
        (d / SE.JOBS_INDEX).write_text(json.dumps(entries or [{"name": n} for n in jobs]), encoding="utf-8")

    def job_rules(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for i in pls.lint(self.r):
            if i["site"] == "_tenant":
                out.setdefault(i["rule"], []).append(i["msg"])
        return out

    def test_scheduled_script_bodies_follow_the_server_script_rules(self):
        self.job_files({"clean": "var t = items.Get(${site:a}, '{}');"})
        self.assertEqual(self.job_rules(), {})
        self.job_files({"rawid": "items.Get(202, '{}');"})                                 # L-REF-01: stg id written raw
        self.assertIn("202", self.job_rules()["L-REF-01"][0])
        self.job_files({"secret": "var k = 'sk-ant-abcdefghijklmnop';"})                   # L-SEC-01
        self.assertEqual(list(self.job_rules()), ["L-SEC-01"])
        self.job_files({"shared": "const U = 1;", "own": "const V = 2;"},
                       [{"name": "shared", "shared": True}, {"name": "own"}])            # L-SCR-01 only when shared (D7)
        self.assertEqual(self.job_rules()["L-SCR-01"], ["scheduled script shared: shared script declares top-level const/let (D7)"])
        self.job_files({"unres": "var u = '${env:NOPE}';"})                               # resolved per env, not guessed
        self.assertTrue(any("NOPE" in m for m in self.job_rules()["L-REF-02"]))
        self.job_files({"Bad Name": "var a = 1;"})                                          # L-JOB-01: file stem rule
        self.assertIn("L-JOB-01", self.job_rules())

    def test_job_layout_problems_reach_pls_lint(self):
        self.job_files({"orphan": "var a = 1;"}, [{"name": "orphan"}, {"name": "missing"}])
        self.assertTrue(any("missing.js is missing" in m for m in self.job_rules()["L-JOB-01"]))

    def test_jobs_baseline_is_the_last_verified_applied_release_of_the_same_env(self):
        def rel(name, env, status, at, jobs):
            d = self.r / "releases" / name
            d.mkdir(parents=True)
            (d / "plan.json").write_text(json.dumps({"release": name, "env": env, "status": status, "applied_at": at,
                                                     **({"jobs": jobs} if jobs is not None else {})}), encoding="utf-8")
        ok = {"fingerprints": {"j": "old"}, "changed": []}
        rel("R1", "stg", "applied", "2026-11-01T10:00:00+09:00", ok)
        rel("R2", "stg", "applied-differs", "2026-11-02T10:00:00+09:00", {"fingerprints": {"j": "differs"}, "changed": []})
        rel("R3", "dev", "applied", "2026-11-09T10:00:00+09:00", {"fingerprints": {"j": "dev"}, "changed": []})   # other env
        rel("R4", "stg", "applied", "2026-11-03T10:00:00+09:00", None)                     # made before the jobs check
        rel("R5", "stg", "planned", "2026-11-04T10:00:00+09:00", {"fingerprints": {"j": "planned"}, "changed": []})
        rel("R6", "stg", "applied", "2026-11-05T10:00:00+09:00",
            {"fingerprints": {"j": "unverified"}, "changed": ["j changed"]})                # manual deploy not confirmed
        rel("R7", "stg", "applied", "2026-11-06T10:00:00+09:00", {"fingerprints": ["broken"], "changed": []})   # hand-broken
        rel("R8", "stg", "applied", "2026-11-01T01:00:00+00:00", {"fingerprints": {"j": "utc-earlier"}, "changed": []})
        self.assertEqual(pls.last_applied_jobs(self.r, "stg"), {"j": "differs"})
        self.assertIsNone(pls.last_applied_jobs(self.r, "prod"))

    def test_scheduled_script_syntax_is_checked_on_the_resolved_body(self):
        import pls_scripts as SX
        if not SX.node_available():
            self.skipTest("node not installed")
        self.job_files({"ok": "var u = '${env:URL}'; return;"})          # wrapped like a server script: return allowed
        self.assertNotIn("L-SCR-02", self.job_rules())
        self.job_files({"broken": "var a = ;"})
        msgs = self.job_rules()["L-SCR-02"]
        self.assertEqual(len(msgs), 1)                                    # same text on every env → checked once
        self.assertIn("broken (dev)", msgs[0])

    def test_scheduled_script_syntax_check_is_skipped_with_a_warning_without_node(self):
        import contextlib
        import io
        import pls_scripts as SX
        self.job_files({"broken": "var a = ;"})
        err = io.StringIO()
        with mock.patch.object(SX, "node_available", return_value=False), contextlib.redirect_stderr(err):
            rules = self.job_rules()
        self.assertNotIn("L-SCR-02", rules)
        self.assertIn("node not found", err.getvalue())

    def test_slot_ledger(self):
        self.unpack_dev()
        (self.r / "design").mkdir()
        (self.r / "design/slot-ledger.json").write_text(json.dumps({"a": {"ClassA": {"status": "allocated"}}}), encoding="utf-8")
        msgs = [i["msg"] for i in pls.lint(self.r) if i["rule"] == "L-SLOT-01"]
        self.assertTrue(any("ClassB" in m for m in msgs))

    def test_process_without_display_condition_is_a_lint_error(self):          # L-PRC-01, D21
        ss = {"Processes": [{"Id": 1, "Name": "ok", "View": {"ColumnFilterHash": {"Status": "[\"100\"]"}}},
                            {"Id": 2, "Name": "none"},
                            {"Id": 3, "Name": "defaults-only", "View": {"Id": 0, "ApiDataType": 0, "ColumnFilterHash": {}}}]}
        self.assertEqual(pls.unconditioned_processes(ss), ["none", "defaults-only"])
        self.assertEqual(pls.unconditioned_processes(ss, view_missing_only=True), ["none"])
        self.unpack_dev()
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Processes"] = ss["Processes"]
        p.write_text(json.dumps(site), encoding="utf-8")
        msgs = [i["msg"] for i in pls.lint(self.r) if i["rule"] == "L-PRC-01"]
        self.assertEqual(len(msgs), 1)                    # only the process with no View object (D21)
        self.assertIn("'none'", msgs[0])

    def test_canon_and_lint(self):
        self.unpack_dev()
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Processes"] = [{"Id": 1, "Name": "x", "ScreenType": 20, "View": {"ColumnFilterHash": {}},
                              "DataChanges": [{"Id": 1, "Type": "InputValue", "ColumnName": "ClassA", "Value": "v"}],
                              "Notifications": [{"Id": 1, "Type": 1, "Address": "[Manager]"}]}]
        p.write_text(json.dumps(site), encoding="utf-8")
        self.assertIn("L-CAN-01", {i["rule"] for i in pls.lint(self.r)})
        self.assertEqual(pls.main(["canon", "--site", "a"]), 0)
        self.assertNotIn("L-CAN-01", {i["rule"] for i in pls.lint(self.r)})
        proc = json.loads(p.read_text(encoding="utf-8"))["Processes"][0]
        self.assertNotIn("ScreenType", proc)
        self.assertEqual(proc["View"]["ApiDataType"], 0)
        self.assertEqual(proc["Notifications"][0]["MediaType"], "application/json")
        self.assertFalse(proc["DataChanges"][0]["ValueFormulaIsDisplayError"])

    def _stg_export_from_payload(self, rel, mutate=None):
        pl = json.loads((self.r / "releases" / rel / "payload.json").read_text(encoding="utf-8"))
        if mutate:
            mutate(pl["SiteSettings"])
        return {"StatusCode": 200, "Response": {"Data": {"SiteId": 201, "Title": pl["Title"], "ReferenceType": pl["ReferenceType"],
                                                          "Body": pl.get("Body", ""), "SiteName": "", "SiteGroupName": "",
                                                          "SiteSettings": pl["SiteSettings"]}}}

    def test_release_lifecycle_drift_against_last_release(self):
        self.unpack_dev()
        stg_before = self.r / "stg-before.json"
        stg_before.write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": "", "ClassC": "new in git"})
        # first release: nothing applied yet → plan allowed
        self.assertEqual(pls.main(["plan", str(stg_before), "--env", "stg", "--site", "a", "--release", "R1"]), 0)
        # mark-applied refuses when live != payload
        wrong = self.r / "wrong.json"
        wrong.write_text(json.dumps(self._stg_export_from_payload("R1", lambda s: s["Columns"].pop())), encoding="utf-8")
        self.assertEqual(pls.main(["mark-applied", "R1", str(wrong)]), 1)
        live = self.r / "stg-live.json"
        live.write_text(json.dumps(self._stg_export_from_payload("R1")), encoding="utf-8")
        self.assertEqual(pls.main(["mark-applied", "R1", str(live)]), 0)
        # git moves on (unreleased change) → NOT drift, because the baseline is the last release
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Columns"].append({"ColumnName": "ClassC", "LabelText": "new in git"})
        p.write_text(json.dumps(site), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(live), "--env", "stg", "--site", "a"]), 0)
        # customer edits stg in the UI (adds a choice) → drift; reverting it is data-impacting; plan refused
        def add_choice(s):
            [c for c in s["Columns"] if c["ColumnName"] == "ClassA"][0]["ChoicesText"] = "X\nY"
        edited = self.r / "stg-edited.json"
        edited.write_text(json.dumps(self._stg_export_from_payload("R1", add_choice)), encoding="utf-8")
        self.assertEqual(pls.main(["drift", str(edited), "--env", "stg", "--site", "a"]), 1)
        diffs, text = pls.drift_report(self.r, ENVS["envs"]["stg"], "stg", "a", json.loads(edited.read_text(encoding="utf-8")), None)
        self.assertIn("Reverting this drift would be: data-impacting", text)
        self.assertEqual(pls.main(["plan", str(edited), "--env", "stg", "--site", "a", "--release", "R2"]), 1)
        # planning over the accepted drift would remove the customer's choice → data-impacting → migration required
        args = ["plan", str(edited), "--env", "stg", "--site", "a", "--release", "R2", "--accept-drift", "ops/drift/decision.md"]
        self.assertEqual(pls.main(args), 1)
        self._migration("mig")
        self.assertEqual(pls.main(args + ["--migration", "mig"]), 0)

    def _ledger(self, slots):
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design/slot-ledger.json").write_text(json.dumps(
            {"a": {k: {"label": v, "status": "allocated", "zone": "madlab"} for k, v in slots.items()}}), encoding="utf-8")

    def _stg_live(self, extra_cols=(), editor=None):
        ex = export(201, 202, "http://stg.internal", extra_cols=extra_cols)
        if editor is not None:
            ex["Response"]["Data"]["SiteSettings"]["EditorColumnHash"] = {"General": editor}
        p = self.r / "stg-live-slots.json"
        p.write_text(json.dumps(ex), encoding="utf-8")
        return p

    def test_slots_clean(self):
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        self.assertEqual(pls.slot_collisions(*self._models(self._stg_live())), [])
        self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 0)

    def _models(self, live_path):
        e = ENVS["envs"]["stg"]
        live = pls.logical(json.loads(live_path.read_text(encoding="utf-8")), e)
        git = pls.read_tree(self.r / "config/a")
        led = json.loads((self.r / "design/slot-ledger.json").read_text(encoding="utf-8"))["a"]
        return live["settings"], git["settings"], led

    def test_slots_collision_blocks_plan(self):
        # customer added NumD in the UI on stg; git also defines NumD → deploying would overwrite it (A2)
        self.unpack_dev()
        p = self.r / "config/a/site.json"
        site = json.loads(p.read_text(encoding="utf-8"))
        site["Columns"].append({"ColumnName": "NumD", "LabelText": "git use"})
        p.write_text(json.dumps(site), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": ""})
        live = self._stg_live(extra_cols=[{"ColumnName": "NumD", "LabelText": "顧客の項目"}])
        kinds = {c["kind"] for c in pls.slot_collisions(*self._models(live))}
        self.assertEqual(kinds, {"collision"})
        self.assertEqual(pls.main(["plan", str(live), "--env", "stg", "--site", "a", "--release", "R1"]), 1)
        self.assertFalse((self.r / "releases/R1/plan.json").exists())

    def test_slots_editor_only_and_repurposed(self):
        # NumE enabled only by placing it on the editor (no Columns entry, D8); ClassA relabelled on the target
        self.unpack_dev()
        self._ledger({"ClassA": "No", "ClassB": ""})
        live = self._stg_live(editor=["ClassA", "ClassB", "NumE"])
        ex = json.loads(live.read_text(encoding="utf-8"))
        [c for c in ex["Response"]["Data"]["SiteSettings"]["Columns"] if c["ColumnName"] == "ClassA"][0]["LabelText"] = "別用途"
        live.write_text(json.dumps(ex), encoding="utf-8")
        found = {(c["slot"], c["kind"]) for c in pls.slot_collisions(*self._models(live))}
        self.assertEqual(found, {("NumE", "unledgered-live"), ("ClassA", "repurposed")})

    def test_slots_missing_ledger_refuses_plan(self):
        self.unpack_dev()
        self.assertEqual(pls.main(["plan", str(self._stg_live()), "--env", "stg", "--site", "a", "--release", "R1"]), 1)

    # ---------------------------------------------------------- multi-site release plan (A3)

    def _two_sites(self):
        """config/a references site b (Links + script); config/b references nothing."""
        self.unpack_dev()
        b = {"StatusCode": 200, "Response": {"Data": {"SiteId": 102, "Title": "dev_B", "ReferenceType": "Results", "Body": "",
             "UpdatedTime": "t0", "SiteSettings": {"Version": 1.017, "Columns": [{"ColumnName": "ClassA", "LabelText": "Code"}]}}}}
        p = self.r / "dev-b.json"
        p.write_text(json.dumps(b), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(p), "--env", "dev", "--site", "b"]), 0)
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design/slot-ledger.json").write_text(json.dumps({
            "a": {"ClassA": {"label": "No", "status": "allocated"}, "ClassB": {"label": "", "status": "allocated"}},
            "b": {"ClassA": {"label": "Code", "status": "allocated"}}}), encoding="utf-8")
        sa = self.r / "stg-a.json"
        sa.write_text(json.dumps(export(201, 202, "http://stg.internal")), encoding="utf-8")
        bs = json.loads(json.dumps(b)); bs["Response"]["Data"].update(SiteId=202, Title="stg_B", UpdatedTime="t-stg-b")
        sb = self.r / "stg-b.json"
        sb.write_text(json.dumps(bs), encoding="utf-8")
        return sa, sb

    def test_order_sites_and_cycles(self):
        self.assertEqual(pls.order_sites({"a": {"b"}, "b": set(), "c": {"a"}}), (["b", "a", "c"], []))
        self.assertEqual(pls.order_sites({"a": {"b"}, "b": {"a"}, "c": set()}), (["c", "a", "b"], ["a", "b"]))

    def test_release_plan_orders_by_dependency_and_reverses_rollback(self):
        sa, sb = self._two_sites()
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 0)
        rel = self.r / "releases/R1"
        plan = json.loads((rel / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["sites"], ["b", "a"])                      # a references b → b first
        self.assertEqual([x["site"] for x in plan["rollback"]], ["a", "b"])
        self.assertEqual(plan["per_site"]["a"]["depends_on"], ["b"])
        op = (self.r / "releases/R1/diff-report.operator.md").read_text(encoding="utf-8")   # written by the tool
        self.assertIn("| Order | b → a", op)
        self.assertIn("## Checks per site", op)
        self.assertEqual(plan["per_site"]["b"]["snapshot_updated_time"], "t-stg-b")
        for f in ("payload-a.json", "payload-b.json", "rollback-a.json", "rollback-b.json", "raw-diff-a.md", "raw-diff-b.md"):
            self.assertTrue((rel / f).exists(), f)
        pa = json.loads((rel / "payload-a.json").read_text(encoding="utf-8"))
        self.assertIn("202", json.dumps(pa))                              # ${site:b} resolved to stg id
        self.assertNotIn("${site:", json.dumps(pa))

    def test_release_plan_records_scheduled_script_changes_against_the_last_applied_release(self):
        import pls_side_effects as SE
        sa, sb = self._two_sites()
        d = self.r / SE.JOBS_DIR
        d.mkdir(parents=True)
        (d / "nightly.js").write_text("const id = ${site:b};", encoding="utf-8")
        (d / SE.JOBS_INDEX).write_text(json.dumps([{"name": "nightly", "schedule": "毎日", "enabled": True}]), encoding="utf-8")
        for rel in ("R2", "R3", "R4", "R5"):
            self.assertEqual(pls.main(["gate", "G3", "--approver", "Nam", "--release", rel, "--quote", "G3 approved"]), 0)
        plan_of = lambda rel: json.loads((self.r / f"releases/{rel}/plan.json").read_text(encoding="utf-8"))   # noqa: E731
        rp = lambda rel: pls.main(["release-plan", "--env", "stg", "--release", rel, "--export", f"a={sa}", "--export", f"b={sb}"])  # noqa: E731
        import contextlib
        import io
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(rp("R1"), 0)
        self.assertIn("envs.stg.side_effects.jobs is 'unknown' — `pls apply` will refuse", out.getvalue())
        self.assertIn("JOB nightly added", out.getvalue())
        plan = plan_of("R1")
        self.assertEqual(plan["jobs"]["deploy"], "manual")
        self.assertTrue(plan["jobs"]["changed"][0].startswith("nightly added"))
        # what the operator copies is resolved for stg (site b = 202 there)
        self.assertEqual((self.r / "releases/R1/scheduled-scripts/nightly.js").read_text(encoding="utf-8"), "const id = 202;")
        self.assertIn("Scheduled scripts (manual)", (self.r / "releases/R1/diff-report.operator.md").read_text(encoding="utf-8"))
        with self.assertRaises(pls.Fail):                                            # not applied yet
            pls.main(["jobs-verified", "R1", "--by", "Nam", "--quote", "copied and checked"])
        plan.update(status="applied", applied_at="2026-11-09T10:00:00+09:00")       # as mark-applied records it
        (self.r / "releases/R1/plan.json").write_text(json.dumps(plan), encoding="utf-8")
        self.assertEqual(rp("R2"), 0)                                                # deploy not confirmed: listed again
        self.assertTrue(plan_of("R2")["jobs"]["changed"][0].startswith("nightly added"))
        with self.assertRaises(pls.Fail):                                            # only a profile approver
            pls.main(["jobs-verified", "R1", "--by", "Someone", "--quote", "ok"])
        self.assertEqual(pls.main(["jobs-verified", "R1", "--by", "Nam", "--quote", "copied and checked"]), 0)
        self.assertEqual(rp("R3"), 0)
        self.assertEqual(plan_of("R3")["jobs"]["changed"], [])
        self.assertFalse((self.r / "releases/R3/scheduled-scripts").exists())
        (d / "nightly.js").write_text("const id = ${site:b}; // v2", encoding="utf-8")
        self.assertEqual(rp("R4"), 0)
        self.assertEqual(plan_of("R4")["jobs"]["changed"], ["nightly changed"])
        (d / SE.JOBS_INDEX).write_text("[{}]", encoding="utf-8")                   # a bad index refuses the plan
        self.assertEqual(rp("R5"), 1)
        self.assertFalse((self.r / "releases/R5").exists())

    def test_jobs_verified_accepts_an_operator_of_the_env_or_a_g4_approver(self):
        def applied(rel, env):
            d = self.r / "releases" / rel
            d.mkdir(parents=True)
            (d / "plan.json").write_text(json.dumps({"release": rel, "env": env, "status": "applied", "sites": [],
                                                     "jobs": {"fingerprints": {"nightly": "x"}, "changed": ["nightly added"]}}),
                                         encoding="utf-8")
        verified = lambda rel: json.loads((self.r / f"releases/{rel}/plan.json").read_text(encoding="utf-8"))["jobs"].get("verified")  # noqa: E731
        jv = lambda *a: pls.main(["jobs-verified", *a, "--quote", "copied and compared"])                                # noqa: E731
        for rel in ("S1", "S2", "S3", "S4", "S5"):
            applied(rel, "stg")
        prof = self.r / "CLAUDE.md"
        # older profile, no Operators row: only G4 approvers
        with self.assertRaises(pls.Fail):
            jv("S1", "--by", "Hana")
        prof.write_text("| Approvers | Nam (all gates) |\n| Operators | dev: Taro; stg: Hana (night shift); prod: <customer operator> |\n",
                        encoding="utf-8")
        self.assertEqual(jv("S1", "--by", "hana"), 0)                                 # operator of stg (name matched as written)
        self.assertEqual({k: verified("S1")[k] for k in ("by", "role", "env", "quote")},
                         {"by": "Hana", "role": "operator", "env": "stg", "quote": "copied and compared"})
        self.assertIn("at", verified("S1"))
        with self.assertRaises(pls.Fail):                                              # dev's operator cannot confirm stg
            jv("S2", "--by", "Taro")
        with self.assertRaises(pls.Fail):                                              # nobody of the profile
            jv("S2", "--by", "Mallory")
        self.assertIsNone(verified("S2"))
        self.assertEqual(jv("S3", "--by", "Nam"), 0)
        self.assertEqual(verified("S3")["role"], "g4-approver")
        self.assertEqual(jv("S4", "--by", "Hana", "--approved-by", "Nam"), 0)          # copier and approver differ
        self.assertEqual((verified("S4")["by"], verified("S4")["approved_by"]), ("Hana", "Nam"))
        with self.assertRaises(pls.Fail):                                              # --approved-by must be a G4 approver
            jv("S5", "--by", "Hana", "--approved-by", "Taro")
        import pls_gate as GT
        self.assertEqual(GT.operators("| Operators | dev: Nam; stg: <name>; prod: <customer operator> |"), {"dev": {"Nam"}})
        self.assertIsNone(GT.operators("| Approvers | Nam |"))

    def test_release_plan_writes_nothing_if_one_site_fails(self):
        sa, sb = self._two_sites()
        bad = json.loads(sb.read_text(encoding="utf-8"))
        bad["Response"]["Data"]["SiteSettings"]["Columns"].append({"ColumnName": "NumZ", "LabelText": "customer"})
        sb.write_text(json.dumps(bad), encoding="utf-8")
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 1)
        self.assertFalse((self.r / "releases/R1").exists())

    def test_release_plan_mark_applied_and_drift_per_site(self):
        sa, sb = self._two_sites()
        self.assertEqual(pls.main(["release-plan", "--env", "stg", "--release", "R1", "--export", f"a={sa}", "--export", f"b={sb}"]), 0)
        rel = self.r / "releases/R1"
        lives = {}
        for site, sid in (("a", 201), ("b", 202)):
            pl = json.loads((rel / f"payload-{site}.json").read_text(encoding="utf-8"))
            p = self.r / f"live-{site}.json"
            p.write_text(json.dumps({"Response": {"Data": dict(pl, SiteId=sid)}}), encoding="utf-8")
            lives[site] = p
        self.assertEqual(pls.main(["mark-applied", "R1", "--export", f"a={lives['a']}"]), 1)   # every site required
        self.assertEqual(pls.main(["mark-applied", "R1", "--export", f"a={lives['a']}", "--export", f"b={lives['b']}"]), 0)
        self.assertEqual(json.loads((rel / "plan.json").read_text(encoding="utf-8"))["status"], "applied")
        # drift baseline for each site is that site's payload in the multi-site release
        self.assertEqual(pls.main(["drift", str(lives["b"]), "--env", "stg", "--site", "b"]), 0)
        self.assertEqual(pls.main(["drift", str(lives["a"]), "--env", "stg", "--site", "a"]), 0)

    def _migration(self, name, files=("migration.json", "backup", "dry-run.md")):
        d = self.r / name
        d.mkdir(exist_ok=True)
        if "migration.json" in files:
            (d / "migration.json").write_text(json.dumps({"site": "a", "keys": ["ClassA"], "rollback": "bulkupsert backup/"}), encoding="utf-8")
        if "backup" in files:
            (d / "backup").mkdir(exist_ok=True)
            (d / "backup/records.json").write_text("[]", encoding="utf-8")
        if "dry-run.md" in files:
            (d / "dry-run.md").write_text("dry run ok", encoding="utf-8")
        return d

    def test_migration_problems(self):
        self.assertTrue(pls.migration_problems(self.r, None))
        self._migration("m1", files=("migration.json",))
        probs = pls.migration_problems(self.r, "m1")
        self.assertTrue(any("backup" in p for p in probs) and any("dry-run" in p for p in probs))
        self._migration("m2")
        self.assertEqual(pls.migration_problems(self.r, "m2"), [])
        (self.r / "m2/backup/records.json").unlink()
        (self.r / "m2/backup/.keep").write_text("", encoding="utf-8")       # a placeholder is not a backup
        self.assertTrue(any("empty" in p for p in pls.migration_problems(self.r, "m2")))

    # ---------------------------------------------------------- permissions (C3, D15)

    def _with_perms(self, ex, inherit, entries):
        ex["Response"]["Data"].update(InheritPermission=inherit, Permissions=entries)
        return ex

    def test_permissions_unpack_refs_pack_resolves_and_lint(self):
        envs = json.loads(json.dumps(ENVS))
        envs["envs"]["dev"]["principals"] = {"admins": "Group,2"}
        envs["envs"]["stg"]["principals"] = {"admins": "Group,7"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(self._with_perms(export(101, 102, "http://dev.internal"), 101, ["Group,2,511", "User,99,1"])), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]), 0)
        perms = json.loads((self.r / "config/a/permissions.json").read_text(encoding="utf-8"))
        self.assertEqual(perms["inherit"], "${site:a}")
        self.assertIn("${principal:admins},511", perms["entries"])
        self.assertTrue(any(i["rule"] == "L-PERM-01" and "User,99" in i["msg"] for i in pls.lint(self.r)))
        # unmapped principal cannot be packed for another environment
        with self.assertRaises(pls.Fail):
            pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        perms["entries"] = ["${principal:admins},511"]
        (self.r / "config/a/permissions.json").write_text(json.dumps(perms), encoding="utf-8")
        p = pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        self.assertEqual((p["InheritPermission"], p["Permissions"]), (201, ["Group,7,511"]))

    def test_permissions_not_managed_means_not_compared_and_not_sent(self):
        self.unpack_dev()                                  # export without permission keys → no permissions.json
        self.assertFalse((self.r / "config/a/permissions.json").exists())
        p = pls.payload(pls.read_tree(self.r / "config/a"), ENVS["envs"]["stg"], "a")
        self.assertNotIn("Permissions", p)                 # omitted → live permissions untouched (D15)
        live = self.r / "stg-perm.json"
        live.write_text(json.dumps(self._with_perms(export(201, 202, "http://stg.internal"), 201, ["User,1,511"])), encoding="utf-8")
        self._ledger({"ClassA": "No", "ClassB": ""})
        self.assertEqual(pls.main(["plan", str(live), "--env", "stg", "--site", "a", "--release", "R1"]), 0)
        self.assertEqual(json.loads((self.r / "releases/R1/plan.json").read_text(encoding="utf-8"))["classification"]["classification"], "config-only")

    def test_permission_change_is_permission_impacting(self):
        envs = json.loads(json.dumps(ENVS))
        for k, v in (("dev", "Group,2"), ("stg", "Group,7")):
            envs["envs"][k]["principals"] = {"admins": v}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(self._with_perms(export(101, 102, "http://dev.internal"), 101, ["Group,2,511"])), encoding="utf-8")
        pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"])
        live = self.r / "stg-perm.json"
        live.write_text(json.dumps(self._with_perms(export(201, 202, "http://stg.internal"), 201, ["Group,7,31"])), encoding="utf-8")
        diffs = pls.flat_diff(pls.same_meta(pls.logical(json.loads(live.read_text(encoding="utf-8")), envs["envs"]["stg"]), pls.read_tree(self.r / "config/a")),
                              pls.read_tree(self.r / "config/a"))
        self.assertEqual(pls.classify(diffs)["classification"], "permission-impacting")

    def test_process_access_control_refs(self):
        envs = json.loads(json.dumps(ENVS))
        envs["envs"]["dev"]["principals"] = {"support": "Group,373"}
        envs["envs"]["stg"]["principals"] = {"support": "Group,9"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        ex = export(101, 102, "http://dev.internal")
        ex["Response"]["Data"]["SiteSettings"]["Processes"] = [{"Id": 1, "Name": "escalate", "Groups": [373], "Users": [5]}]
        p = self.r / "dev.json"
        p.write_text(json.dumps(ex), encoding="utf-8")
        pls.main(["unpack", str(p), "--env", "dev", "--site", "a"])
        proc = json.loads((self.r / "config/a/site.json").read_text(encoding="utf-8"))["Processes"][0]
        self.assertEqual(proc["Groups"], ["${principal:support}"])
        self.assertEqual(proc["Users"], [5])                                   # unmapped → raw → lint + pack refuses
        self.assertTrue(any(i["rule"] == "L-PERM-01" and "Users" in i["msg"] for i in pls.lint(self.r)))
        with self.assertRaises(pls.Fail):
            pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        site = json.loads((self.r / "config/a/site.json").read_text(encoding="utf-8"))
        del site["Processes"][0]["Users"]
        (self.r / "config/a/site.json").write_text(json.dumps(site), encoding="utf-8")
        pl = pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")
        self.assertEqual(pl["SiteSettings"]["Processes"][0]["Groups"], [9])   # resolved per environment
        envs["envs"]["stg"]["principals"]["support"] = "User,9"                  # wrong principal type
        with self.assertRaises(pls.Fail):
            pls.payload(pls.read_tree(self.r / "config/a"), envs["envs"]["stg"], "a")

    def test_last_applied_release_compares_instants_not_strings(self):
        # Escaped in slice 1.5: R-01 applied_at "…T09:19:30+09:00" (00:19 UTC) sorted after
        # R-02 "…T01:48:06+00:00" as strings, so drift kept using the older release as baseline.
        for rel, ts in (("R-01", "2026-11-05T09:19:30+09:00"), ("R-02", "2026-11-05T01:48:06+00:00")):
            d = self.r / "releases" / rel
            d.mkdir(parents=True)
            (d / "plan.json").write_text(json.dumps({"release": rel, "env": "stg", "site": "a",
                                                     "status": "applied", "applied_at": ts}), encoding="utf-8")
        got = [p["release"] for _, p in pls.releases_for(self.r, "stg", "a", "applied")]
        self.assertEqual(got, ["R-01", "R-02"])

    def test_classify_summary_change_is_data_impacting(self):
        d = [{"path": "settings.Summaries[1]", "kind": "added", "before": None, "after": {"Type": "Total"}}]
        c = pls.classify(d)
        self.assertEqual(c["classification"], "data-impacting")
        self.assertIn("D16", c["data_impacting"][0])

    def test_classify_lookup_json_by_meaning_not_layout(self):
        before = '[\n  {\n    "SiteId" : ${site:b},\n    "View": {"ColumnFilterHash": {"Status": 1}}\n  }\n]'
        layout = '[\n  {\n    "SiteId": ${site:b},\n    "View": {\n      "ColumnFilterHash": {\n        "Status": "1"\n      }\n    }\n  }\n]'
        d = [{"path": "settings.Columns[ClassO].ChoicesText", "kind": "changed", "before": before, "after": layout}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")      # re-serialised by an import
        comma = '[{"SiteId": ${site:b}, "Lookups": [{"From": "A", "To": "A",}]}]'
        clean = '[{"SiteId": ${site:b}, "Lookups": [{"From": "A", "To": "A"}]}]'
        d = [{"path": "settings.Columns[ClassF].ChoicesText", "kind": "changed", "before": comma, "after": clean}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")      # trailing comma dropped by an import
        other = layout.replace("${site:b}", "${site:c}")
        d = [{"path": "settings.Columns[ClassO].ChoicesText", "kind": "changed", "before": before, "after": other}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")   # the link now points elsewhere

    def test_classify(self):
        d = [{"path": "settings.Columns[ClassB]", "kind": "removed", "before": {}, "after": None}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a\nb\nc"}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")
        d = [{"path": "settings.Columns[ClassE].ChoicesText", "kind": "changed", "before": "a\nb", "after": "a"}]
        self.assertEqual(pls.classify(d)["classification"], "data-impacting")

    def test_bootstrap_plan_and_bind_new_site(self):
        envs = json.loads(json.dumps(ENVS))
        envs["managed_sites"] = ["a", "c"]
        envs["envs"]["stg"]["parent_id"] = 900
        envs["envs"]["stg"]["sites"]["c"] = {"title": "stg_C"}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        (self.r / "config/c").mkdir(parents=True)
        (self.r / "config/c/meta.json").write_text(json.dumps({"ReferenceType": "Issues"}), encoding="utf-8")
        (self.r / "config/c/site.json").write_text(json.dumps({"Links": [{"SiteId": "${site:a}"}]}), encoding="utf-8")
        e = pls.env_conf(self.r, "stg")
        with self.assertRaises(pls.Fail):                      # a reference to an unbound site cannot resolve
            pls.from_refs({"Links": [{"SiteId": "${site:c}"}]}, e)
        self.assertEqual(pls.id_maps(e)[0], {"201": "a", "202": "b"})
        self.assertEqual(pls.main(["bootstrap-plan", "--env", "stg", "--release", "R-1"]), 0)
        bp = json.loads((self.r / "releases/R-1/bootstrap.json").read_text(encoding="utf-8"))
        self.assertEqual([s["site"] for s in bp["steps"]], ["c"])
        self.assertEqual(bp["steps"][0]["payload"], {"Title": "stg_C", "ReferenceType": "Issues", "Body": "", "SiteSettings": {}})
        with self.assertRaises(pls.Fail):                      # id already used
            pls.main(["bind", "--env", "stg", "--release", "R-1", "--created", "c=201"])
        self.assertEqual(pls.main(["bind", "--env", "stg", "--release", "R-1", "--created", "c=203"]), 0)
        e = pls.env_conf(self.r, "stg")
        self.assertEqual(e["sites"]["c"]["id"], 203)
        self.assertEqual(pls.payload(pls.read_tree(self.r / "config/c"), e, "c")["SiteSettings"]["Links"][0]["SiteId"], 201)
        self.assertEqual(json.loads((self.r / "releases/R-1/bootstrap.json").read_text(encoding="utf-8"))["status"], "created")
        self.assertEqual(pls.main(["bootstrap-plan", "--env", "stg", "--release", "R-2"]), 0)   # nothing left
        self.assertFalse((self.r / "releases/R-2/bootstrap.json").exists())

    def test_bootstrap_refused_for_prod(self):
        envs = json.loads(json.dumps(ENVS))
        envs["envs"]["prod"] = {"role": "prod", "parent_id": 1, "sites": {}}
        (self.r / "environments.json").write_text(json.dumps(envs), encoding="utf-8")
        with self.assertRaises(pls.Fail):
            pls.main(["bootstrap-plan", "--env", "prod", "--release", "R-1"])

    def test_classify_process_access_control_is_permission_impacting(self):
        d = [{"path": "settings.Processes[escalate].Groups", "kind": "added", "before": None, "after": ["${principal:x}"]}]
        self.assertEqual(pls.classify(d)["classification"], "permission-impacting")
        d = [{"path": "settings.Processes[escalate]", "kind": "added", "before": None, "after": {"Name": "escalate", "Groups": [1]}}]
        self.assertEqual(pls.classify(d)["classification"], "permission-impacting")
        d = [{"path": "settings.Processes", "kind": "added", "before": None, "after": [{"Name": "r", "Groups": [1]}]}]
        self.assertEqual(pls.classify(d)["classification"], "permission-impacting")
        d = [{"path": "settings.Processes[escalate].DisplayName", "kind": "changed", "before": "a", "after": "b"}]
        self.assertEqual(pls.classify(d)["classification"], "config-only")

    def test_new_sites_only_after_bootstrap_and_before_first_applied_release(self):
        d = self.r / "releases/B-1"; d.mkdir(parents=True)
        (d / "bootstrap.json").write_text(json.dumps({"env": "dev", "created": {"a": 101}}), encoding="utf-8")
        self.assertEqual(pls.new_sites(self.r, "dev"), {"a"})
        self.assertEqual(pls.new_sites(self.r, "stg"), set())
        d2 = self.r / "releases/R-1"; d2.mkdir(parents=True)
        (d2 / "plan.json").write_text(json.dumps({"release": "R-1", "env": "dev", "sites": ["a"], "status": "applied",
                                                  "applied_at": "2026-11-05T10:00:00+09:00"}), encoding="utf-8")
        self.assertEqual(pls.new_sites(self.r, "dev"), set())


    # ---------------------------------------------------------------- D3: init, launcher, skills, coverage paths

    def test_init_records_the_origin(self):
        import tempfile as _t
        with _t.TemporaryDirectory() as d:
            for origin in ("new", "existing"):
                target = Path(d) / origin
                pls.init_project(target, "project", "stg", "Nam", origin=origin)
                text = (target / "CLAUDE.md").read_text(encoding="utf-8")
                self.assertIn(f"| Origin | `{origin}` |", text)
                self.assertIn("No P1 before the onboarding summary exists", text)

    def test_change_work_on_an_existing_app_waits_for_the_onboarding_summary(self):
        import pls_gate as GT
        proj = self.r / "takeover"
        pls.init_project(proj, "project", "stg", "Nam", origin="existing")
        os.chdir(proj)
        try:
            self.assertEqual(GT.origin(proj), "existing")
            self.assertEqual(pls.main(["step", "onboarding", "adopt site 1"]), 0)      # onboarding itself is allowed
            self.assertEqual(pls.main(["step", "P6", "incident"]), 0)
            for argv in (["step", "P1", "analyse the request"], ["step", "G1", "ask"],
                         ["gate", "G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "ok"],
                         ["bootstrap-plan", "--env", "dev", "--release", "B-1"],
                         ["release-plan", "--env", "dev", "--release", "R-1", "--export", "a=x.json"]):
                with self.assertRaises(pls.Fail, msg=argv) as cm:
                    pls.main(argv)
                self.assertIn("onboarding", str(cm.exception))
            (proj / "requirements/REQ-001-x.md").write_text("# REQ-001\n", encoding="utf-8")
            self.assertIn("L-ONB-01", {i["rule"] for i in pls.lint(proj)})
            (proj / "ops/onboarding").mkdir(parents=True, exist_ok=True)
            (proj / "ops/onboarding/2026-11-09-summary.md").write_text("# Onboarding\n", encoding="utf-8")
            self.assertNotIn("L-ONB-01", {i["rule"] for i in pls.lint(proj)})
            self.assertEqual(pls.main(["step", "P1", "analyse the request"]), 0)
            self.assertEqual(pls.main(["gate", "G1", "--approver", "Nam", "--item", "REQ-001", "--quote", "ok"]), 0)
        finally:
            os.chdir(self.r)
        new = self.r / "fresh"
        pls.init_project(new, "project", "stg", "Nam", origin="new")
        self.assertFalse(GT.onboarding_missing(new))
        self.assertIsNone(GT.origin(self.r))                                       # no Origin row: not blocked

    def test_init_creates_a_working_project(self):
        proj = self.r / "newapp"
        self.assertEqual(pls.main(["init", str(proj), "--approver", "Nam"]), 0)
        for f in ("CLAUDE.md", "pls.py", "environments.json", ".gitignore", "connections.example.json",
                  "design/slot-ledger.json", "traceability.json", "requirements/index.md", ".claude/framework.lock"):
            self.assertTrue((proj / f).exists(), f)
        self.assertIn("| Approvers | Nam (all gates) |", (proj / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("| Operators | dev: Nam; stg: Nam; prod: <customer operator> |", (proj / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertTrue((proj / ".claude/skills/pls-x-lifecycle/SKILL.md").exists())
        out = subprocess.run([sys.executable, "pls.py", "lint"], cwd=proj, capture_output=True, text=True)
        self.assertIn("L-ENV-01", out.stdout, out.stderr)                    # launcher runs; setup not finished yet
        ev = json.loads((proj / "environments.json").read_text(encoding="utf-8"))
        ev["envs"]["dev"]["parent_id"] = 500
        (proj / "environments.json").write_text(json.dumps(ev), encoding="utf-8")
        out = subprocess.run([sys.executable, "pls.py", "lint"], cwd=proj, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("0 issue(s)", out.stdout)
        os.chdir(proj)
        self.assertEqual(pls.main(["skills", "check"]), 0)
        with self.assertRaises(pls.Fail):                                     # never over an existing project
            pls.init_project(proj, "demo", "dev", None)

    def test_skills_check_finds_edited_and_outdated_copies(self):
        fw = self.r / "fw"
        (fw / "skills/pls-a").mkdir(parents=True)
        (fw / "skills/pls-a/SKILL.md").write_text("v1", encoding="utf-8")
        (fw / "skills/README.md").write_text("| `pls-a` | P1 | 0.1 | x |\n", encoding="utf-8")
        proj = self.r / "p"
        (proj / ".claude").mkdir(parents=True)
        (proj / ".claude/framework.lock").write_text("{}", encoding="utf-8")
        lock = pls.sync_skills(proj, fw)
        self.assertEqual(lock["skills"]["pls-a"]["version"], "0.1")
        self.assertEqual(pls.skills_check(proj, fw), [])
        (fw / "skills/pls-a/SKILL.md").write_text("v2", encoding="utf-8")
        self.assertIn("newer", pls.skills_check(proj, fw)[0])
        (proj / ".claude/skills/pls-a/SKILL.md").write_text("local edit", encoding="utf-8")
        self.assertIn("edited", pls.skills_check(proj, fw)[0])

    def test_coverage_checks_the_element_not_only_the_file(self):
        (self.r / "config/a").mkdir(parents=True)
        (self.r / "config/a/site.json").write_text(json.dumps(
            {"Columns": [{"ColumnName": "ClassA"}], "Processes": [{"Name": "ret"}], "Views": [{"Id": 2}]}), encoding="utf-8")
        ok = ["config/a/site.json#Columns[ClassA]", "config/a/site.json#Processes[ret]", "config/a/site.json#Views[2]",
              "config/a/site.json#Columns", "config/a/site.json"]
        for ref in ok:
            self.assertTrue(pls.config_path_exists(self.r, ref), ref)
        for ref in ["config/a/site.json#Columns[ClassB]", "config/a/site.json#Processes[x]", "config/a/site.json#Summaries",
                    "config/b/site.json"]:
            self.assertFalse(pls.config_path_exists(self.r, ref), ref)


    def test_release_id_is_used_once_and_drift_decision_must_exist(self):                 # S3
        exp = self.unpack_dev()
        (self.r / "design").mkdir(exist_ok=True)
        (self.r / "design/slot-ledger.json").write_text(json.dumps({"a": {}}), encoding="utf-8")
        (self.r / "releases/R-X").mkdir(parents=True)
        (self.r / "releases/R-X/plan.json").write_text(json.dumps({"status": "applied"}), encoding="utf-8")
        with self.assertRaises(pls.Fail):
            pls.release_plan(self.r, "dev", "R-X", {"a": str(exp)}, None)
        self.assertEqual(json.loads((self.r / "releases/R-X/plan.json").read_text(encoding="utf-8"))["status"], "applied")
        with self.assertRaises(pls.Fail):
            pls.release_plan(self.r, "dev", "R-Y", {"a": str(exp)}, "no-such-decision.md")

    def test_lint_skips_meta_only_sites_and_flags_unresolved_references(self):           # S5
        self.unpack_dev()
        (self.r / "config/newsite").mkdir()
        (self.r / "config/newsite/meta.json").write_text(json.dumps({"ReferenceType": "Issues"}), encoding="utf-8")
        site = json.loads((self.r / "config/a/site.json").read_text(encoding="utf-8"))
        site.setdefault("Processes", []).append({"Id": 9, "Name": "p", "Groups": ["${principal:nobody}"]})
        (self.r / "config/a/site.json").write_text(json.dumps(site), encoding="utf-8")
        rules = [i for i in pls.lint(self.r) if i["rule"] == "L-REF-02"]
        self.assertTrue(rules and "nobody" in rules[0]["msg"], rules)

    def test_script_bodies_keep_crlf(self):                                               # S7
        exp = self.r / "dev.json"
        exp.write_text(json.dumps(export(101, 102, "http://dev.internal", scripts=[
            {"Id": 1, "Name": "s1", "Body": "var a = 1;\r\nvar b = 2;\r\n", "BeforeCreate": True}])), encoding="utf-8")
        self.assertEqual(pls.main(["unpack", str(exp), "--env", "dev", "--site", "a"]), 0)
        self.assertEqual(pls.main(["diff", str(exp), "--env", "dev", "--site", "a"]), 0)

if __name__ == "__main__":
    unittest.main()
