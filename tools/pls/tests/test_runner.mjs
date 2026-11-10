// Tests for the browser runner's release logic with a fake Pleasanter (node --test tools/pls/tests/)
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const src = readFileSync(new URL('../browser/pls-runner.js', import.meta.url), 'utf8');

function fakePleasanter(sites, failOn = null) {
  const calls = [];
  const fetch = async (path, opts) => {
    const [, id, op] = path.match(/\/api\/items\/(\d+)\/(\w+)/);
    calls.push(`${op} ${id}`);
    const site = sites[id];
    if (op === 'getsite') return {status: 200, text: async () => JSON.stringify({Response: {Data: site}})};
    if (op === 'updatesite') {
      if (failOn === Number(id)) return {status: 500, text: async () => '{"Message":"boom"}'};
      const body = JSON.parse(opts.body);
      Object.assign(site, {SiteSettings: body.SiteSettings, UpdatedTime: `${site.UpdatedTime}+`});
      return {status: 200, text: async () => '{"Message":"ok"}'};
    }
    throw new Error(`unexpected ${path}`);
  };
  const ctx = {fetch, console};
  vm.createContext(ctx);
  vm.runInContext(src + '\nthis.plsRunner = plsRunner;', ctx);
  return {runner: ctx.plsRunner, calls};
}

const plan = {
  env: 'dev', env_role: 'dev', sites: ['b', 'a'],
  per_site: {a: {site_id: 201, snapshot_updated_time: 'ta'}, b: {site_id: 202, snapshot_updated_time: 'tb'}},
  steps: [{op: 'updatesite', site: 'b', site_id: 202, payload_file: 'payload-b.json', expect_updated_time: 'tb'},
          {op: 'updatesite', site: 'a', site_id: 201, payload_file: 'payload-a.json', expect_updated_time: 'ta'}],
  rollback: [{op: 'updatesite', site: 'a', site_id: 201, payload_file: 'rollback-a.json'},
             {op: 'updatesite', site: 'b', site_id: 202, payload_file: 'rollback-b.json'}],
};
const pl = tag => ({Title: tag, ReferenceType: 'Results', SiteSettings: {tag}});
const files = {'payload-a.json': pl('new-a'), 'payload-b.json': pl('new-b'), 'rollback-a.json': pl('old-a'), 'rollback-b.json': pl('old-b')};
const sites = () => ({201: {UpdatedTime: 'ta', SiteSettings: {tag: 'old-a'}}, 202: {UpdatedTime: 'tb', SiteSettings: {tag: 'old-b'}}});

test('applies in plan order', async () => {
  const s = sites(); const {runner, calls} = fakePleasanter(s);
  const r = await runner.applyRelease(plan, files);
  assert.equal(r.status, 'applied-unverified');
  assert.deepEqual(calls.filter(c => c.startsWith('updatesite')), ['updatesite 202', 'updatesite 201']);
  assert.equal(s[201].SiteSettings.tag, 'new-a'); assert.equal(s[202].SiteSettings.tag, 'new-b');
});

test('failure on the second site restores both, in reverse order', async () => {
  const s = sites(); const {runner, calls} = fakePleasanter(s, 201);
  const r = await runner.applyRelease(plan, files);
  // site a refuses its restore too: a failed restore is never reported as rolled-back
  assert.equal(r.status, 'recovery-required'); assert.equal(r.failed_site, 'a'); assert.equal(JSON.stringify(r.failed_restores), '["a"]');   // array from the runner's vm context
  assert.deepEqual(calls.filter(c => c.startsWith('updatesite')), ['updatesite 202', 'updatesite 201', 'updatesite 201', 'updatesite 202']);
  assert.equal(s[202].SiteSettings.tag, 'old-b');
});

test('preflight refuses when a target changed since the plan; nothing written', async () => {
  const s = sites(); s[201].UpdatedTime = 'changed'; const {runner, calls} = fakePleasanter(s);
  const r = await runner.applyRelease(plan, files);
  assert.equal(r.status, 'refused');
  assert.equal(calls.filter(c => c.startsWith('updatesite')).length, 0);
});

