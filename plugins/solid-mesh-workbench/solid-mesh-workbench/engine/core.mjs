import { readFile } from 'node:fs/promises';
import Module from '../vendor/manifold.js';

export const LIMITS = Object.freeze({
  inputBytes: 2 * 1024 * 1024, objBytes: 1024 * 1024,
  vertices: 10000, triangles: 20000, resultVertices: 10000,
  resultTriangles: 20000, outputBytes: 12 * 1024 * 1024,
  coordinate: 100000, dimension: 10000,
});
const SCHEMA = 'solid-mesh-workbench/v1';
class InputError extends Error {}
const fail = message => { throw new InputError(message); };
const requireThat = (condition, message) => { if (!condition) fail(message); };
const bytes = value => Buffer.byteLength(value, 'utf8');
let modulePromise;
async function engine() {
  if (!modulePromise) modulePromise = readFile(new URL('../vendor/manifold.wasm', import.meta.url))
    .then(wasmBinary => Module({ wasmBinary, print: () => {}, printErr: () => {} }))
    .then(wasm => { wasm.setup(); return wasm; });
  return modulePromise;
}
function keys(object, allowed, label) {
  requireThat(object !== null && typeof object === 'object' && !Array.isArray(object), `${label}必须是对象。`);
  requireThat(Object.keys(object).every(key => allowed.includes(key)), `${label}含有不支持的字段。`);
}
function number(value, min, max, label) {
  requireThat(typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max, `${label}必须是 ${min} 至 ${max} 之间的有限数值。`);
  return value;
}
function vector(value, min, max, label) {
  requireThat(Array.isArray(value) && value.length === 3, `${label}必须包含三个数值。`);
  return value.map(x => number(x, min, max, label));
}
function indexArray(value, n, label) {
  requireThat(Array.isArray(value), `${label}必须是索引数组。`);
  return value.map(x => {
    requireThat(Number.isSafeInteger(x) && x >= 0 && x < n, `${label}含有越界或非整数索引。`);
    return x;
  });
}

// The OBJ subset deliberately has no path resolution, materials, commands or scripts.
export function parseOBJ(text) {
  requireThat(typeof text === 'string' && bytes(text) <= LIMITS.objBytes, 'OBJ 必须为不超过 1 MiB 的 UTF-8 文本。');
  requireThat(!/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/.test(text), 'OBJ 含有不支持的控制字符。');
  const positions = [], triangles = [];
  const numeric = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.split('#', 1)[0].trim();
    if (!line) continue;
    const part = line.split(/\s+/);
    if (part[0] === 'v') {
      requireThat(part.length === 4 && part.slice(1).every(x => numeric.test(x)), 'OBJ 顶点必须为 v x y z。');
      requireThat(positions.length / 3 < LIMITS.vertices, 'OBJ 顶点超过 10000 个。');
      positions.push(...part.slice(1).map(x => number(Number(x), -LIMITS.coordinate, LIMITS.coordinate, '顶点坐标')));
    } else if (part[0] === 'f') {
      requireThat(part.length === 4 && part.slice(1).every(x => /^[1-9]\d*$/.test(x)), 'OBJ 面必须为三个正整数索引；不支持多边形、相对索引或斜线属性。');
      requireThat(triangles.length / 3 < LIMITS.triangles, 'OBJ 三角形超过 20000 个。');
      triangles.push(...part.slice(1).map(x => Number(x) - 1));
    } else fail('OBJ 仅支持 v、三角形 f 和注释；不支持材质、纹理、外部引用或其他指令。');
  }
  return { positions, triangles, mergeFromVert: [], mergeToVert: [] };
}

