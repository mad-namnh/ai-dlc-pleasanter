// pls browser runner — transport between the pls toolchain (files) and a Pleasanter environment.
// Runs in a browser tab that is logged in to the TARGET Pleasanter (session auth, no API key).
// Only for dev/stg-like environments driven by a person; production uses the customer-side runner (ADR-0003).
//
//   await plsRunner.exportSite(siteId)                 → getsite response (save as export JSON)
//   await plsRunner.apply(siteId, payload)             → updatesite with a COMPLETE payload (I2)
//   await plsRunner.runTests(siteId, specs, envName)   → results JSON for tests/results/
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
  return {exportSite, apply, runTests};
})();