test('writes only plans made for dev (ADR-0014 TB-7)', async () => {
  for (const role of ['stg', 'prod', undefined]) {
    const {runner, calls} = fakePleasanter(sites());
    const r = await runner.applyRelease({...plan, env_role: role}, files);
    assert.equal(r.status, 'refused'); assert.equal(calls.length, 0);
    await assert.rejects(runner.rollbackRelease({...plan, env_role: role}, files));
    assert.equal(calls.length, 0);
    const b = await runner.bulkUpsert({...plan, env_role: role}, 201, ['ClassA'], [{ClassA: 'x'}]);   // migrations too
    assert.equal(b.refused, true); assert.equal(calls.length, 0);
  }
});

test('refuses a step whose site id differs from per_site', async () => {
  const {runner, calls} = fakePleasanter(sites());
  const r = await runner.applyRelease({...plan, per_site: {a: {site_id: 201}, b: {site_id: 999}}}, files);
  assert.equal(r.status, 'refused'); assert.equal(calls.length, 0);
});

test('refuses steps that do not match the planned sites, files or snapshot (same rule as pls apply)', async () => {
  const extra = {op: 'updatesite', site: 'shared', site_id: 902, payload_file: 'payload-b.json', expect_updated_time: 'tb'};
  const bad = {
    'extra step': {...plan, steps: [...plan.steps, extra]},
    'other file': {...plan, steps: [{...plan.steps[0], payload_file: 'payload-a.json'}, plan.steps[1]]},
    'other snapshot': {...plan, steps: [{...plan.steps[0], expect_updated_time: 'later'}, plan.steps[1]]},
    'rollback not reversed': {...plan, rollback: [...plan.rollback].reverse()},
    'no per_site': {...plan, per_site: undefined},
  };
  for (const [label, p] of Object.entries(bad)) {
    const {runner, calls} = fakePleasanter(sites());
    const r = await runner.applyRelease(p, files);
    assert.equal(r.status, 'refused', label); assert.equal(calls.length, 0, label);
    await assert.rejects(runner.rollbackRelease(p, files), undefined, label);
    assert.equal(calls.length, 0, label);
  }
});

test('refuses when a payload or rollback file is missing', async () => {
  const {runner, calls} = fakePleasanter(sites());
  const r = await runner.applyRelease(plan, {...files, 'rollback-b.json': undefined});
  assert.equal(r.status, 'refused'); assert.equal(calls.length, 0);
});

test('backupRecords pages through every record', async () => {
  const records = Array.from({length: 5}, (_, i) => ({ResultId: i + 1}));
  const calls = [];
  const fetch = async (path, opts) => {
    const b = JSON.parse(opts.body); calls.push(b.Offset);
    return {status: 200, text: async () => JSON.stringify({Response: {TotalCount: 5, Data: records.slice(b.Offset, b.Offset + b.PageSize)}})};
  };
  const ctx = {fetch, console}; vm.createContext(ctx);
  vm.runInContext(src + '\nthis.plsRunner = plsRunner;', ctx);
  const r = await ctx.plsRunner.backupRecords(9, 2);
  assert.equal(r.count, 5); assert.deepEqual(calls, [0, 2, 4]);
});

test('runTests: create on another site with $var, update/delete with expected HTTP', async () => {
  const recs = {}; let next = 100; const calls = [];
  const fetch = async (path, opts) => {
    const [, id, op] = path.match(/\/api\/items\/(\d+)\/(\w+)/); const body = opts && opts.body ? JSON.parse(opts.body) : {};
    calls.push(`${op} ${id}`);
    const res = (status, obj) => ({status, text: async () => JSON.stringify(obj)});
    if (op === 'getsite') return res(200, {Response: {Data: {SiteSettings: {Processes: []}}}});
    if (op === 'create') { const nid = next++; recs[nid] = {site: id, ...body}; return res(200, {Id: nid}); }
    if (op === 'update') return Number(id) === 101 ? res(403, {Message: 'no'}) : res(200, {});
    if (op === 'delete') return res(200, {});
    if (op === 'get') return res(200, {Response: {Data: [{ClassHash: recs[id].ClassHash}]}});
  };
  const ctx = {fetch, console, DOMParser: class {}}; vm.createContext(ctx);
  vm.runInContext(src + '\nthis.plsRunner = plsRunner;', ctx);
  const out = await ctx.plsRunner.runTests(1, [{id: 'T', steps: [
    {op: 'create', save: 'p', data: {Title: 'parent'}},
    {op: 'create', site: 2, save: 'c', data: {ClassHash: {ClassA: '$p'}}},
    {op: 'get', record: '$c', expect: {'ClassHash.ClassA': '100'}},
    {op: 'update', record: '$c', data: {NumHash: {NumA: 1}}, expectHttp: 403},
    {op: 'delete', record: '$p'}]}], 'dev');
  assert.equal(out.tests[0].status, 'pass', JSON.stringify(out.tests[0].log));
  assert.ok(calls.includes('create 2'));
});