// Explicit topological identities are authoritative. Equal coordinates are never welded.
function identities(mesh) {
  const n = mesh.positions.length / 3, parent = Array.from({ length: n }, (_, i) => i);
  const root = x => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
  for (let i = 0; i < mesh.mergeFromVert.length; i++) {
    const a = mesh.mergeFromVert[i], b = mesh.mergeToVert[i];
    requireThat([0, 1, 2].every(k => mesh.positions[3 * a + k] === mesh.positions[3 * b + k]), '拓扑合并索引必须引用坐标完全相同的顶点。');
    const ra = root(a), rb = root(b);
    if (ra !== rb) parent[Math.max(ra, rb)] = Math.min(ra, rb);
  }
  return Array.from({ length: n }, (_, i) => root(i));
}
function checkTopology(mesh) {
  const roots = identities(mesh), edges = new Map(), links = new Map();
  for (let i = 0; i < mesh.triangles.length; i += 3) {
    const ids = mesh.triangles.slice(i, i + 3).map(x => roots[x]);
    requireThat(new Set(ids).size === 3, '网格含有退化三角形。');
    const [a, b, c] = ids.map(x => mesh.positions.slice(x * 3, x * 3 + 3));
    const u = b.map((x, k) => x - a[k]), v = c.map((x, k) => x - a[k]);
    const cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
    requireThat(cross.some(x => x !== 0), '网格含有零面积三角形。');
    for (let j = 0; j < 3; j++) {
      const x = ids[j], y = ids[(j + 1) % 3], z = ids[(j + 2) % 3];
      const key = x < y ? `${x},${y}` : `${y},${x}`;
      const edge = edges.get(key) ?? [0, 0];
      edge[0]++; edge[1] += x < y ? 1 : -1; edges.set(key, edge);
      if (!links.has(x)) links.set(x, new Map());
      const link = links.get(x);
      for (const [from, to] of [[y, z], [z, y]]) {
        if (!link.has(from)) link.set(from, new Set());
        link.get(from).add(to);
      }
    }
  }
  requireThat([...edges.values()].every(([count, direction]) => count === 2 && direction === 0), '网格必须封闭且朝向一致；发现边界边、非流形边或方向冲突。');
  for (const link of links.values()) {
    requireThat([...link.values()].every(neighbors => neighbors.size === 2), '网格含有非流形顶点。');
    const todo = [link.keys().next().value], seen = new Set();
    while (todo.length) {
      const item = todo.pop();
      if (seen.has(item)) continue;
      seen.add(item); todo.push(...link.get(item));
    }
    requireThat(seen.size === link.size, '网格含有相互断开的顶点邻域。');
  }
}
function validateMesh(input) {
  requireThat(Array.isArray(input.positions) && input.positions.length >= 12 && input.positions.length % 3 === 0 && input.positions.length <= 3 * LIMITS.vertices, '网格顶点必须为 4 至 10000 个 XYZ 坐标。');
  const positions = input.positions.map(x => Math.fround(number(x, -LIMITS.coordinate, LIMITS.coordinate, '顶点坐标')));
  const n = positions.length / 3;
  requireThat(Array.isArray(input.triangles) && input.triangles.length >= 12 && input.triangles.length % 3 === 0 && input.triangles.length <= 3 * LIMITS.triangles, '网格必须含有 4 至 20000 个三角形。');
  requireThat(Array.isArray(input.mergeFromVert ?? []) && Array.isArray(input.mergeToVert ?? []) && (input.mergeFromVert ?? []).length <= n && (input.mergeToVert ?? []).length <= n, '拓扑合并数组长度无效。');
  const mesh = { positions, triangles: indexArray(input.triangles, n, '三角形'), mergeFromVert: indexArray(input.mergeFromVert ?? [], n, '拓扑合并'), mergeToVert: indexArray(input.mergeToVert ?? [], n, '拓扑合并') };
  requireThat(mesh.mergeFromVert.length === mesh.mergeToVert.length, '拓扑合并数组的长度必须一致。');
  checkTopology(mesh);
  return mesh;
}
function operand(input, name) {
  const common = ['kind', 'translate', 'rotate'];
  const fields = { box: ['size'], cylinder: ['radius', 'height', 'segments'], obj: ['text'], mesh: ['positions', 'triangles', 'mergeFromVert', 'mergeToVert'] };
  keys(input, [...common, ...(fields[input?.kind] ?? [])], `实体 ${name}`);
  requireThat(Object.hasOwn(fields, input.kind), `实体 ${name}的类型不受支持。`);
  const result = { kind: input.kind, translate: vector(input.translate ?? [0, 0, 0], -LIMITS.coordinate, LIMITS.coordinate, '平移'), rotate: vector(input.rotate ?? [0, 0, 0], -360, 360, '旋转角度') };
  if (input.kind === 'box') result.size = vector(input.size, 0.01, LIMITS.dimension, '长方体尺寸');
  if (input.kind === 'cylinder') {
    result.radius = number(input.radius, 0.01, LIMITS.dimension, '圆柱半径');
    result.height = number(input.height, 0.01, LIMITS.dimension, '圆柱高度');
    result.segments = number(input.segments ?? 32, 8, 128, '圆柱分段');
    requireThat(Number.isInteger(result.segments), '圆柱分段必须是整数。');
  }
  if (input.kind === 'obj' || input.kind === 'mesh') {
    Object.assign(result, validateMesh(input.kind === 'obj' ? parseOBJ(input.text) : input));
    result.kind = 'mesh';
  }
  return result;
}
function fromManifold(solid, isResult = false) {
  requireThat(solid.status() === 'NoError', '几何引擎拒绝此网格；请检查封闭性、方向和拓扑。');
  const m = solid.getMesh();
  const positions = [];
  for (let i = 0; i < m.vertProperties.length; i += m.numProp) positions.push(...m.vertProperties.slice(i, i + 3));
  const output = { positions, triangles: Array.from(m.triVerts), mergeFromVert: Array.from(m.mergeFromVert), mergeToVert: Array.from(m.mergeToVert) };
  requireThat(positions.length / 3 <= (isResult ? LIMITS.resultVertices : LIMITS.vertices) && output.triangles.length / 3 <= (isResult ? LIMITS.resultTriangles : LIMITS.triangles), '计算网格超过顶点或三角形限制。');
  requireThat(positions.every(x => Number.isFinite(x) && Math.abs(x) <= LIMITS.coordinate), '变换后的坐标超出允许范围。');
  return output;
}
export function exportOBJ(mesh) {
  const roots = identities(mesh), used = new Map(), positions = [], triangles = [];
  for (const raw of mesh.triangles) {
    const root = roots[raw];
    if (!used.has(root)) {
      used.set(root, used.size + 1);
      positions.push(`v ${mesh.positions.slice(root * 3, root * 3 + 3).join(' ')}`);
    }
    triangles.push(used.get(root));
  }
  const lines = ['# 立体网格布尔工坊；坐标单位：毫米（mm）', ...positions];
  for (let i = 0; i < triangles.length; i += 3) lines.push(`f ${triangles.slice(i, i + 3).join(' ')}`);
  return `${lines.join('\n')}\n`;
}

