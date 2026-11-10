// Plugin-owned model contract and strict JSON reader. Model contents are data.
export const VERSION = '1.0.0';
export class ModelError extends Error {
  constructor(code, message) { super(message); this.code = code; }
}
const fail = (code, message) => { throw new ModelError(code, message); };
export function parseModel(text) {
  if (typeof text !== 'string' || new TextEncoder().encode(text).length > 65536)
    fail('input_limit', '模型文本最多 64 KiB。');
  let pos = 0;
  const space = () => { while (/\s/.test(text[pos] || '') && pos < text.length) pos++; };
  function value(depth = 0) {
    if (depth > 10) fail('invalid_json', 'JSON 嵌套过深。');
    space();
    if (text[pos] === '"') {
      const match = /^"(?:[^"\\\x00-\x1f]|\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))*"/.exec(text.slice(pos));
      if (!match) fail('invalid_json', 'JSON 字符串无效。');
      pos += match[0].length; return JSON.parse(match[0]);
    }
    if (text[pos] === '{' || text[pos] === '[') {
      const object = text[pos++] === '{', end = object ? '}' : ']';
      const result = object ? Object.create(null) : [], keys = new Set();
      space(); if (text[pos] === end) { pos++; return result; }
      for (;;) {
        space();
        if (object) {
          if (text[pos] !== '"') fail('invalid_json', '对象字段名必须加双引号。');
          const key = value(depth + 1); space();
          if (keys.has(key)) fail('duplicate_json_key', 'JSON 含重复字段，拒绝静默覆盖。');
          keys.add(key);
          if (text[pos++] !== ':') fail('invalid_json', 'JSON 字段缺少冒号。');
          result[key] = value(depth + 1);
        } else result.push(value(depth + 1));
        space(); const next = text[pos++];
        if (next === end) return result;
        if (next !== ',') fail('invalid_json', 'JSON 分隔符无效。');
      }
    }
    const match = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(pos));
    if (!match) fail('invalid_json', '请输入有效 JSON 模型。');
    pos += match[0].length; return JSON.parse(match[0]);
  }
  const model = value(); space();
  if (pos !== text.length) fail('invalid_json', 'JSON 后含多余内容。');
  return validateModel(model);
}
function shape(v, keys, label) {
  if (!v || typeof v !== 'object' || Array.isArray(v) || Object.keys(v).length !== keys.length || keys.some(k => !Object.hasOwn(v, k)))
    fail('model_invalid', `${label}字段不完整或含未支持字段。`);
}
function number(v, min, max, label) {
  if (typeof v !== 'number' || !Number.isFinite(v) || v < min || v > max)
    fail('model_invalid', `${label}必须为 ${min} 到 ${max} 之间的有限数值。`);
}
export function validateModel(m) {
  shape(m, ['schema_version','name','headloss','nodes','pipes'], '模型');
  if (m.schema_version !== 1 || m.headloss !== 'H-W') fail('unsupported_model', '仅支持 schema_version=1、headloss="H-W" 的稳态固定需水模型。');
  if (typeof m.name !== 'string' || !m.name.trim() || m.name.length > 80) fail('model_invalid', '模型名称须为 1–80 个字符。');
  if (!Array.isArray(m.nodes) || m.nodes.length < 2 || m.nodes.length > 50 || !Array.isArray(m.pipes) || m.pipes.length < 1 || m.pipes.length > 80)
    fail('input_limit', '仅支持 2–50 个节点和 1–80 条管道。');
  const ids = new Set(), links = new Set(), neighbors = new Map(); let reservoir;
  const id = (s, set) => {
    if (typeof s !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]{0,30}$/.test(s) || set.has(s))
      fail('model_invalid', 'ID 须以英文字母开头、仅含字母数字或 _-，最多 31 位且不能重复。');
    set.add(s);
  };
  for (const n of m.nodes) {
    if (!n || !['reservoir','junction'].includes(n.type)) fail('unsupported_model', '仅支持 reservoir 水库与 junction 需水节点。');
    shape(n, n.type === 'reservoir' ? ['id','type','head_m','x','y'] : ['id','type','elevation_m','demand_lps','x','y'], '节点');
    id(n.id, ids); neighbors.set(n.id, []);
    number(n.x, -1e6, 1e6, '绘图 x'); number(n.y, -1e6, 1e6, '绘图 y');
    if (n.type === 'reservoir') {
      if (reservoir) fail('unsupported_model', '本版仅支持一个固定水头水库。');
      reservoir = n.id; number(n.head_m, -100, 5000, '水库总水头（m）');
    } else {
      number(n.elevation_m, -100, 5000, '节点高程（m）'); number(n.demand_lps, 0, 1000, '需水量（L/s）');
    }
  }
  if (!reservoir) fail('model_invalid', '模型必须含一个固定水头水库。');
  for (const p of m.pipes) {
    shape(p, ['id','from','to','length_m','diameter_mm','roughness'], '管道'); id(p.id, links);
    if (!ids.has(p.from) || !ids.has(p.to) || p.from === p.to) fail('model_invalid', '管道两端须为不同且已定义的节点。');
    number(p.length_m, 0.1, 100000, '管长（m）'); number(p.diameter_mm, 10, 3000, '管径（mm）'); number(p.roughness, 10, 200, 'H-W C 系数');
    neighbors.get(p.from).push(p.to); neighbors.get(p.to).push(p.from);
  }
  const seen = new Set([reservoir]), queue = [reservoir];
  for (const n of queue) for (const other of neighbors.get(n)) if (!seen.has(other)) { seen.add(other); queue.push(other); }
  if (seen.size !== ids.size) fail('disconnected_model', '存在无法连到水库的节点；没有运行求解。');
  return m;
}
