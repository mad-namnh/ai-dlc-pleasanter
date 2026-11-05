// pls browser runner — transport between the pls toolchain (files) and a Pleasanter environment.
// Runs in a browser tab that is logged in to the TARGET Pleasanter (session auth, no API key).
// Only for dev/stg-like environments driven by a person; production uses the customer-side runner (ADR-0003).
//
//   await plsRunner.exportSite(siteId)                 → getsite response (save as export JSON)
//   await plsRunner.apply(siteId, payload)             → updatesite with a COMPLETE payload (I2)
//   await plsRunner.runTests(siteId, specs, envName)   → results JSON for tests/results/
//   await plsRunner.applyRelease(plan, files)          → multi-site release (pls release-plan): preflight, ordered apply,
//                                                        automatic reverse-order restore on failure (A3)
//   await plsRunner.rollbackRelease(plan, files, sites) → restore the given sites (default: all) in reverse order
//   files = {"payload-<site>.json": {...}, "rollback-<site>.json": {...}} — content of the release folder
//   await plsRunner.backupRecords(siteId)              → every record of a site (paged), for migration/backup/ (ADR-0004)
//   await plsRunner.bulkUpsert(siteId, keys, data)     → /bulkupsert; records matched by `keys` are updated, others created
//     API updates do not create record versions (Ver stays 1 — D14), so the backup is the only way back.
var plsRunner = (() => {
  const call = async (path, body, method = 'POST') => {
    const r = await fetch(path, {method, headers: {'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest'},
      body: method === 'POST' ? JSON.stringify({ApiVersion: 1.1, ...(body || {})}) : undefined});
    const text = await r.text();
    let json = null; try { json = JSON.parse(text); } catch (e) { /* not JSON */ }
    return {http: r.status, json, text};
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
      const vars = {}, log = []; let status = 'pass';
      try {
        for (const st of spec.steps) {
          const rid = st.record ? vars[st.record.replace('$', '')] : null;
          if (st.op === 'create') {
            const r = await call(`/api/items/${siteId}/create`, st.data);
            if (!r.json || !r.json.Id) throw new Error(`create failed: HTTP ${r.http} ${r.text.slice(0, 200)}`);
            vars[st.save] = r.json.Id; log.push(`create → ${r.json.Id}`);
          } else if (st.op === 'exec') {
            const p = procs[st.process];
            if (!p) throw new Error(`process '${st.process}' not found`);
            const r = await call(`/api/items/${rid}/update`, {ProcessId: p.Id, ...(st.data || {})});
            log.push(`exec ${st.process}(Id ${p.Id}) → HTTP ${r.http}`);
            if (st.expectHttp && r.http !== st.expectHttp) { status = 'fail'; log.push(`expected HTTP ${st.expectHttp}`); }
          } else if (st.op === 'get') {
            const r = await call(`/api/items/${rid}/get`);
            const rec = r.json.Response.Data[0];
            for (const [path, exp] of Object.entries(st.expect)) {
              const act = getPath(rec, path);
              const ok = check(act, exp);
              log.push(`${ok ? 'ok ' : 'NG '} ${path} = ${JSON.stringify(act)} (expected ${JSON.stringify(exp)})`);
              if (!ok) status = 'fail';
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
      out.push({id: spec.id, reqs: spec.reqs, title: spec.title, status, log});
    }
    return {env: envName, site_id: siteId, executed_at: new Date().toISOString(), tests: out};
  };
  const rollbackRelease = async (plan, files, sites) => {
    const only = sites ? new Set(sites) : null;
    const log = [];
    for (const step of plan.rollback) {
      if (only && !only.has(step.site)) continue;
      const r = await apply(step.site_id, files[step.payload_file]);
      log.push(`restore ${step.site} (${step.site_id}) → HTTP ${r.http}`);
    }
    return log;
  };

  const applyRelease = async (plan, files) => {
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
        const restored = await rollbackRelease(plan, files, touched);
        return {status: 'rolled-back', failed_site: step.site, log: [...log, ...restored]};
      }
    }
    return {status: 'applied-unverified', log: [...log, 'next: export every site and run `pls mark-applied <release> --export site=file …`']};
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

  const bulkUpsert = async (siteId, keys, data) => {
    const r = await call(`/api/items/${siteId}/bulkupsert`, {Keys: keys, Data: data});
    return {http: r.http, message: r.json && r.json.Message};
  };

  return {exportSite, apply, runTests, applyRelease, rollbackRelease, backupRecords, bulkUpsert};
})();
