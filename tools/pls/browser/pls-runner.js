// pls browser runner — transport between the pls toolchain (files) and a Pleasanter environment.
// Runs in a browser tab that is logged in to the TARGET Pleasanter (session auth, no API key).
// Only for dev, driven by a person — agents do not use it (ADR-0014 TB-7): applyRelease, rollbackRelease,
// bootstrapSites and bulkUpsert refuse a plan whose env_role (written by pls release-plan / bootstrap-plan) is not
// "dev"; stg and prod go through pls over HTTP (migrations: `pls migrate`).
//
//   await plsRunner.exportSite(siteId)                 → getsite response (save as export JSON)
//   await plsRunner.apply(siteId, payload)             → updatesite with a COMPLETE payload (I2)
//   await plsRunner.runTests(siteId, specs, envName)   → results JSON for tests/results/
//     ops: create (expectHttp for refusals), exec, update, delete, get, list (view contains/excludes), editPage, siteConfig
//     runs as the logged-in user: specs or steps with as_key are refused (role tests run with `pls test`);
//     results carry transport: "browser" and as: "session-user". Differences from pls test: ADR-0008
//   await plsRunner.applyRelease(plan, files)          → multi-site release (pls release-plan): preflight, ordered apply,
//                                                        automatic reverse-order restore on failure (A3)
//   await plsRunner.rollbackRelease(plan, files, sites) → restore the given sites (default: all) in reverse order
//   files = {"payload-<site>.json": {...}, "rollback-<site>.json": {...}} — content of the release folder
//   await plsRunner.bootstrapSites(plan)           → new sites (ADR-0007): createsite skeletons from releases/R/bootstrap.json;
//                                                        returns {site: newId} for `pls bind`; never deletes anything
//   await plsRunner.backupRecords(siteId)              → every record of a site (paged), for migration/backup/ (ADR-0004)
//   await plsRunner.bulkUpsert(plan, siteId, keys, data) → /bulkupsert for a dev plan; records matched by `keys` are
//                                                        updated, others created. Guarded runs: `pls migrate`
//     API updates do not create record versions (Ver stays 1 — D14), so the backup is the only way back.
var plsRunner = (() => {
  const call = async (path, body, method = 'POST') => {
    const r = await fetch(path, {method, headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
      body: method === 'POST' ? JSON.stringify({ApiVersion: 1.1, ...(body || {})}) : undefined});
    const text = await r.text();
    let json = null; try { json = JSON.parse(text); } catch (e) { /* not JSON */ }
    return {http: r.status, json, text};
  };
  // The runner has no environments.json and no gate records, so it writes only plans made for dev (ADR-0014 TB-7).
  const planRefusal = plan => {
    if (!plan || plan.env_role !== 'dev') {
      return `plan for ${plan && plan.env} has env_role ${JSON.stringify(plan && plan.env_role)}: the browser runner ` +
        'writes only dev (ADR-0014 TB-7); use pls apply / pls bootstrap over HTTP, or re-plan with a current pls';
    }
    return null;
  };
  // Same rule as pls plan_steps_problem: the writes use steps / rollback, the checks read per_site; both must name the
  // same sites, ids and files, each site once, in the planned order (rollback reversed).
  const stepsRefusal = plan => {
    const sites = plan.sites, per = plan.per_site;
    if (!Array.isArray(sites) || !sites.length || !per || Object.keys(per).sort().join('\u0000') !== [...sites].sort().join('\u0000')) {
      return 'plan sites and per_site do not name the same sites — re-plan';
    }
    for (const [part, key, prefix, order] of [['steps', 'payload_file', 'payload', sites],
                                              ['rollback', 'rollback_file', 'rollback', [...sites].reverse()]]) {
      const st = plan[part];
      if (!Array.isArray(st) || st.map(x => x && x.site).join('\u0000') !== order.join('\u0000')) {
        return `plan ${part} do not list exactly the sites ${order.join(', ')} — re-plan`;
      }
      for (const x of st) {
        const ps = per[x.site], file = ps[key] || `${prefix}-${x.site}.json`;
        if (x.op !== 'updatesite' || x.site_id !== ps.site_id || x.payload_file !== file) {
          return `plan ${part} entry for ${x.site} does not match per_site (site id, file or op) — re-plan`;
        }
        if (part === 'steps' && 'snapshot_updated_time' in ps && x.expect_updated_time !== ps.snapshot_updated_time) {
          return `plan steps entry for ${x.site}: expect_updated_time is not the planned snapshot's — re-plan`;
        }
      }
    }
    return null;
  };
  const exportSite = async id => {
    const r = await call(`/api/items/${id}/getsite`);
    if (r.http !== 200) throw new Error(`getsite ${id}: HTTP ${r.http}`);
    return r.json;
  };
  const apply = async (id, payload) => {
    for (const k of ['Title', 'ReferenceType', 'SiteSettings']) if (!(k in payload)) throw new Error(`payload missing ${k} (I2)`);
    const r = await call(`/api/items/${id}/updatesite`, payload);
    return {http: r.http, message: r.json && r.json.Message};
  };
  const getPath = (o, p) => p.split('.').reduce((x, k) => (x == null ? x : x[k]), o);
  const check = (actual, expected) => expected === '!empty'
    ? actual != null && actual !== '' && !String(actual).startsWith('1899-12-30')
    : JSON.stringify(actual) === JSON.stringify(expected);

  const runTests = async (siteId, specs, envName) => {
    const site = (await exportSite(siteId)).Response.Data;
    const procs = Object.fromEntries((site.SiteSettings.Processes || []).map(p => [p.Name, p]));
    const out = [];
    for (const spec of specs) {
      const vars = {...(spec.vars || {})}, log = []; let status = 'pass';   // spec.vars: fixtures from an earlier run
      // "$name" anywhere in step data → id of the record saved as `name` earlier in this test
      const subst = v => typeof v === 'string' && /^\$\w+$/.test(v) && v.slice(1) in vars ? String(vars[v.slice(1)])
        : Array.isArray(v) ? v.map(subst) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, subst(x)])) : v;
      try {
        // Every request here is sent as the logged-in user. A spec that names a role's key would run as that user
        // (usually an administrator) and its expected refusals could pass or delete fixtures: refuse it unsent.
        const keys = [spec.as_key, ...spec.steps.map(st => st.as_key)].filter(Boolean);
        if (keys.length) {
          throw new Error(`as_key ${[...new Set(keys)].join(', ')}: the browser runner cannot switch users — ` +
            'run this spec with pls test over HTTP (ADR-0008); nothing sent');
        }
        for (const st of spec.steps) {
          const rid = st.record ? vars[st.record.replace('$', '')] : null;
          if (st.op === 'create') {
            const r = await call(`/api/items/${st.site || siteId}/create`, subst(st.data));
            if (st.expectHttp) {                 // negative create: must be refused with this status
              const ok = r.http === st.expectHttp;
              log.push(`${ok ? 'ok ' : 'NG '} create refused → HTTP ${r.http} (expected ${st.expectHttp})${r.json && r.json.Message ? ' ' + r.json.Message : ''}`);
              if (!ok) status = 'fail';
              continue;
            }
            if (!r.json || !r.json.Id) throw new Error(`create failed: HTTP ${r.http} ${r.text.slice(0, 200)}`);
            vars[st.save] = r.json.Id; log.push(`create → ${r.json.Id}`);
          } else if (st.op === 'exec') {
            const p = procs[st.process];
            if (!p) throw new Error(`process '${st.process}' not found`);
            const r = await call(`/api/items/${rid}/update`, {ProcessId: p.Id, ...(st.data || {})});
            log.push(`exec ${st.process}(Id ${p.Id}) → HTTP ${r.http}`);
            const want = st.expectHttp || 200;   // same rule as pls test: an unexpected status is never a pass
            if (r.http !== want) { status = 'fail'; log.push(`expected HTTP ${want}`); }
          } else if (st.op === 'update' || st.op === 'delete') {
            const r = await call(`/api/items/${rid}/${st.op}`, st.op === 'update' ? subst(st.data || {}) : undefined);
            log.push(`${st.op} ${rid} → HTTP ${r.http}`);
            const want = st.expectHttp || 200;
            if (r.http !== want) { status = 'fail'; log.push(`expected HTTP ${want}`); }
          } else if (st.op === 'get') {
            const r = await call(`/api/items/${rid}/get`);
            if (st.expectHttp) {
              const ok = r.http === st.expectHttp;
              log.push(`${ok ? 'ok ' : 'NG '} get ${rid} → HTTP ${r.http} (expected ${st.expectHttp})`);
              if (!ok) status = 'fail';
              continue;
            }
            const rec = r.json.Response.Data[0];
            for (const [path, exp0] of Object.entries(st.expect)) {
              const act = getPath(rec, path), exp = subst(exp0);   // "$name" in expectations = saved record id
              const ok = check(act, exp);
              log.push(`${ok ? 'ok ' : 'NG '} ${path} = ${JSON.stringify(act)} (expected ${JSON.stringify(exp)})`);
              if (!ok) status = 'fail';
            }
          } else if (st.op === 'list') {         // records returned by a view: {site, view, contains:[$x], excludes:[$y]}
            const r = await call(`/api/items/${st.site || siteId}/get`, {View: st.view || {}});
            if (st.expectHttp) {
              const ok = r.http === st.expectHttp;
              log.push(`${ok ? 'ok ' : 'NG '} list → HTTP ${r.http} (expected ${st.expectHttp})`);
              if (!ok) status = 'fail';
              continue;
            }
            const ids = new Set(((r.json && r.json.Response && r.json.Response.Data) || []).map(x => String(x.IssueId || x.ResultId)));
            for (const [want, list] of [[true, st.contains || []], [false, st.excludes || []]]) {
              for (const v of list) {
                const id = String(subst(v)); const ok = ids.has(id) === want;
                log.push(`${ok ? 'ok ' : 'NG '} ${id} ${want ? 'in' : 'not in'} view`);
                if (!ok) status = 'fail';
              }
            }
          } else if (st.op === 'editPage') {
            const html = await fetch(`/items/${rid}/edit`).then(r => r.text());
            const doc = new DOMParser().parseFromString(html, 'text/html');
            const present = [...doc.querySelectorAll('button')].some(b => b.textContent.trim() === st.button);
            const ok = present === st.present;
            log.push(`${ok ? 'ok ' : 'NG '} button '${st.button}' present=${present} (expected ${st.present})`);
            if (!ok) status = 'fail';
          } else if (st.op === 'siteConfig') {
            for (const [path, exp] of Object.entries(st.expect)) {
              const act = getPath(site.SiteSettings, path);
              const ok = exp && exp.contains ? String(act).includes(exp.contains) : check(act, exp);
              log.push(`${ok ? 'ok ' : 'NG '} SiteSettings.${path} = ${JSON.stringify(act)} (expected ${JSON.stringify(exp)})`);
              if (!ok) status = 'fail';
            }
          } else throw new Error(`unknown op ${st.op}`);
        }
      } catch (e) { status = 'error'; log.push(String(e.message || e)); }
      out.push({id: spec.id, reqs: spec.reqs, title: spec.title, as: 'session-user', status, log});
    }
    return {env: envName, site_id: siteId, transport: 'browser', executed_at: new Date().toISOString(), tests: out};
  };
  // Restore in rollback order; one failing restore never stops the others. failed = sites not answered with 200.
  const restoreSites = async (plan, files, sites) => {
    const only = sites ? new Set(sites) : null;
    const log = [], failed = [];
    for (const step of plan.rollback) {
      if (only && !only.has(step.site)) continue;
      let r;
      try { r = await apply(step.site_id, files[step.payload_file]); } catch (e) { r = {http: `error ${e.message || e}`}; }
      log.push(`restore ${step.site} (${step.site_id}) → HTTP ${r.http}`);
      if (r.http !== 200) failed.push(step.site);
    }
    return {log, failed};
  };
  const rollbackRelease = async (plan, files, sites) => {
    const no = planRefusal(plan) || stepsRefusal(plan);
    if (no) throw new Error(no);
    return (await restoreSites(plan, files, sites)).log;
  };

  const applyRelease = async (plan, files) => {
    const no = planRefusal(plan) || stepsRefusal(plan);
    if (no) return {status: 'refused', log: [no]};
    const log = [];
    for (const step of plan.steps) {           // files present before anything is written
      if (!files[step.payload_file]) return {status: 'refused', log: [`missing ${step.payload_file}`]};
    }
    for (const step of plan.rollback) {
      if (!files[step.payload_file]) return {status: 'refused', log: [`missing ${step.payload_file}`]};
    }
    for (const step of plan.steps) {           // preflight: nobody changed a target since the plan
      const live = (await exportSite(step.site_id)).Response.Data;
      if (live.UpdatedTime !== step.expect_updated_time) {
        return {status: 'refused', log: [...log, `${step.site}: UpdatedTime ${live.UpdatedTime} ≠ plan ${step.expect_updated_time} — re-plan`]};
      }
      log.push(`preflight ${step.site} ok`);
    }
    const touched = [];
    for (const step of plan.steps) {
      touched.push(step.site);                 // a failed updatesite may still have changed the site → restore it too
      let r;
      try { r = await apply(step.site_id, files[step.payload_file]); } catch (e) { r = {http: 0, message: String(e)}; }
      log.push(`apply ${step.site} (${step.site_id}) → HTTP ${r.http}`);
      if (r.http !== 200) {
        // never "rolled-back" after a failed restore; the person exports every site and runs pls mark-applied,
        // which records what the sites really hold
        const {log: restored, failed} = await restoreSites(plan, files, touched);
        return {status: failed.length ? 'recovery-required' : 'rolled-back', failed_site: step.site, touched,
                failed_restores: failed, log: [...log, ...restored]};
      }
    }
    return {status: 'applied-unverified', log: [...log, 'next: export every site and run `pls mark-applied <release> --export site=file …`']};
  };

  const bootstrapSites = async plan => {
    const created = {}, log = [];
    const no = planRefusal(plan);
    if (no) return {status: 'refused', created, log: [no]};
    const parent = await call(`/api/items/${plan.parent_id}/getsite`);
    if (parent.http !== 200 || !parent.json || parent.json.Response.Data.ReferenceType !== 'Sites') {
      return {status: 'refused', created, log: [`parent ${plan.parent_id} is not a reachable folder (HTTP ${parent.http})`]};
    }
    for (const st of plan.steps) {
      if (st.op !== 'createsite' || st.parent_id !== plan.parent_id) return {status: 'refused', created, log: [...log, `bad step ${st.site}`]};
      const r = await call(`/api/items/${st.parent_id}/createsite`, st.payload);
      const id = r.json && (r.json.Id || (r.json.Response && r.json.Response.Id));
      log.push(`createsite ${st.site} under ${st.parent_id} → HTTP ${r.http}${id ? ` id ${id}` : ''}`);
      if (r.http !== 200 || !id) return {status: 'partial', created, log: [...log, r.text.slice(0, 200), 'stop: bind what was created, then decide']};
      created[st.site] = id;
    }
    return {status: 'created', created, log: [...log, `next: pls bind --env ${plan.env} --release ${plan.release} ` +
      Object.entries(created).map(([k, v]) => `--created ${k}=${v}`).join(' ')]};
  };

  const backupRecords = async (siteId, pageSize = 200) => {
    const all = [];
    for (let offset = 0; ; offset += pageSize) {
      const r = await call(`/api/items/${siteId}/get`, {Offset: offset, PageSize: pageSize, View: {ColumnSorterHash: {ResultId: 'asc'}}});
      if (r.http !== 200 || !r.json) throw new Error(`get ${siteId} offset ${offset}: HTTP ${r.http}`);
      const page = r.json.Response.Data || [];
      all.push(...page);
      const total = r.json.Response.TotalCount;
      if (page.length === 0 || (total != null && all.length >= total) || page.length < pageSize) break;
    }
    return {site_id: siteId, taken_at: new Date().toISOString(), count: all.length, records: all};
  };

  const bulkUpsert = async (plan, siteId, keys, data) => {
    const no = planRefusal(plan);
    if (no) return {http: null, message: no, refused: true};
    const r = await call(`/api/items/${siteId}/bulkupsert`, {Keys: keys, Data: data});
    return {http: r.http, message: r.json && r.json.Message};
  };

  return {exportSite, apply, runTests, applyRelease, rollbackRelease, bootstrapSites, backupRecords, bulkUpsert};
})();
