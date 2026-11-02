/* Only this plugin's dedicated worker adapts the upstream browser globals. */
'use strict';
self.window = self;
self.document = {};
importScripts('geometry.js', 'vendor/modules.js', 'vendor/mapshaper.js');
self.onmessage = async event => {
  try { self.postMessage({ok: true, value: await GeoLab.simplify(event.data.text, event.data.percent, self.mapshaper)}); }
  catch (e) { self.postMessage({ok: false, error: {code: e.code || 'engine_error', message: e.code ? e.message : '离线计算失败，原文未修改。'}}); }
};
