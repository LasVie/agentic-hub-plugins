import {parseModel} from './network.js';
import {solveNetwork} from './hydraulics.js';
self.onmessage = async ({data}) => {
  try { self.postMessage({ok:true,result:await solveNetwork(parseModel(data.text))}); }
  catch(e) { self.postMessage({ok:false,error:{code:e.code || 'engine_failed',message:e.code ? e.message : '无法载入或运行本地水力引擎；请核对浏览器支持后重试。'}}); }
};
