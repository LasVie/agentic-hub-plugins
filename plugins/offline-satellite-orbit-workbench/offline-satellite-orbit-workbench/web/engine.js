// Plugin-owned input boundaries and bounded geometry; Satellite.js modules remain unchanged.
import {twoline2satrec, json2satrec, alpha5ToNumber} from './vendor/satellite-js/io.js';
import {sgp4, gstime} from './vendor/satellite-js/propagation.js';
import {eciToGeodetic, eciToEcf, ecfToLookAngles} from './vendor/satellite-js/transforms.js';

export const VERSION = '1.0.0';
export const ENGINE_VERSION = '7.2.0';
const DAY_MS = 86400000;
const DEG = 180 / Math.PI;
const MAX_ELEMENTS_BYTES = 16384;

export class OrbitError extends Error {
  constructor(code, message) { super(message); this.name = 'OrbitError'; this.code = code; }
}
function fail(code, message) { throw new OrbitError(code, message); }
function object(value, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('invalid_parameter', `${label}必须是对象。`);
}
function number(value, min, max, label) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < min || value > max) {
    fail('invalid_parameter', `${label}必须是 ${min} 至 ${max} 之间的有限数值。`);
  }
  return value;
}
function unknownKeys(value, allowed, code, label) {
  if (Object.keys(value).some(key => !allowed.has(key))) fail(code, `${label}包含不支持的字段。`);
}

// Parse through six fractional digits without truncating the input to Date milliseconds.
export function parseUtc(text) {
  if (typeof text !== 'string') fail('invalid_utc', '时间必须是明确以 Z 结尾的 UTC 文本。');
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?Z$/.exec(text);
  if (!m) fail('invalid_utc', '请使用 YYYY-MM-DDTHH:mm:ss[.ffffff]Z 格式的 UTC 时间。');
  const [year, month, day, hour, minute, second] = m.slice(1, 7).map(Number);
  if (year < 1957 || year > 2056 || month < 1 || month > 12 || day < 1 || hour > 23 || minute > 59 || second > 59) {
    fail('invalid_utc', 'UTC 日期超出支持范围，或包含无效日期、时刻或闰秒。');
  }
  const whole = Date.UTC(year, month - 1, day, hour, minute, second);
  const d = new Date(whole);
  if (d.getUTCFullYear() !== year || d.getUTCMonth() !== month - 1 || d.getUTCDate() !== day) {
    fail('invalid_utc', 'UTC 日期不存在；不会自动滚动到下个月。');
  }
  return whole + Number(`0.${m[7] || '0'}`) * 1000;
}
export function formatUtc(ms) {
  const micros = Math.round(ms * 1000);
  const seconds = Math.floor(micros / 1000000);
  return `${new Date(seconds * 1000).toISOString().slice(0, 19)}.${String(micros - seconds * 1000000).padStart(6, '0')}Z`;
}

// A small strict JSON reader preserves duplicate-key rejection before conversion.
export function readStrictJson(text) {
  let i = 0;
  const bad = () => fail('invalid_omm', 'OMM 必须是有效的 JSON 对象。');
  const white = () => { while (i < text.length && /[ \t\r\n]/.test(text[i])) i++; };
  function string() {
    const start = i++;
    while (i < text.length) {
      if (text[i] === '\\') { i += 2; continue; }
      if (text[i++] === '"') { try { return JSON.parse(text.slice(start, i)); } catch { bad(); } }
    }
    bad();
  }
  function value(depth) {
    if (depth > 12) fail('invalid_omm', 'OMM JSON 嵌套过深。');
    white();
    if (text[i] === '"') return string();
    if (text[i] === '{') {
      i++; white(); const out = Object.create(null); const keys = new Set();
      if (text[i] === '}') { i++; return out; }
      while (i < text.length) {
        white(); if (text[i] !== '"') bad(); const key = string();
        if (keys.has(key)) fail('duplicate_json_key', `OMM JSON 包含重复字段：${key}。`);
        keys.add(key); white(); if (text[i++] !== ':') bad(); out[key] = value(depth + 1); white();
        const end = text[i++]; if (end === '}') return out; if (end !== ',') bad();
      }
      bad();
    }
    if (text[i] === '[') {
      i++; white(); const out = []; if (text[i] === ']') { i++; return out; }
      while (i < text.length) { out.push(value(depth + 1)); white(); const end = text[i++]; if (end === ']') return out; if (end !== ',') bad(); }
      bad();
    }
    const token = /^(?:true|false|null|-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?)/.exec(text.slice(i));
    if (!token) bad(); i += token[0].length;
    const result = JSON.parse(token[0]); if (typeof result === 'number' && !Number.isFinite(result)) bad(); return result;
  }
  const result = value(0); white(); if (i !== text.length) bad(); return result;
}