// One fake for the test-spec probes: process "approve" answers with `execStatus`; every call is recorded.
function testRunner(execStatus = 200) {
  const calls = []; let next = 100;
  const fetch = async path => {
    const [, id, op] = path.match(/\/api\/items\/(\d+)\/(\w+)/);
    calls.push(`${op} ${id}`);
    const res = (status, obj) => ({status, text: async () => JSON.stringify(obj)});
    if (op === 'getsite') return res(200, {Response: {Data: {SiteSettings: {Processes: [{Id: 1, Name: 'approve'}]}}}});
    if (op === 'create') return res(200, {Id: next++});
    if (op === 'update') return res(execStatus, {});
    return res(200, {});
  };
  const ctx = {fetch, console, DOMParser: class {}}; vm.createContext(ctx);
  vm.runInContext(src + '\nthis.plsRunner = plsRunner;', ctx);
  return {runner: ctx.plsRunner, calls};
}
const execSpec = extra => [{id: 'T', steps: [{op: 'create', save: 'r', data: {}}, {op: 'exec', record: '$r', process: 'approve', ...extra}]}];

test('runTests: exec answered with an unexpected status is a failure, as in pls test', async () => {
  const failed = await testRunner(500).runner.runTests(1, execSpec({}), 'dev');
  assert.equal(failed.tests[0].status, 'fail', JSON.stringify(failed.tests[0].log));
  const refused = await testRunner(403).runner.runTests(1, execSpec({expectHttp: 403}), 'dev');
  assert.equal(refused.tests[0].status, 'pass');
  const ok = await testRunner(200).runner.runTests(1, execSpec({}), 'dev');
  assert.equal(ok.tests[0].status, 'pass');
});

test('runTests: a spec or step with as_key is refused unsent — the runner cannot switch users', async () => {
  for (const spec of [{id: 'T', as_key: 'staff', steps: [{op: 'create', expectHttp: 403, data: {}}]},
                      {id: 'T', steps: [{op: 'create', save: 'r', data: {}}, {op: 'delete', as_key: 'staff', record: '$r', expectHttp: 403}]}]) {
    const {runner, calls} = testRunner();
    const out = await runner.runTests(1, [spec], 'dev');
    assert.equal(out.tests[0].status, 'error', JSON.stringify(out.tests[0].log));
    assert.match(out.tests[0].log.join(' '), /as_key staff/);
    assert.deepEqual(calls.filter(c => !c.startsWith('getsite')), []);
  }
});

test('runTests: results say which transport ran them and as whom', async () => {
  const out = await testRunner().runner.runTests(1, execSpec({}), 'dev');
  assert.equal(out.transport, 'browser');
  assert.equal(out.tests[0].as, 'session-user');
});

test('applyRelease: a restore that throws does not stop the other restores', async () => {
  const live = sites(); const calls = []; let updates = 0;
  const fetch = async (path, opts) => {
    const [, id, op] = path.match(/\/api\/items\/(\d+)\/(\w+)/);
    calls.push(`${op} ${id}`);
    if (op === 'getsite') return {status: 200, text: async () => JSON.stringify({Response: {Data: live[id]}})};
    updates += 1;
    if (updates === 2) return {status: 500, text: async () => '{"Message":"boom"}'};     // apply of a fails
    if (updates === 3) throw new Error('network down');                                 // restore of a throws
    live[id].SiteSettings = JSON.parse(opts.body).SiteSettings;
    return {status: 200, text: async () => '{}'};
  };
  const ctx = {fetch, console}; vm.createContext(ctx);
  vm.runInContext(src + '\nthis.plsRunner = plsRunner;', ctx);
  const out = await ctx.plsRunner.applyRelease(plan, files);
  assert.equal(out.status, 'recovery-required');
  assert.deepEqual([...out.failed_restores], ['a']);
  assert.equal(live[202].SiteSettings.tag, 'old-b');                                    // b was still restored
});