/** No filesystem paths, URLs, arbitrary code, or implicit unit conversion are accepted. */
export async function calculate(project) {
  const owned = [];
  const own = value => { owned.push(value); return value; };
  try {
    requireThat(bytes(JSON.stringify(project)) <= LIMITS.inputBytes, '项目超过 2 MiB 限制。');
    keys(project, ['schema', 'units', 'operation', 'a', 'b'], '项目');
    requireThat(project.schema === SCHEMA && project.units === 'mm', '项目版本无效，或尚未明确选择毫米（mm）。');
    requireThat(['union', 'difference', 'intersection'].includes(project.operation), '只支持并集、A 减 B 和交集。');
    const a = operand(project.a, 'A'), b = operand(project.b, 'B');
    const wasm = await engine();
    const meshSolid = spec => own(new wasm.Manifold(new wasm.Mesh({ numProp: 3, vertProperties: new Float32Array(spec.positions), triVerts: new Uint32Array(spec.triangles), mergeFromVert: new Uint32Array(spec.mergeFromVert), mergeToVert: new Uint32Array(spec.mergeToVert) })));
    const make = spec => {
      let local;
      if (spec.kind === 'box') local = own(wasm.Manifold.cube(spec.size, false));
      else if (spec.kind === 'cylinder') local = own(wasm.Manifold.cylinder(spec.height, spec.radius, spec.radius, spec.segments, false));
      else local = meshSolid(spec);
      // Accept primitives at the same Float32 precision stored by the project.
      // Otherwise decimal dimensions change metrics on the first JSON reload.
      if (spec.kind !== 'mesh') local = meshSolid(fromManifold(local));
      const localMesh = fromManifold(local);
      requireThat(local.volume() > 0 && Number.isFinite(local.volume()), '输入实体的体积必须为正；不支持空实体或整体反向的表面。');
      let world = local;
      if (spec.rotate.some(x => x !== 0)) world = own(world.rotate(spec.rotate));
      if (spec.translate.some(x => x !== 0)) world = own(world.translate(spec.translate));
      return { solid: world, mesh: fromManifold(world), project: { kind: 'mesh', ...localMesh, translate: spec.translate, rotate: spec.rotate } };
    };
    const left = make(a), right = make(b);
    const result = own(project.operation === 'union' ? left.solid.add(right.solid) : project.operation === 'difference' ? left.solid.subtract(right.solid) : left.solid.intersect(right.solid));
    const mesh = fromManifold(result, true), empty = result.numTri() === 0;
    const volume = empty ? 0 : result.volume(), area = empty ? 0 : result.surfaceArea();
    requireThat(Number.isFinite(volume) && volume >= 0 && Number.isFinite(area) && area >= 0, '几何结果无效；请检查输入和变换。');
    const obj = exportOBJ(mesh);
    requireThat(bytes(obj) <= LIMITS.objBytes, '结果 OBJ 超过 1 MiB；请减少模型复杂度。');
    const response = { ok: true, metrics: { volume_mm3: volume, area_mm2: area, bounds: empty ? null : result.boundingBox(), triangles: result.numTri(), vertices: result.numVert(), empty }, mesh, obj, project: { schema: SCHEMA, units: 'mm', operation: project.operation, a: left.project, b: right.project }, operands: { a: left.mesh, b: right.mesh } };
    requireThat(bytes(JSON.stringify(response.project)) <= LIMITS.inputBytes, '可重载项目超过 2 MiB；请减少输入复杂度。');
    requireThat(bytes(JSON.stringify(response)) <= LIMITS.outputBytes, '结果超过 12 MiB；请减少输入复杂度。');
    return response;
  } catch (error) {
    return { ok: false, error: error instanceof InputError ? error.message : '几何计算失败；请检查网格拓扑，或减少模型复杂度后重试。' };
  } finally {
    for (let i = owned.length - 1; i >= 0; i--) owned[i].delete();
  }
}
