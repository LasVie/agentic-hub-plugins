'use strict';
importScripts('matter.js', 'engine.js');
self.onmessage = event => {
  try { self.postMessage({job: event.data.job, result: Mechanics.simulate(event.data.scene)}); }
  catch (error) { self.postMessage({job: event.data.job, error: error.message || '计算失败；没有替代结果。'}); }
};
