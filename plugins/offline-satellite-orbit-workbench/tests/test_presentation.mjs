// Focused presentation regressions. DOM checks use real jsdom when available via
// NODE_PATH (test-only dependency); they are explicitly skipped when unavailable.
// These checks do not establish browser rendering, downloads or host dispatch.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import {analyzeOrbit} from '../offline-satellite-orbit-workbench/web/engine.js';
import {numberText, utcText, splitGroundTrack, exportCsv, groundTrackSvg, elevationSvg, exportSvg} from '../offline-satellite-orbit-workbench/web/presentation.js';

let JSDOM;
try { ({JSDOM} = createRequire(import.meta.url)('jsdom')); } catch (error) {
  if (error.code !== 'MODULE_NOT_FOUND') throw error;
}
const domOptions = {skip: !JSDOM && 'jsdom is unavailable; set NODE_PATH to an installed test-only jsdom module'};
const result = analyzeOrbit({
  format: 'tle',
  elements: fs.readFileSync(new URL('./fixtures/00005.tle', import.meta.url), 'utf8'),
  startUtc: '2000-06-27T18:50:19.733568Z',
  durationHours: 24,
  stepSeconds: 60,
  observer: {latitudeDeg: 1.3521, longitudeDeg: 103.8198, heightM: 0},
  minimumElevationDeg: 10,
});

test('number formatting preserves integer zeroes and UTC microseconds', () => {
  assert.equal(numberText(180, 0), '180');
  assert.equal(numberText(1000, 0), '1000');
  assert.equal(numberText(180.25, 3), '180.25');
  assert.equal(numberText(-0.001, 3), '-0.001');
  assert.equal(numberText(NaN), '—');
  assert.equal(utcText(result.startUtc), '2000-06-27 18:50:19.733568 Z');
});

test('eastward dateline crossing splits and interpolates both seam endpoints', () => {
  const points = [{longitudeDeg: 179, latitudeDeg: 10}, {longitudeDeg: -179, latitudeDeg: 12}];
  const before = structuredClone(points);
  assert.deepEqual(splitGroundTrack(points), [
    [{longitudeDeg: 179, latitudeDeg: 10}, {longitudeDeg: 180, latitudeDeg: 11}],
    [{longitudeDeg: -180, latitudeDeg: 11}, {longitudeDeg: -179, latitudeDeg: 12}],
  ]);
  assert.deepEqual(points, before);
});

test('westward dateline crossing and actual orbit never draw a longitude jump over 180 degrees', () => {
  assert.deepEqual(splitGroundTrack([{longitudeDeg: -179, latitudeDeg: 10}, {longitudeDeg: 179, latitudeDeg: 12}]), [
    [{longitudeDeg: -179, latitudeDeg: 10}, {longitudeDeg: -180, latitudeDeg: 11}],
    [{longitudeDeg: 180, latitudeDeg: 11}, {longitudeDeg: 179, latitudeDeg: 12}],
  ]);
  const segments = splitGroundTrack(result.samples);
  assert.ok(segments.length > 2);
  for (const segment of segments) for (let i = 1; i < segment.length; i++) {
    assert.ok(Math.abs(segment[i].longitudeDeg - segment[i - 1].longitudeDeg) <= 180);
  }
  assert.deepEqual(splitGroundTrack([]), []);
});

test('CSV exports every actual sample with BOM, units, full values and correct string escaping', () => {
  const csv = exportCsv(result);
  assert.ok(csv.startsWith('\uFEFF'));
  assert.ok(csv.endsWith('\r\n'));
  const lines = csv.slice(1).trimEnd().split('\r\n');
  assert.equal(lines.length, result.samples.length + 1);
  assert.match(lines[0], /椭球高（km）/);
  assert.match(lines[0], /TEME速度x（km\/s）/);
  assert.match(lines[1], new RegExp(`^"${result.startUtc}"`));
  assert.ok(lines[1].includes(`"${result.samples[0].temePositionKm.x}"`));
  assert.ok(lines.at(-1).startsWith(`"${result.endUtc}"`));
  for (const prefix of ['=', '+', '-', '@', '\t', '\r']) {
    const text = exportCsv({...result, element: {...result.element, catalogId: `${prefix}SUM(1,2)"`}});
    assert.ok(text.includes(`"'${prefix}SUM(1,2)"""`));
  }
  assert.ok(csv.includes(`"${result.samples[0].elevationDeg}"`));
  assert.ok(!csv.includes(`"'${result.samples[0].elevationDeg}"`), 'negative numerical values are not text-prefixed');
});

test('plots build real SVG DOM with fixed safe element and attribute types', domOptions, () => {
  const dom = new JSDOM('<!doctype html><html><body></body></html>');
  globalThis.document = dom.window.document;
  try {
    for (const plot of [groundTrackSvg(result, 360), elevationSvg(result, 360)]) {
      assert.equal(plot.namespaceURI, 'http://www.w3.org/2000/svg');
      assert.equal(plot.getAttribute('role'), 'img');
      assert.ok(plot.querySelector('title').textContent.length > 0);
      assert.ok(plot.querySelectorAll('path').length > 0);
      assert.equal(plot.querySelectorAll('script, foreignObject, image, use, a').length, 0);
      for (const node of plot.querySelectorAll('*')) for (const attribute of node.attributes) {
        assert.ok(!/^on/i.test(attribute.name));
        assert.ok(!/javascript:/i.test(attribute.value));
        assert.ok(!/NaN|Infinity/.test(attribute.value));
      }
    }
  } finally { delete globalThis.document; dom.window.close(); }
});

test('standalone SVG export uses the real XML serializer and keeps metadata as text', domOptions, () => {
  const dom = new JSDOM('<!doctype html><html><body></body></html>');
  globalThis.document = dom.window.document;
  globalThis.XMLSerializer = dom.window.XMLSerializer;
  try {
    const maliciousId = '<script>not code</script> & "satellite"';
    const xml = exportSvg({...result, element: {...result.element, catalogId: maliciousId}}, 360);
    const parsed = new dom.window.DOMParser().parseFromString(xml, 'image/svg+xml');
    assert.equal(parsed.querySelectorAll('parsererror').length, 0);
    const svg = parsed.documentElement;
    assert.equal(svg.namespaceURI, 'http://www.w3.org/2000/svg');
    assert.equal(svg.getAttribute('viewBox'), '0 0 1040 990');
    assert.equal(svg.querySelectorAll('svg').length, 2);
    assert.equal(svg.querySelectorAll('script, foreignObject, image, use, a').length, 0);
    assert.ok(svg.textContent.includes(maliciousId));
    assert.ok(svg.textContent.includes(result.startUtc));
    assert.ok(svg.textContent.includes('椭球高 0 m'));
    assert.ok(svg.textContent.includes('不代表实际可见'));
    assert.ok(xml.includes('&lt;script&gt;'));
  } finally {
    delete globalThis.document;
    delete globalThis.XMLSerializer;
    dom.window.close();
  }
});