function tleChecksum(line) {
  let sum = 0;
  for (const c of line.slice(0, 68)) sum += /\d/.test(c) ? Number(c) : c === '-' ? 1 : 0;
  return sum % 10 === Number(line[68]);
}
function readTle(text) {
  let lines = text.replace(/\r\n/g, '\n').split('\n');
  if (lines.at(-1) === '') lines.pop();
  let name = '未命名卫星';
  if (lines.length === 3) { name = lines.shift().replace(/^0 /, ''); if (!name || name.length > 80 || /[\x00-\x1f]/.test(name)) fail('invalid_tle', 'TLE 名称必须是 1 至 80 个可显示字符。'); }
  if (lines.length !== 2) fail('invalid_tle', 'TLE 需要两条数据行，可在前面添加一条名称行。');
  const [a, b] = lines;
  if (lines.some(line => line.length !== 69 || !/^[\x20-\x7e]+$/.test(line) || !/\d$/.test(line))) fail('invalid_tle', 'TLE 每条数据行必须恰好有 69 个 ASCII 字符，末位是校验数字；不能附带仿真参数。');
  if (a.slice(0, 2) !== '1 ' || b.slice(0, 2) !== '2 ') fail('invalid_tle', 'TLE 行号必须依次为 1 和 2。');
  if (!tleChecksum(a) || !tleChecksum(b)) fail('tle_checksum', 'TLE 校验和不符；请核对完整原始行，不要自行补齐字段。');
  const cat = a.slice(2, 7);
  if (!/^(?:\d{5}|[A-HJ-NP-Z]\d{4})$/.test(cat) || cat !== b.slice(2, 7) || alpha5ToNumber(cat) <= 0) fail('invalid_tle', 'TLE 的两行目录编号必须相同且有效。');
  const spaceA = [8, 17, 32, 43, 52, 61, 63]; const spaceB = [7, 16, 25, 33, 42, 51];
  if (spaceA.some(i => a[i] !== ' ') || spaceB.some(i => b[i] !== ' ') || !/^[UCS]$/.test(a[7]) || !/^[A-Z0-9 -]{8}$/.test(a.slice(9, 17)) || !/^[ 0-9]{4}$/.test(a.slice(64, 68)) || !/^[ 0-9]{5}$/.test(b.slice(63, 68)) || a[62] !== '0') fail('invalid_tle', 'TLE 固定列格式无效，或不是支持的标准 SGP4 元素类型 0。');
  if (!/^\d{2}\d{3}\.\d{8}$/.test(a.slice(18, 32)) || !/^[ +\-]\.\d{8}$/.test(a.slice(33, 43)) || !/^[ +\-]\d{5}[+\-]\d$/.test(a.slice(44, 52)) || !/^[ +\-]\d{5}[+\-]\d$/.test(a.slice(53, 61))) fail('invalid_tle', 'TLE 历元、导数或阻力字段格式无效。');
  for (const [start, end] of [[8, 16], [17, 25], [34, 42], [43, 51]]) if (!/^\s*\d{1,3}\.\d{4}$/.test(b.slice(start, end))) fail('invalid_tle', 'TLE 角度字段格式无效。');
  if (!/^\d{7}$/.test(b.slice(26, 33)) || !/^\s*\d{1,2}\.\d{8}$/.test(b.slice(52, 63))) fail('invalid_tle', 'TLE 偏心率或平均运动字段格式无效。');
  const yy = Number(a.slice(18, 20)), year = yy >= 57 ? 1900 + yy : 2000 + yy;
  const days = Number(a.slice(20, 32)); const yearDays = (Date.UTC(year + 1, 0, 1) - Date.UTC(year, 0, 1)) / DAY_MS;
  if (days < 1 || days >= yearDays + 1) fail('invalid_tle', 'TLE 历元日不在该年份内。');
  if (Number(b.slice(8, 16)) > 180 || Number(b.slice(17, 25)) >= 360 || Number(b.slice(34, 42)) >= 360 || Number(b.slice(43, 51)) >= 360 || Number(b.slice(52, 63)) < 0.05 || Number(b.slice(52, 63)) > 18) fail('invalid_tle', 'TLE 轨道角度或平均运动超出本工作台支持范围（平均运动 0.05–18 圈/日）。');
  return {satrec: twoline2satrec(a, b), epochMs: Date.UTC(year, 0, 1) + (days - 1) * DAY_MS, name, catalogId: String(alpha5ToNumber(cat)), elements: [name, a, b].join('\n')};
}

