/* Plugin-owned bounded GeoJSON adapter; no user commands or expressions. */
(function (root) {
  'use strict';
  const VERSION = '1.0.1';
  const LIMITS = Object.freeze({bytes: 2097152, features: 200, vertices: 40000, depth: 24, timeout: 12000});
  const fail = (code, message) => { throw Object.assign(new Error(message), {code}); };
  const bytes = text => new TextEncoder().encode(text).length;
  const own = (x, k) => Object.prototype.hasOwnProperty.call(x, k);
  const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  // Reject duplicate keys and unsafe integer literals instead of silently changing attributes.
  function parse(text) {
    if (typeof text !== 'string' || bytes(text) > LIMITS.bytes) fail('input_limit', '输入须为不超过 2 MiB 的 UTF-8 GeoJSON 文本。');
    let i = 0;
    const ws = () => { while (/[ \t\r\n]/.test(text[i] || '') && i < text.length) i++; };
    function string() {
      const start = i++; let escape = false;
      while (i < text.length) { const c = text[i++]; if (!escape && c === '"') { try { return JSON.parse(text.slice(start, i)); } catch (_) { break; } } if (!escape && c === '\\') escape = true; else escape = false; }
      fail('invalid_json', 'JSON 字符串无效。');
    }
    function value(depth) {
      if (depth > LIMITS.depth) fail('input_limit', 'JSON 嵌套超过 24 层。');
      ws(); const c = text[i];
      if (c === '"') return string();
      if (c === '{') {
        i++; ws(); const result = Object.create(null), keys = new Set();
        if (text[i] === '}') { i++; return result; }
        while (i < text.length) {
          ws(); if (text[i] !== '"') fail('invalid_json', 'JSON 对象字段须为字符串。');
          const key = string(); if (keys.has(key)) fail('duplicate_key', 'JSON 包含重复字段；不会静默覆盖。'); keys.add(key);
          ws(); if (text[i++] !== ':') fail('invalid_json', 'JSON 字段缺少冒号。'); result[key] = value(depth + 1);
          ws(); const end = text[i++]; if (end === '}') return result; if (end !== ',') break;
        }
        fail('invalid_json', 'JSON 对象格式无效。');
      }
      if (c === '[') {
        i++; ws(); const result = []; if (text[i] === ']') { i++; return result; }
        while (i < text.length) { result.push(value(depth + 1)); ws(); const end = text[i++]; if (end === ']') return result; if (end !== ',') break; }
        fail('invalid_json', 'JSON 数组格式无效。');
      }
      const literal = /^(true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(i));
      if (!literal) fail('invalid_json', 'JSON 值无效。');
      i += literal[0].length; const v = JSON.parse(literal[0]);
      if (typeof v === 'number' && (!Number.isFinite(v) || (Number.isInteger(v) && !Number.isSafeInteger(v)))) fail('unsafe_number', '数值超出有限安全范围；请将大型标识符改为字符串。');
      return v;
    }
    const result = value(0); ws(); if (i !== text.length) fail('invalid_json', 'JSON 末尾含额外内容。'); return result;
  }
  function fields(obj, allowed) { if (!object(obj) || Object.keys(obj).some(k => !allowed.includes(k))) fail('unsupported_field', '存在不支持的字段；仅接受明确的 GeoJSON 字段，不支持 CRS、bbox 或扩展字段。'); }
  const polygons = geometry => geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  function statistics(fc) {
    let vertices = 0, rings = 0, parts = 0;
    for (const f of fc.features) for (const p of polygons(f.geometry)) { parts++; for (const r of p) { rings++; vertices += r.length - 1; } }
    return {features: fc.features.length, vertices, rings, parts, bytes: bytes(JSON.stringify(fc))};
  }
  function validate(fc) {
    fields(fc, ['type', 'features']);
    if (fc.type !== 'FeatureCollection' || !Array.isArray(fc.features) || !fc.features.length || fc.features.length > LIMITS.features) fail('unsupported_collection', '须提供含 1 至 200 个要素的 FeatureCollection。');
    let vertices = 0, minX = Infinity, maxX = -Infinity; const ids = new Set();
    for (const f of fc.features) {
      fields(f, ['type', 'id', 'properties', 'geometry']);
      if (f.type !== 'Feature' || !(f.properties === null || object(f.properties))) fail('invalid_feature', '每个要素须含 Feature 类型、properties 对象或 null。');
      if (own(f, 'id')) {
        if (!(typeof f.id === 'string' || (typeof f.id === 'number' && Number.isFinite(f.id)))) fail('invalid_id', '要素 id 只能是有限数字或字符串。');
        const id = JSON.stringify(f.id); if (ids.has(id)) fail('duplicate_id', '要素 id 重复；请提供唯一标识。'); ids.add(id);
      }
      const g = f.geometry; fields(g, ['type', 'coordinates']);
      if (!['Polygon', 'MultiPolygon'].includes(g.type) || !Array.isArray(g.coordinates) || !g.coordinates.length) fail('unsupported_geometry', '仅支持非空二维 Polygon / MultiPolygon。');
      for (const p of polygons(g)) {
        if (!Array.isArray(p) || !p.length) fail('invalid_ring', '多边形须包含外环。');
        for (const ring of p) {
          if (!Array.isArray(ring) || ring.length < 4) fail('invalid_ring', '环须含至少 4 个坐标（含闭合点）。');
          vertices += ring.length; if (vertices > LIMITS.vertices) fail('input_limit', '坐标数量超过 40,000（含闭合点）。');
          let area = 0;
          for (let j = 0; j < ring.length; j++) {
            const a = ring[j];
            if (!Array.isArray(a) || a.length !== 2 || !a.every(Number.isFinite) || Math.abs(a[0]) > 180 || Math.abs(a[1]) > 90) fail('invalid_coordinate', '坐标须为有限的 [经度, 纬度]；范围 ±180° / ±90°，不支持 Z/M。');
            minX = Math.min(minX, a[0]); maxX = Math.max(maxX, a[0]);
            if (j) { const b = ring[j - 1]; if (Math.abs(a[0] - b[0]) > 180) fail('dateline', '不支持跨越日期变更线的环。'); area += b[0] * a[1] - a[0] * b[1]; }
          }
          const first = ring[0], last = ring[ring.length - 1];
          if (first[0] !== last[0] || first[1] !== last[1] || area === 0) fail('invalid_ring', '环必须精确闭合且不能为零面积。');
        }
      }
    }
    if (maxX - minX > 180) fail('dateline', '数据经度跨度超过 180°，不在本工作台范围内。');
    return fc;
  }
  const read = text => validate(parse(text));
  async function simplify(text, percent, engine) {
    if (!Number.isInteger(percent) || percent < 1 || percent > 100) fail('invalid_percent', '保留比例须为 1 至 100 的整数。');
    const original = read(text);
    const clean = {type: 'FeatureCollection', features: original.features.map((f, i) => ({type: 'Feature', properties: {__slot: i}, geometry: f.geometry}))};
    // No paths, expressions, formatting or commands are taken from feature data.
    const commands = ['-i', 'input.geojson', '-simplify', `${percent}%`, 'weighted', 'keep-shapes', '-o', 'output.geojson', 'format=geojson'];
    let transformed;
    try {
      const files = await engine.applyCommands(commands, {'input.geojson': JSON.stringify(clean)});
      const content = files['output.geojson'];
      transformed = JSON.parse(typeof content === 'string' ? content : new TextDecoder().decode(content));
    } catch (_) { fail('engine_error', '几何引擎未能处理此数据；请检查环、交叉及重叠。原文未修改。'); }
    if (!transformed || !Array.isArray(transformed.features) || transformed.features.length !== original.features.length) fail('feature_loss', '引擎输出丢失了要素；已禁止导出，请提高保留比例或检查数据。');
    const bySlot = new Map();
    for (const f of transformed.features) {
      const slot = f.properties && f.properties.__slot;
      if (!Number.isInteger(slot) || slot < 0 || slot >= original.features.length || bySlot.has(slot) || !f.geometry) fail('feature_loss', '引擎输出身份或几何异常；已禁止导出。');
      bySlot.set(slot, f.geometry);
    }
    const result = {type: 'FeatureCollection', features: original.features.map((f, i) => {
      let geometry = bySlot.get(i);
      if (f.geometry.type === 'MultiPolygon' && geometry.type === 'Polygon') geometry = {type: 'MultiPolygon', coordinates: [geometry.coordinates]};
      const out = {type: 'Feature', properties: f.properties, geometry}; if (own(f, 'id')) out.id = f.id; return out;
    })};
    validate(result);
    const before = statistics(original), after = statistics(result);
    const losses = original.features.map((f, i) => {
      const a = statistics({features: [f]}), b = statistics({features: [result.features[i]]});
      return {index: i, removed_rings: Math.max(0, a.rings - b.rings), removed_parts: Math.max(0, a.parts - b.parts)};
    }).filter(x => x.removed_rings || x.removed_parts);
    return {version: VERSION, engine_version: '0.7.101', percent, original, result, before, after, losses, original_file_bytes: bytes(text)};
  }
  function drawing(fc, bounds) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const f of fc.features) for (const p of polygons(f.geometry)) for (const r of p) for (const [x,y] of r) { minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y); }
    const box = bounds || [minX,minY,maxX,maxY];
    const scale = Math.min(880 / Math.max(box[2]-box[0],1e-12), 520 / Math.max(box[3]-box[1],1e-12));
    const project = ([x,y]) => [(x-(box[0]+box[2])/2)*scale+480, ((box[1]+box[3])/2-y)*scale+300];
    const paths = fc.features.map(f => polygons(f.geometry).map(p => p.map(r => r.map((pt,i)=>{const a=project(pt);return `${i?'L':'M'}${a[0].toFixed(3)},${a[1].toFixed(3)}`;}).join(' ')+' Z').join(' ')).join(' '));
    return {paths, bounds:box};
  }
  function svg(fc) {
    const paths = drawing(fc).paths;
    return '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" width="960" height="600"><title>离线地图简化结果：等距经纬度示意，非测量地图</title><rect width="960" height="600" fill="#f6f8f7"/>' + paths.map((d,i)=>`<path d="${d}" fill="${i%2?'#b5d3c7':'#d6e5b2'}" stroke="#17665e" stroke-width="1.4" fill-rule="evenodd"/>`).join('')+'</svg>\n';
  }
  root.GeoLab = {VERSION, LIMITS, parse, read, validate, statistics, simplify, drawing, svg, bytes};
})(globalThis);
