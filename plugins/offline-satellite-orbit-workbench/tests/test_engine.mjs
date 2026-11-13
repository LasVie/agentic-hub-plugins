import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {analyzeOrbit, validateInput, parseUtc, formatUtc, readStrictJson} from '../offline-satellite-orbit-workbench/web/engine.js';

const fixture = name => fs.readFileSync(new URL(`./fixtures/${name}`, import.meta.url), 'utf8');
const tle = fixture('00005.tle');
const omm = fixture('00005.omm.json');
const deepTle = fixture('04632.tle');
const references = JSON.parse(fixture('reference.json'));
const base = {format: 'tle', elements: tle, startUtc: '2000-06-27T18:50:19.733568Z', durationHours: 24, stepSeconds: 60, observer: {latitudeDeg: 1.3521, longitudeDeg: 103.8198, heightM: 0}, minimumElevationDeg: 10};
const copy = (overrides = {}) => ({...base, observer: {...base.observer}, ...overrides});
const close = (actual, expected, tolerance, label) => assert.ok(Math.abs(actual - expected) <= tolerance, `${label}: ${actual} vs ${expected}`);
const rejects = (input, code) => assert.throws(() => analyzeOrbit(input), e => e.code === code && /[\u3400-\u9fff]/u.test(e.message), code);
function checksum(line) {
  const body = line.slice(0, 68);
  const sum = [...body].reduce((a, c) => a + (/\d/.test(c) ? Number(c) : c === '-' ? 1 : 0), 0);
  return body + sum % 10;
}
function changeTle(lineIndex, start, replacement) {
  const lines = tle.trimEnd().split('\n');
  const line = lines[lineIndex]; lines[lineIndex] = checksum(line.slice(0, start) + replacement + line.slice(start + replacement.length));
  return lines.join('\n');
}
const quick = overrides => analyzeOrbit(copy({durationHours: 0.25, ...overrides}));
let standard;
test('unchanged published JavaScript closure matches recorded SHA-256 for every module', () => {
  const folder = new URL('../offline-satellite-orbit-workbench/web/vendor/satellite-js/', import.meta.url);
  const meta = JSON.parse(fs.readFileSync(new URL('UPSTREAM.json', folder), 'utf8'));
  assert.equal(meta.version, '7.2.0'); assert.equal(Object.keys(meta.included_modules).length, 16);
  let bytes = 0;
  for (const [path, hash] of Object.entries(meta.included_modules)) {
    const b = fs.readFileSync(new URL(path, folder)); bytes += b.length;
    assert.equal(createHash('sha256').update(b).digest('hex'), hash, path);
    assert.doesNotMatch(b.toString(), /\beval\s*\(|\bnew\s+Function\s*\(/);
    assert.doesNotMatch(b.toString(), /\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\b|\bimportScripts\s*\(/);
  }
  assert.equal(bytes, 106103);
});
test('actual analyzeOrbit first sample preserves microsecond epoch and matches official TEME position/velocity', () => {
  standard = analyzeOrbit(copy());
  assert.equal(standard.element.epochUtc, base.startUtc);
  assert.equal(standard.samples[0].utc, base.startUtc);
  assert.equal(standard.version, '1.0.0'); assert.equal(standard.engineVersion, '7.2.0');
  const first = standard.samples[0];
  references.vectors[0].position.forEach((v, i) => close(Object.values(first.temePositionKm)[i], v, 0.001, `epoch position${i}km`));
  references.vectors[0].velocity.forEach((v, i) => close(Object.values(first.temeVelocityKmS)[i], v, 0.000001, `epoch velocity${i}km/s`));
  close(first.heightKm, 782.5369280818, 0.000001, 'geodetic height km');
});
test('full-window samples at +360 and +720 minutes match independent official reference facts', () => {
  for (const vector of references.vectors.slice(1)) {
    const p = standard.samples[vector.minutesSinceEpoch];
    vector.position.forEach((v, i) => close(Object.values(p.temePositionKm)[i], v, 0.001, `${vector.minutesSinceEpoch}min r${i}`));
    vector.velocity.forEach((v, i) => close(Object.values(p.temeVelocityKmS)[i], v, 0.000001, `${vector.minutesSinceEpoch}min v${i}`));
  }
});
test('TLE and equivalent OMM give the same numerical orbit through the actual analyzer', () => {
  const json = analyzeOrbit(copy({format: 'omm', elements: omm}));
  assert.equal(json.element.catalogId, '5'); assert.equal(json.samples.length, 1441);
  for (const i of [0, 10, 360, 720, 1440]) {
    for (const key of ['x', 'y', 'z']) close(json.samples[i].temePositionKm[key], standard.samples[i].temePositionKm[key], 0.000001, `OMM match${i}${key}`);
  }
});
test('UTC fractions round-trip and midnight/year boundaries retain valid UTC values', () => {
  for (const s of ['2000-06-27T18:50:19.733568Z', '2000-12-31T23:59:59.999999Z', '2000-02-29T00:00:00.123456Z']) assert.equal(formatUtc(parseUtc(s)), s);
  assert.equal(formatUtc(parseUtc('2000-12-31T23:59:59Z') + 1000), '2001-01-01T00:00:00.000000Z');
});
test('invalid dates, absent UTC marker, leap second and unsupported years are rejected without normalization', () => {
  for (const s of ['2001-02-29T00:00:00Z', '2000-06-31T00:00:00Z', '2000-06-27T24:00:00Z', '2000-06-27T18:50:60Z', '2000-06-27T18:50:19+00:00', '2000-06-27T18:50:19', '2057-01-01T00:00:00Z']) rejects(copy({startUtc: s}), 'invalid_utc');
});
test('bad checksum is rejected before propagation', () => rejects(copy({elements: tle.replace('4753', '4754')}), 'tle_checksum'));
test('different catalog numbers are rejected even with recomputed checksums', () => rejects(copy({elements: changeTle(2, 2, '00006')}), 'invalid_tle'));
test('extra line columns, appended simulation directives and missing fields are rejected', () => {
  rejects(copy({elements: tle.trimEnd() + ' 0.00 4320 360'}), 'invalid_tle');
  rejects(copy({elements: tle.replace('1 00005', '100005')}), 'invalid_tle');
});
test('fixed-column punctuation, malformed number and unsupported ephemeris are rejected', () => {
  rejects(copy({elements: changeTle(1, 17, 'X')}), 'invalid_tle');
  rejects(copy({elements: changeTle(2, 8, ' NaN.000')}), 'invalid_tle');
  rejects(copy({elements: changeTle(1, 62, '1')}), 'invalid_tle');
});
test('invalid epoch day and physically unsupported mean motion or angle are rejected', () => {
  rejects(copy({elements: changeTle(1, 20, '000.78495062')}), 'invalid_tle');
  rejects(copy({elements: changeTle(2, 52, '99.82419157')}), 'invalid_tle');
  rejects(copy({elements: changeTle(2, 17, '360.0000')}), 'invalid_tle');
});
test('Alpha-5 catalog identifiers retain their data identity without changing orbital values', () => {
  let lines = tle.trimEnd().split('\n');
  for (const i of [1, 2]) lines[i] = checksum(lines[i].slice(0, 2) + 'A0000' + lines[i].slice(7));
  const r = quick({elements: lines.join('\n')});
  assert.equal(r.element.catalogId, '100000'); assert.deepEqual(r.samples[0].temePositionKm, standard.samples[0].temePositionKm);
});
test('OMM rejects duplicate keys, including differently escaped duplicate names', () => {
  rejects(copy({format: 'omm', elements: omm.replace('"NORAD_CAT_ID": 5', '"NORAD_CAT_ID":5,"NORAD_CAT_ID":5')}), 'duplicate_json_key');
  assert.throws(() => readStrictJson('{"EPOCH":1,"\\u0045POCH":2}'), e => e.code === 'duplicate_json_key');
});
test('OMM rejects incompatible body, frame, time system and theory', () => {
  for (const [key, value] of Object.entries({CENTER_NAME: 'MARS', REF_FRAME: 'ITRF', TIME_SYSTEM: 'TAI', MEAN_ELEMENT_THEORY: 'KEPLER', EPHEMERIS_TYPE: 2})) {
    rejects(copy({format: 'omm', elements: JSON.stringify({...JSON.parse(omm), [key]: value})}), 'unsupported_omm');
  }
});
test('OMM numeric strings, booleans, nonfinite values, unknown fields and arrays cannot be reinterpreted as valid elements', () => {
  for (const update of [{NORAD_CAT_ID: '5'}, {MEAN_MOTION: true}, {MEAN_MOTION: 0}, {UNKNOWN: 1}, {ECCENTRICITY: 1}, {NORAD_CAT_ID: 5.1}]) rejects(copy({format: 'omm', elements: JSON.stringify({...JSON.parse(omm), ...update})}), 'invalid_omm');
  for (const text of ['[]', 'null', '{"EPOCH":NaN}', omm + '\u00a0']) rejects(copy({format: 'omm', elements: text}), 'invalid_omm');
});
test('OMM standard epoch without Z is explicitly interpreted as UTC, with supported metadata unchanged', () => {
  const obj = JSON.parse(omm); obj.EPOCH = obj.EPOCH.slice(0, -1);
  assert.deepEqual(quick({format: 'omm', elements: JSON.stringify(obj)}).samples[0].temePositionKm, standard.samples[0].temePositionKm);
});
test('date window is bounded against element epoch at both ends, and age is reported honestly', () => {
  rejects(copy({startUtc: '2000-07-04T18:50:19.733568Z', durationHours: 0.25}), 'epoch_window');
  rejects(copy({startUtc: '2000-06-20T18:50:18.733568Z', durationHours: 0.25}), 'epoch_window');
  const r = quick({startUtc: '2000-07-01T00:00:00Z'}); assert.ok(r.warnings.some(s => s.includes('超过 3 日')));
});
test('all numeric controls are finite and input/object keys remain allowlisted', () => {
  for (const update of [{durationHours: '24'}, {stepSeconds: 60.5}, {stepSeconds: 0}, {minimumElevationDeg: Infinity}, {extra: 1}]) rejects(copy(update), 'invalid_parameter');
  for (const observer of [{...base.observer, latitudeDeg: 90}, {...base.observer, longitudeDeg: 181}, {...base.observer, heightM: -1}, {...base.observer, unknown: 1}]) rejects(copy({observer}), 'invalid_parameter');
  rejects(copy({elements: 'x'.repeat(16385)}), 'invalid_elements');
});
test('maximum admitted sampling window is complete, finite and includes both endpoints', () => {
  const r = analyzeOrbit(copy({stepSeconds: 10})); assert.equal(r.samples.length, 8641);
  assert.equal(r.samples.at(-1).utc, r.endUtc);
  for (const s of r.samples) for (const key of ['latitudeDeg', 'longitudeDeg', 'heightKm', 'azimuthDeg', 'elevationDeg', 'rangeKm']) assert.ok(Number.isFinite(s[key]), key);
});
test('observer changes affect look angles but cannot alter the underlying TEME orbit', () => {
  const a = quick(); const b = quick({observer: {latitudeDeg: 51, longitudeDeg: -1, heightM: 120}});
  assert.deepEqual(a.samples.map(x => x.temePositionKm), b.samples.map(x => x.temePositionKm));
  assert.notEqual(a.samples[0].azimuthDeg, b.samples[0].azimuthDeg); assert.notEqual(a.samples[0].rangeKm, b.samples[0].rangeKm);
});
test('geometric threshold crossings are genuinely bracketed within one second', () => {
  assert.equal(standard.intervals.length, 7);
  const interval = standard.intervals[0]; assert.equal(interval.startClipped, false); assert.equal(interval.endClipped, false);
  const at = utc => quick({startUtc: utc, stepSeconds: 10}).samples[0].elevationDeg;
  const start = parseUtc(interval.startUtc), end = parseUtc(interval.endUtc);
  assert.ok(at(formatUtc(start - 1000)) < 10); assert.ok(at(formatUtc(start + 1000)) > 10);
  assert.ok(at(formatUtc(end - 1000)) > 10); assert.ok(at(formatUtc(end + 1000)) < 10);
});
test('no-pass windows return an empty interval list rather than fabricated passes', () => assert.equal(analyzeOrbit(copy({minimumElevationDeg: 89})).intervals.length, 0));
test('clipped intervals preserve window boundaries and sampled-peak limitations', () => {
  const p = standard.samples[0];
  const r = quick({observer: {latitudeDeg: p.latitudeDeg, longitudeDeg: p.longitudeDeg, heightM: 0}, minimumElevationDeg: 0});
  assert.equal(r.intervals[0].startClipped, true); assert.equal(r.intervals[0].startUtc, r.startUtc);
  assert.ok(r.warnings.some(s => s.includes('最高仰角来自采样点')));
  const d = analyzeOrbit(copy({elements: deepTle, startUtc: '2004-01-31T21:51:25.308576Z', durationHours: 0.25}));
  const q = d.samples[0];
  const clipped = analyzeOrbit(copy({elements: deepTle, startUtc: d.startUtc, durationHours: 0.25, observer: {latitudeDeg: q.latitudeDeg, longitudeDeg: q.longitudeDeg, heightM: 0}, minimumElevationDeg: 0}));
  assert.equal(clipped.intervals[0].endClipped, true); assert.equal(clipped.intervals[0].endUtc, clipped.endUtc);
});
test('deep-space cache does not leak between nonmonotonic refinements, repeated analyses or observer changes', () => {
  const inp = copy({elements: deepTle, startUtc: '2004-01-31T21:51:25.308576Z', durationHours: 24, stepSeconds: 60});
  const a = analyzeOrbit(inp); const b = analyzeOrbit(inp);
  assert.deepEqual(a, b);
  for (const i of [60, 720, 1000]) {
    const single = analyzeOrbit({...inp, startUtc: a.samples[i].utc, durationHours: 0.25});
    for (const axis of ['x', 'y', 'z']) close(single.samples[0].temePositionKm[axis], a.samples[i].temePositionKm[axis], 1e-8, `deep-space fresh${i}${axis}`);
  }
});
test('failed propagation has an explicit Chinese error and does not prevent a later valid calculation', () => {
  const obj = {...JSON.parse(omm), MEAN_MOTION: 18, ECCENTRICITY: 0.9};
  rejects(copy({format: 'omm', elements: JSON.stringify(obj)}), 'propagation_error');
  assert.equal(quick().version, '1.0.0');
});