const OMM_REQUIRED = ['EPOCH', 'NORAD_CAT_ID', 'MEAN_MOTION', 'ECCENTRICITY', 'INCLINATION', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY', 'BSTAR', 'MEAN_MOTION_DOT', 'MEAN_MOTION_DDOT'];
const OMM_ALLOWED = new Set([...OMM_REQUIRED, 'OBJECT_NAME', 'OBJECT_ID', 'CENTER_NAME', 'REF_FRAME', 'TIME_SYSTEM', 'MEAN_ELEMENT_THEORY', 'CLASSIFICATION_TYPE', 'EPHEMERIS_TYPE', 'ELEMENT_SET_NO', 'REV_AT_EPOCH']);
function readOmm(text) {
  const obj = readStrictJson(text);
  if (!obj || typeof obj !== 'object' || Array.isArray(obj)) fail('invalid_omm', 'OMM 必须是一个 JSON 对象，不能是目录数组。');
  unknownKeys(obj, OMM_ALLOWED, 'invalid_omm', 'OMM');
  if (OMM_REQUIRED.some(key => !Object.hasOwn(obj, key))) fail('invalid_omm', `OMM 缺少必要字段：${OMM_REQUIRED.filter(key => !Object.hasOwn(obj, key)).join('、')}。`);
  for (const [key, expected] of [['CENTER_NAME', 'EARTH'], ['REF_FRAME', 'TEME'], ['TIME_SYSTEM', 'UTC'], ['MEAN_ELEMENT_THEORY', 'SGP4']]) if (Object.hasOwn(obj, key) && obj[key] !== expected) fail('unsupported_omm', `仅支持 ${key}=${expected}。`);
  if (typeof obj.EPOCH !== 'string') fail('invalid_omm', 'OMM EPOCH 必须是 UTC 文本。');
  const epochText = obj.EPOCH.endsWith('Z') ? obj.EPOCH : `${obj.EPOCH}Z`;
  const epochMs = parseUtc(epochText); obj.EPOCH = epochText;
  for (const key of OMM_REQUIRED.filter(key => !['EPOCH'].includes(key))) {
    if (typeof obj[key] !== 'number' || !Number.isFinite(obj[key])) fail('invalid_omm', `OMM ${key} 必须是有限数值。`);
  }
  const bounds = {NORAD_CAT_ID: [1, 999999999], MEAN_MOTION: [0.05, 18], ECCENTRICITY: [0, 0.9999999], INCLINATION: [0, 180], RA_OF_ASC_NODE: [0, 359.999999999], ARG_OF_PERICENTER: [0, 359.999999999], MEAN_ANOMALY: [0, 359.999999999], BSTAR: [-1, 1], MEAN_MOTION_DOT: [-1, 1], MEAN_MOTION_DDOT: [-1, 1]};
  for (const [key, [min, max]] of Object.entries(bounds)) if (obj[key] < min || obj[key] > max) fail('invalid_omm', `OMM ${key} 超出支持范围。`);
  if (!Number.isInteger(obj.NORAD_CAT_ID)) fail('invalid_omm', 'OMM 目录编号必须是整数。');
  if (Object.hasOwn(obj, 'EPHEMERIS_TYPE') && obj.EPHEMERIS_TYPE !== 0) fail('unsupported_omm', '仅支持 EPHEMERIS_TYPE=0 的 SGP4 元素。');
  for (const key of ['ELEMENT_SET_NO', 'REV_AT_EPOCH']) if (Object.hasOwn(obj, key) && (!Number.isInteger(obj[key]) || obj[key] < 0 || obj[key] > 999999999)) fail('invalid_omm', `OMM ${key} 必须是有限范围内的非负整数。`);
  for (const key of ['OBJECT_NAME', 'OBJECT_ID', 'CLASSIFICATION_TYPE']) if (Object.hasOwn(obj, key) && (typeof obj[key] !== 'string' || obj[key].length > 80 || /[\x00-\x1f]/.test(obj[key]))) fail('invalid_omm', `OMM ${key} 必须是不超过 80 个字符的文本。`);
  return {satrec: json2satrec(obj), epochMs, name: obj.OBJECT_NAME || '未命名卫星', catalogId: String(obj.NORAD_CAT_ID), elements: JSON.stringify(obj, null, 2)};
}

export function validateInput(raw) {
  object(raw, '输入'); unknownKeys(raw, new Set(['format', 'elements', 'startUtc', 'durationHours', 'stepSeconds', 'observer', 'minimumElevationDeg']), 'invalid_parameter', '输入');
  if (!['tle', 'omm'].includes(raw.format)) fail('invalid_parameter', '元素格式必须是 tle 或 omm。');
  if (typeof raw.elements !== 'string' || !raw.elements.trim() || new TextEncoder().encode(raw.elements).length > MAX_ELEMENTS_BYTES) fail('invalid_elements', '轨道元素必须是 1 至 16384 字节的文本。');
  const startMs = parseUtc(raw.startUtc);
  const durationHours = number(raw.durationHours, 0.25, 24, '时窗小时数');
  const stepSeconds = number(raw.stepSeconds, 10, 600, '采样步长（秒）');
  if (!Number.isInteger(stepSeconds)) fail('invalid_parameter', '采样步长必须是整数秒。');
  object(raw.observer, '观察点'); unknownKeys(raw.observer, new Set(['latitudeDeg', 'longitudeDeg', 'heightM']), 'invalid_parameter', '观察点');
  const observer = {latitudeDeg: number(raw.observer.latitudeDeg, -89.9, 89.9, '观察点纬度'), longitudeDeg: number(raw.observer.longitudeDeg, -180, 180, '观察点经度'), heightM: number(raw.observer.heightM, 0, 9000, '观察点高程（米）')};
  const minimumElevationDeg = number(raw.minimumElevationDeg, 0, 89, '最低仰角（度）');
  const orbit = raw.format === 'tle' ? readTle(raw.elements) : readOmm(raw.elements);
  if (orbit.satrec.error) fail('propagation_error', `SGP4 无法初始化该元素集（代码 ${orbit.satrec.error}）。`);
  const endMs = startMs + durationHours * 3600000;
  if (Math.max(Math.abs(startMs - orbit.epochMs), Math.abs(endMs - orbit.epochMs)) > 7 * DAY_MS) fail('epoch_window', '完整计算时窗必须位于轨道元素历元前后 7 日内；请使用相应日期的元素。');
  if (Math.ceil(durationHours * 3600 / stepSeconds) + 1 > 8641) fail('sample_limit', '采样数量超过 8641；请增大步长或缩短时窗。');
  const input = {format: raw.format, elements: orbit.elements, startUtc: formatUtc(startMs), durationHours, stepSeconds, observer, minimumElevationDeg};
  return {input, orbit, startMs, endMs};
}

export function analyzeOrbit(raw) {
  const {input, orbit, startMs, endMs} = validateInput(raw);
  const observerGd = {latitude: input.observer.latitudeDeg / DEG, longitude: input.observer.longitudeDeg / DEG, height: input.observer.heightM / 1000};
  function sample(ms) {
    // Keep each probe independent: reference and crossing-refinement queries need not be chronological.
    const rec = {...orbit.satrec};
    const rv = sgp4(rec, (ms - orbit.epochMs) / 60000);
    if (!rv || rec.error) fail('propagation_error', `SGP4 未返回有效轨道（代码 ${rec.error || 'unknown'}，UTC ${formatUtc(ms)}）；不会导出部分结果。`);
    const gmst = gstime(ms / DAY_MS + 2440587.5);
    const gd = eciToGeodetic(rv.position, gmst);
    const angles = ecfToLookAngles(observerGd, eciToEcf(rv.position, gmst));
    const out = {utc: formatUtc(ms), latitudeDeg: gd.latitude * DEG, longitudeDeg: gd.longitude * DEG, heightKm: gd.height, azimuthDeg: angles.azimuth * DEG, elevationDeg: angles.elevation * DEG, rangeKm: angles.rangeSat, temePositionKm: {...rv.position}, temeVelocityKmS: {...rv.velocity}};
    if ([gd.latitude, gd.longitude, gd.height, angles.azimuth, angles.elevation, angles.rangeSat, ...Object.values(rv.position), ...Object.values(rv.velocity)].some(x => !Number.isFinite(x)) || gd.height < 0 || angles.rangeSat <= 0) fail('propagation_error', '轨道结果不是有效的地表以上有限数值；不会保留旧结果。');
    return out;
  }
  const times = [startMs]; const stepMs = input.stepSeconds * 1000;
  for (let ms = startMs + stepMs; ms < endMs; ms += stepMs) times.push(ms);
  times.push(endMs);
  const samples = times.map(sample); const threshold = input.minimumElevationDeg;
  const above = point => point.elevationDeg >= threshold;
  function crossing(left, right, leftAbove) {
    for (let n = 0; right - left > 500 && n < 20; n++) { const mid = (left + right) / 2; if (above(sample(mid)) === leftAbove) left = mid; else right = mid; }
    return (left + right) / 2;
  }
  const intervals = []; let current = above(samples[0]) ? {startMs, startClipped: true, peak: samples[0]} : null;
  for (let i = 1; i < samples.length; i++) {
    const prev = samples[i - 1], now = samples[i];
    if (!above(prev) && above(now)) current = {startMs: crossing(times[i - 1], times[i], false), startClipped: false, peak: now};
    if (current && above(now) && now.elevationDeg > current.peak.elevationDeg) current.peak = now;
    if (above(prev) && !above(now)) {
      const finish = crossing(times[i - 1], times[i], true);
      intervals.push({startUtc: formatUtc(current.startMs), endUtc: formatUtc(finish), startClipped: current.startClipped, endClipped: false, peakUtc: current.peak.utc, peakElevationDeg: current.peak.elevationDeg}); current = null;
    }
  }
  if (current) intervals.push({startUtc: formatUtc(current.startMs), endUtc: formatUtc(endMs), startClipped: current.startClipped, endClipped: true, peakUtc: current.peak.utc, peakElevationDeg: current.peak.elevationDeg});
  const warnings = [
    '区间只表示几何仰角达到阈值，不代表肉眼可见；未考虑日照、天气、遮挡、大气折射或实际轨道误差。',
    `区间由 ${input.stepSeconds} 秒采样寻找相邻跨越，再细化到 1 秒以内；完全落在两个采样点之间的短暂或擦边区间可能漏检。`,
    '最高仰角来自采样点，不保证是连续轨道的精确最大值；时窗截断的区间会单独标注。',
    '轨道元素仅作为用户提供的数据处理；没有联网更新，也没有验证其真实性或工程适用性。',
  ];
  const maxAgeDays = Math.max(Math.abs(startMs - orbit.epochMs), Math.abs(endMs - orbit.epochMs)) / DAY_MS;
  if (maxAgeDays > 3) warnings.push('计算时窗距离元素历元超过 3 日；元素过旧可能使预测偏离真实轨道。');
  return {version: VERSION, engineVersion: ENGINE_VERSION, input, element: {name: orbit.name, catalogId: orbit.catalogId, epochUtc: formatUtc(orbit.epochMs), format: input.format}, observer: input.observer, minimumElevationDeg: threshold, startUtc: formatUtc(startMs), endUtc: formatUtc(endMs), samples, intervals, warnings, summary: {sampleCount: samples.length, minHeightKm: Math.min(...samples.map(x => x.heightKm)), maxHeightKm: Math.max(...samples.map(x => x.heightKm)), intervalCount: intervals.length}};
}
