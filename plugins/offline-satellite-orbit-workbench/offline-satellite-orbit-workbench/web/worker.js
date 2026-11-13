import {analyzeOrbit} from './engine.js';
self.onmessage = event => {
  const {id, input} = event.data || {};
  try { self.postMessage({id, result: analyzeOrbit(input)}); }
  catch (error) { self.postMessage({id, error: {code: error.code || 'calculation_failed', message: error.code ? error.message : '轨道计算失败；请核对输入或重新载入公开示例。'}}); }
};
