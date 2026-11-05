import test from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { calculate, LIMITS, exportOBJ } from '../plugins/solid-mesh-workbench/solid-mesh-workbench/engine/core.mjs';

const box = (size = [20, 20, 20], translate = [0, 0, 0]) => ({ kind: 'box', size, translate });
const project = (operation = 'union', a = box(), b = box([20, 20, 20], [10, 0, 0])) => ({ schema: 'solid-mesh-workbench/v1', units: 'mm', operation, a, b });
const clone = value => JSON.parse(JSON.stringify(value));
const tetra = { kind: 'mesh', positions: [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], triangles: [0, 2, 1, 0, 1, 3, 0, 3, 2, 1, 2, 3], mergeFromVert: [], mergeToVert: [] };
const near = (actual, expected, tolerance = 1e-6) => assert.ok(Math.abs(actual - expected) <= tolerance * Math.max(1, Math.abs(expected)), `${actual} != ${expected}`);
async function good(input) { const result = await calculate(input); assert.equal(result.ok, true, result.error); return result; }
async function bad(input, pattern) { const result = await calculate(input); assert.equal(result.ok, false); assert.match(result.error, pattern ?? /[\u4e00-\u9fff]/); return result; }

// This independent calculation consumes only exported v/f records, not engine metrics.
function independentOBJ(text) {
  const vertices = [], triangles = [], edges = new Map(); let volume = 0, area = 0;
  for (const line of text.trim().split('\n')) {
    const [kind, ...parts] = line.split(/\s+/);
    if (kind === 'v') vertices.push(parts.map(Number));
    if (kind === 'f') triangles.push(parts.map(x => Number(x) - 1));
  }
  for (const ids of triangles) {
    const [a, b, c] = ids.map(x => vertices[x]);
    const cross = (u, v) => [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    volume += a.reduce((sum, value, i) => sum + value * cross(b, c)[i], 0) / 6;
    area += Math.hypot(...cross(b.map((x, i) => x - a[i]), c.map((x, i) => x - a[i]))) / 2;
    for (let i = 0; i < 3; i++) {
      const a = ids[i], b = ids[(i + 1) % 3], key = [Math.min(a, b), Math.max(a, b)].join(',');
      const old = edges.get(key) ?? { count: 0, direction: 0 };
      old.count++; old.direction += a < b ? 1 : -1; edges.set(key, old);
    }
  }
  assert.ok([...edges.values()].every(x => x.count === 2 && x.direction === 0), 'export must have opposite closed edge pairs');
  return { volume, area, vertices: vertices.length, triangles: triangles.length };
}

for (const [operation, volume, area, min, max] of [
  ['union', 12000, 3200, [0, 0, 0], [30, 20, 20]],
  ['difference', 4000, 1600, [0, 0, 0], [10, 20, 20]],
  ['intersection', 4000, 1600, [10, 0, 0], [20, 20, 20]],
]) test(`analytic overlapping cubes: ${operation}`, async () => {
  const result = await good(project(operation));
  near(result.metrics.volume_mm3, volume); near(result.metrics.area_mm2, area);
  assert.deepEqual(result.metrics.bounds, { min, max });
  const independent = independentOBJ(result.obj);
  near(independent.volume, volume); near(independent.area, area);
  assert.equal(independent.triangles, result.metrics.triangles);
});

test('saved canonical project survives JSON and a fresh computation', async () => {
  const first = await good(project());
  assert.equal(first.project.a.kind, 'mesh');
  const restored = await good(JSON.parse(JSON.stringify(first.project)));
  assert.deepEqual(restored.metrics, first.metrics);
  assert.deepEqual(restored.project, first.project);
  assert.deepEqual(restored.mesh, first.mesh);
});

test('decimal primitive geometry is accepted at project precision before first calculation', async () => {
  for (const shape of [box([0.1, 0.3, 0.7]), { kind: 'cylinder', radius: 0.3, height: 0.7, segments: 16, rotate: [10, 20, 30] }]) {
    const first = await good(project('difference', shape, box([1, 1, 1], [10, 10, 10])));
    const restored = await good(clone(first.project));
    assert.deepEqual(restored.metrics, first.metrics);
    assert.deepEqual(restored.mesh, first.mesh);
  }
});

test('exported OBJ reimports with preserved geometry and topology', async () => {
  const first = await good(project());
  const restored = await good(project('intersection', { kind: 'obj', text: first.obj }, box([100, 100, 100], [-20, -20, -20])));
  near(restored.metrics.volume_mm3, first.metrics.volume_mm3);
  near(independentOBJ(restored.obj).area, first.metrics.area_mm2);
});

test('explicit merge indices preserve duplicated property-vertex topology', async () => {
  const split = { kind: 'mesh', positions: [], triangles: [], mergeFromVert: [], mergeToVert: [] }, first = new Map();
  tetra.triangles.forEach((id, i) => {
    split.positions.push(...tetra.positions.slice(id * 3, id * 3 + 3)); split.triangles.push(i);
    if (first.has(id)) { split.mergeFromVert.push(i); split.mergeToVert.push(first.get(id)); } else first.set(id, i);
  });
  const result = await good(project('difference', split, box([1, 1, 1], [10, 10, 10])));
  near(result.metrics.volume_mm3, 1 / 6);
  near(independentOBJ(result.obj).volume, 1 / 6);
  await bad(project('union', { ...split, mergeFromVert: [], mergeToVert: [] }), /封闭/);
  const invalid = clone(split); invalid.mergeToVert[0] = 1;
  await bad(project('union', invalid), /坐标完全相同/);
});

test('rotation in degrees occurs at origin before translation', async () => {
  const a = { ...box([2, 3, 4], [10, 0, 0]), rotate: [0, 0, 90] };
  const result = await good(project('difference', a, box([1, 1, 1], [100, 100, 100])));
  near(result.metrics.volume_mm3, 24); assert.deepEqual(result.metrics.bounds, { min: [7, 0, 0], max: [10, 2, 4] });
});

test('cylinder metrics match regular polygon prism, not ideal curved cylinder', async () => {
  const segments = 32, radius = 5, height = 10;
  const result = await good(project('difference', { kind: 'cylinder', radius, height, segments }, box([1, 1, 1], [100, 100, 100])));
  const cap = segments * radius ** 2 * Math.sin(2 * Math.PI / segments) / 2;
  near(result.metrics.volume_mm3, cap * height);
  near(result.metrics.area_mm2, 2 * cap + 2 * segments * radius * Math.sin(Math.PI / segments) * height);
});

test('empty intersection and identical subtraction are successful empty results', async () => {
  for (const input of [project('intersection', box(), box([1, 1, 1], [100, 0, 0])), project('difference', box(), box())]) {
    const result = await good(input);
    assert.deepEqual(result.metrics, { volume_mm3: 0, area_mm2: 0, bounds: null, triangles: 0, vertices: 0, empty: true });
    assert.deepEqual(result.mesh.positions, []); assert.ok(!result.obj.includes('\nv '));
  }
});

test('strict OBJ rejects material, script, external, polygon and malformed syntax', async () => {
  const valid = exportOBJ(tetra);
  for (const line of ['mtllib evil.mtl', 'usemtl x', 'vn 0 0 1', 'vt 0 0', 'call script.obj', 'csh touch pwned', '<script>alert(1)</script>', 'f 1 2 3 4', 'f -1 2 3', 'f 1/1 2/2 3/3', 'v NaN 0 0', 'v 1e309 0 0', '\x00']) {
    await bad(project('union', { kind: 'obj', text: `${valid}\n${line}` }));
  }
  const result = await good(project('difference', { kind: 'obj', text: valid }, box([1, 1, 1], [10, 0, 0])));
  near(result.metrics.volume_mm3, 1 / 6);
});

test('open, nonmanifold, zero-area, reversed and invalid-index meshes are rejected', async () => {
  const open = clone(tetra); open.triangles.pop();
  const duplicate = clone(tetra); duplicate.triangles.push(0, 2, 1);
  const degenerate = clone(tetra); degenerate.positions.splice(3, 3, 0, 0, 0);
  const reverse = clone(tetra); for (let i = 0; i < reverse.triangles.length; i += 3) [reverse.triangles[i], reverse.triangles[i + 1]] = [reverse.triangles[i + 1], reverse.triangles[i]];
  const outside = clone(tetra); outside.triangles[0] = 100;
  const nonfinite = clone(tetra); nonfinite.positions[0] = Infinity;
  const pinch = clone(tetra); pinch.positions.push(-1, 0, 0, 0, -1, 0, 0, 0, -1); pinch.triangles.push(...tetra.triangles.map(x => x === 0 ? 0 : x + 3).reduce((out, x, i, all) => i % 3 ? out : [...out, all[i], all[i + 2], all[i + 1]], []));
  for (const mesh of [open, duplicate, degenerate, reverse, outside, nonfinite, pinch]) await bad(project('union', mesh));
});

test('bounded declarative schema rejects extra fields, invalid units, dimensions and size', async () => {
  for (const input of [
    { ...project(), units: 'in' }, { ...project(), script: 'process.exit()' },
    { ...project(), schema: 'solid-mesh-workbench/v2' }, { ...project(), operation: 'hull' },
    project('union', { kind: 'box', size: [1, 2, 0] }),
    project('union', { kind: 'box', size: [1, 2, 3], rotate: [361, 0, 0] }),
    project('union', { kind: 'box', size: [1, 2, 3], translate: [100000, 0, 0] }),
    project('union', { kind: 'cylinder', radius: 1, height: 1, segments: 8.5 }),
    project('union', { kind: 'mesh', ...tetra, positions: new Array(30003).fill(0) }),
    project('union', { kind: 'obj', text: '#'.repeat(LIMITS.objBytes + 1) }),
  ]) await bad(input);
});

test('repeated mixed success and rejection leaves engine usable', async () => {
  for (let i = 0; i < 30; i++) {
    if (i % 3 === 0) await bad(project('union', { ...tetra, triangles: [0, 1, 2] }));
    const result = await good(project(['union', 'difference', 'intersection'][i % 3]));
    near(result.metrics.volume_mm3, i % 3 === 0 ? 12000 : 4000);
  }
});

test('CLI isolates JSON framing, UTF-8 validation and dynamic-code prohibition', () => {
  const cli = fileURLToPath(new URL('../plugins/solid-mesh-workbench/solid-mesh-workbench/engine/cli.mjs', import.meta.url));
  const run = input => spawnSync(process.execPath, ['--max-old-space-size=256', '--wasm-max-mem-pages=4096', '--disallow-code-generation-from-strings', cli], { input, encoding: 'utf8', timeout: 20000, maxBuffer: LIMITS.outputBytes });
  for (const input of [JSON.stringify(project()), '{broken', Buffer.from([0xff]), ' '.repeat(LIMITS.inputBytes + 1)]) {
    const child = run(input); assert.equal(child.status, 0); assert.equal(child.stderr, '');
    const response = JSON.parse(child.stdout); assert.equal(response.ok, input === JSON.stringify(project()));
    assert.equal(child.stdout.trim().split('\n').length, 1);
  }
});
