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
  env: 'dev', env_role: 'dev',
  steps: [{site: 'b', site_id: 202, payload_file: 'payload-b.json', expect_updated_time: 'tb'},
          {site: 'a', site_id: 201, payload_file: 'payload-a.json', expect_updated_time: 'ta'}],
  rollback: [{site: 'a', site_id: 201, payload_file: 'rollback-a.json'},
             {site: 'b', site_id: 202, payload_file: 'rollback-b.json'}],
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
  }
});

test('refuses a step whose site id differs from per_site', async () => {
  const {runner, calls} = fakePleasanter(sites());
  const r = await runner.applyRelease({...plan, per_site: {a: {site_id: 201}, b: {site_id: 999}}}, files);
  assert.equal(r.status, 'refused'); assert.equal(calls.length, 0);
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
