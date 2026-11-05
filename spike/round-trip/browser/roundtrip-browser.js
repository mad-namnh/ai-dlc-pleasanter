// Round-trip runner executed in a browser logged in to Pleasanter.
// Paste into the DevTools console on the Pleasanter dev origin. NEVER run against production.
// Usage:      await spike.create(42410, 44562)   // copy site 42410 into folder 44562, diff
//             await spike.update(44563)          // change one label → restore → write twice, diff
//             await spike.pkg(42410, [42410,42411], 44562)  // copysitepackage without data, diff
const spike = (() => {
  const VOL = new Set(["ApiKey","SiteId","ParentId","InheritPermission","TenantId","Ver","Creator","Updator",
    "CreatedTime","UpdatedTime","Timestamp","ApiCountDate","ApiCount","LockedTime","LockedUser","ApiVersion"]);
  const NEST = new Set(["UpdatedTime","CreatedTime"]);
  const FIELDS = ["Title","Body","ReferenceType","SiteSettings"];
  const pls = async (path, body) => {
    const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json','X-Requested-With':'XMLHttpRequest'},
      body: JSON.stringify({ApiVersion:1.1, ...body})});
    return r.json();
  };
  const get = async id => (await pls(`/api/items/${id}/getsite`, {})).Response.Data;
  const norm = (o, d=0) => { const drop = d===0 ? new Set([...VOL,...NEST]) : NEST;
    if (Array.isArray(o)) return o.map(v=>norm(v,d+1));
    if (o && typeof o==='object') return Object.fromEntries(Object.keys(o).sort().filter(k=>!drop.has(k)).map(k=>[k,norm(o[k],d+1)]));
    return o; };
  const diff = (a,b,p='$',out=[]) => {
    if (a && b && typeof a==='object' && typeof b==='object' && !Array.isArray(a) && !Array.isArray(b)) {
      for (const k of [...new Set([...Object.keys(a),...Object.keys(b)])].sort()) {
        if (!(k in b)) out.push({path:`${p}.${k}`, kind:'removed', before:a[k]});
        else if (!(k in a)) out.push({path:`${p}.${k}`, kind:'added', after:b[k]});
        else diff(a[k],b[k],`${p}.${k}`,out); }
    } else if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length!==b.length) out.push({path:p, kind:'length', before:a.length, after:b.length});
      a.slice(0,Math.min(a.length,b.length)).forEach((x,i)=>diff(x,b[i],`${p}[${i}]`,out));
    } else if (JSON.stringify(a)!==JSON.stringify(b)) out.push({path:p, kind:'changed', before:a, after:b});
    return out; };
  const mask = v => { let s = typeof v==='string' ? v : JSON.stringify(v); if (s===undefined) return s;
    s = s.replace(/sk-ant-[A-Za-z0-9_\-]+/g,'[REDACTED]'); return s.length>90 ? s.slice(0,90)+'…' : s; };
  const show = d => d.map(x=>({path:x.path, kind:x.kind, before:mask(x.before), after:mask(x.after)}));
  const pick = o => Object.fromEntries(FIELDS.filter(f=>f in o).map(f=>[f,o[f]]));
  return {
    get, norm, diff,
    async create(src, folder) {
      const orig = await get(src);
      const c = await pls(`/api/items/${folder}/createsite`, {TenantId:1, ParentId:folder, InheritPermission:folder, ...pick(orig)});
      const d = diff(norm(orig), norm(await get(c.Id)));
      return {src, copy:c.Id, diffCount:d.length, diffs:show(d)};
    },
    async update(copy) {
      const base = await get(copy), baseN = norm(base);
      const mod = JSON.parse(JSON.stringify(base)); const col = mod.SiteSettings.Columns[0];
      const label = col.LabelText; col.LabelText = label + '_SPIKE';
      await pls(`/api/items/${copy}/updatesite`, pick(mod));
      const applied = (await get(copy)).SiteSettings.Columns.find(c=>c.ColumnName===col.ColumnName).LabelText === label+'_SPIKE';
      const iters = []; let prev = null;
      for (let i=1;i<=2;i++) { await pls(`/api/items/${copy}/updatesite`, pick(base));
        const cur = norm(await get(copy));
        iters.push({i, vsBase: diff(baseN,cur).length, vsPrev: prev ? diff(prev,cur).length : null}); prev = cur; }
      return {copy, changeApplied: applied, iters};
    },
    async pkg(anchor, sites, folder) {
      const r = await pls(`/api/items/${anchor}/copysitepackage`, {TargetSiteId:folder,
        SelectedSites: sites.map(s=>({SiteId:s, IncludeData:false})), IncludeSitePermission:false,
        IncludeRecordPermission:false, IncludeColumnPermission:false, IncludeNotifications:true, IncludeReminders:true});
      const map = JSON.parse(r.Response.Data); const out = [];
      for (const m of map) { const d = diff(norm(await get(m.OldSiteId)), norm(await get(m.NewSiteId)));
        out.push({orig:m.OldSiteId, pkg:m.NewSiteId, diffCount:d.length, diffs:show(d)}); }
      return out;
    },
  };
})();
