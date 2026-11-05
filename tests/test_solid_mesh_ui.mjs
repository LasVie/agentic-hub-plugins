import test from 'node:test';
import assert from 'node:assert/strict';
import { calculate } from '../plugins/solid-mesh-workbench/solid-mesh-workbench/engine/core.mjs';
import { formatMetric, serializeProject, meshFrame } from '../plugins/solid-mesh-workbench/solid-mesh-workbench/web/ui_helpers.mjs';

const LIMIT = 2 * 1024 * 1024;
const project = (a, b, operation = 'difference') => ({ schema: 'solid-mesh-workbench/v1', units: 'mm', operation, a, b });
const box = (size, translate = [0, 0, 0]) => ({ kind: 'box', size, translate });
async function good(input) {
  const result = await calculate(input);
  assert.equal(result.ok, true, result.error);
  return result;
}

// Independent closed torus input, with shared indices and outward orientation.
// Its valid canonical project fits the import cap; indentation makes it too big.
function torus(segments = 88) {
  const mesh = { kind: 'mesh', positions: [], triangles: [], mergeFromVert: [], mergeToVert: [] };
  for (let i = 0; i < segments; i++) for (let j = 0; j < segments; j++) {
    const u = 2 * Math.PI * i / segments, v = 2 * Math.PI * j / segments;
    mesh.positions.push(Math.fround((5 + Math.cos(v)) * Math.cos(u)), Math.fround((5 + Math.cos(v)) * Math.sin(u)), Math.fround(Math.sin(v)));
    const a = i * segments + j, b = ((i + 1) % segments) * segments + j;
    const c = ((i + 1) % segments) * segments + (j + 1) % segments, d = i * segments + (j + 1) % segments;
    mesh.triangles.push(a, b, c, a, c, d);
  }
  return mesh;
}

test('a valid large mesh project downloads within the cap and reloads through the real engine', async () => {
  const mesh = torus();
  const first = await good(project(mesh, mesh, 'intersection'));
  assert.equal(first.metrics.vertices, 7744);
  assert.equal(first.metrics.triangles, 15488);
  assert.ok(Buffer.byteLength(JSON.stringify(first.project, null, 2)) > LIMIT, 'fixture must reproduce the old export overflow');
  const text = serializeProject(first.project);
  assert.ok(Buffer.byteLength(text) <= LIMIT);
  assert.ok(!text.endsWith('\n'));
  const restored = await good(JSON.parse(text));
  assert.deepEqual(restored.metrics, first.metrics);
  assert.deepEqual(restored.mesh, first.mesh);
});

test('small valid solids keep nonzero displayed measurements', async () => {
  const result = await good(project(box([0.01, 0.01, 0.01]), box([1, 1, 1], [10, 10, 10])));
  assert.ok(result.metrics.volume_mm3 > 0);
  const displayed = formatMetric(result.metrics.volume_mm3);
  assert.notEqual(displayed, '0');
  assert.ok(Number(displayed) > 0);
  assert.ok(Math.abs(Number(displayed) / result.metrics.volume_mm3 - 1) < 1e-6);
});

test('metrics preserve seven significant digits, zero and invalid states', () => {
  assert.equal(formatMetric(12000), '12,000');
  assert.equal(formatMetric(1.23456789), '1.234568');
  assert.equal(formatMetric(1e-20), '1E-20');
  assert.equal(formatMetric(1e12), '1E12');
  assert.equal(formatMetric(-0), '0');
  assert.equal(formatMetric(0), '0');
  assert.equal(formatMetric(NaN), '—');
  assert.equal(formatMetric(Infinity), '—');
  assert.equal(formatMetric(null), '—');
});

test('hiding a remote operand allows the actual result to fill the view', async () => {
  const result = await good(project(box([20, 20, 20]), box([20, 20, 20], [90000, 0, 0])));
  const visible = meshFrame([result.mesh]);
  assert.deepEqual(visible.center, [10, 10, 10]);
  assert.equal(visible.radius, Math.hypot(10, 10, 10));
  const withInputs = meshFrame([result.mesh, result.operands.a, result.operands.b]);
  assert.ok(withInputs.radius > 45000);
  assert.ok(withInputs.radius / visible.radius > 2500);
});

test('sub-millimetre geometry uses its actual radius and empty geometry has a stable frame', async () => {
  const result = await good(project(box([0.01, 0.01, 0.01]), box([1, 1, 1], [10, 10, 10])));
  const frame = meshFrame([result.mesh]);
  assert.ok(frame.radius > 0 && frame.radius < 0.01);
  assert.ok(Math.abs(frame.radius - Math.sqrt(3) * Math.fround(0.01) / 2) < 1e-12);
  assert.deepEqual(meshFrame([{ positions: [] }]), { center: [0, 0, 0], radius: 1 });
  assert.throws(() => meshFrame([{ positions: [0, NaN, 0] }]), /无效坐标/);
});

test('project byte cap uses UTF-8 and includes the complete serialized payload', () => {
  const overhead = Buffer.byteLength(JSON.stringify({ text: '' }));
  const remaining = LIMIT - overhead;
  const exact = { text: '中'.repeat(Math.floor(remaining / 3)) + 'x'.repeat(remaining % 3) };
  const text = serializeProject(exact);
  assert.equal(Buffer.byteLength(text), LIMIT);
  assert.deepEqual(JSON.parse(text), exact);
  const tooLarge = { text: exact.text + '中' };
  assert.ok(JSON.stringify(tooLarge).length < LIMIT, 'character count alone would incorrectly allow this file');
  assert.throws(() => serializeProject(tooLarge), /2 MiB/);
  const circular = {}; circular.self = circular;
  assert.throws(() => serializeProject(circular), /有效 JSON/);
  assert.throws(() => serializeProject({ value: NaN }), /有效 JSON/);
});
