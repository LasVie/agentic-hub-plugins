import {parseModel} from './network.js';
import {fmt,networkSVG,resultsCSV} from './presentation.js';
const $=id=>document.getElementById(id), source=$('source'), exports=['json','report','csv','svg'];
let imported='', result=null, previous=null, worker=null, timer=null, inputEpoch=0;
function message(text,error=false){$('message').textContent=text;$('message').className=error?'error':'';}
function stop(){if(worker)worker.terminate();worker=null;clearTimeout(timer);$('run').disabled=false;$('cancel').disabled=true;}
function invalidate(){inputEpoch++;stop();result=null;exports.forEach(id=>$(id).disabled=true);$('state').textContent='输入已变更 · 待求解';$('diagram').replaceChildren(Object.assign(document.createElement('div'),{className:'empty',textContent:'旧结果已失效，请重新求解'}));['nodes','pipes','warnings','modelname'].forEach(id=>$(id).replaceChildren());['total','minimum','residual'].forEach(id=>$(id).textContent='—');$('comparison').textContent='输入已更改，旧结果不可导出。';message('输入已更改，请运行求解；导入原文仍保留。');}
function selectors(){
  try{const m=parseModel(source.value);const oldPipe=$('pipe').value,oldJ=$('junction').value;
    for(const [id,items] of [['pipe',m.pipes],['junction',m.nodes.filter(n=>n.type==='junction')]]){$(id).replaceChildren(...items.map(n=>new Option(n.id,n.id)));if(items.some(n=>n.id===(id==='pipe'?oldPipe:oldJ)))$(id).value=id==='pipe'?oldPipe:oldJ;}
    $('diameter').value=m.pipes.find(p=>p.id===$('pipe').value)?.diameter_mm??'';$('demand').value=m.nodes.find(n=>n.id===$('junction').value)?.demand_lps??'';
  }catch{for(const id of ['pipe','junction'])$(id).replaceChildren();$('diameter').value='';$('demand').value='';}
}
function change(kind){try{const m=parseModel(source.value);if(kind==='pipe')m.pipes.find(p=>p.id===$('pipe').value).diameter_mm=Number($('diameter').value);else m.nodes.find(n=>n.id===$('junction').value).demand_lps=Number($('demand').value);source.value=JSON.stringify(m,null,2);invalidate();}catch{invalidate();message('请先载入有效模型，再编辑参数。',true);}}
function table(id,rows){$(id).replaceChildren(...rows.map(row=>{const tr=document.createElement('tr');for(const value of row)tr.append(Object.assign(document.createElement('td'),{textContent:String(value)}));return tr;}));}
function display(r){result=r;$('state').textContent=r.analysis_complete?(r.warnings.length?'求解完成 · 有警告':'求解完成'):'未收敛 · 仅诊断';$('modelname').textContent=r.model.name;
  const doc=new DOMParser().parseFromString(networkSVG(r),'image/svg+xml');$('diagram').replaceChildren(doc.documentElement);
  $('diagram').querySelectorAll('[role=button]').forEach(el=>{const select=()=>{if(el.dataset.pipe){$('pipe').value=el.dataset.pipe;selectors();}else if(r.nodes.find(n=>n.id===el.dataset.node)?.type==='junction'){$('junction').value=el.dataset.node;selectors();}};el.addEventListener('click',select);el.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();select();}});});
  $('total').textContent=fmt(r.model.nodes.filter(n=>n.type==='junction').reduce((s,n)=>s+n.demand_lps,0));
  const minimum=Math.min(...r.nodes.filter(n=>n.pressure_m!==null).map(n=>n.pressure_m));$('minimum').textContent=fmt(minimum);$('residual').textContent=r.max_continuity_residual_lps.toExponential(2);
  $('warnings').textContent=r.warnings.map(w=>`警告 ${w.code}：${w.message}`).join('；');
  table('nodes',r.nodes.map(n=>[n.id,n.type==='reservoir'?'水库':'需水节点',fmt(n.head_m),fmt(n.pressure_m),fmt(n.demand_lps)]));table('pipes',r.pipes.map(p=>[p.id,`${p.from} → ${p.to}`,fmt(p.flow_lps),fmt(p.velocity_mps),fmt(p.headloss_m)]));
  $('comparison').textContent=previous&&r.analysis_complete?`上一有效方案最低压力 ${fmt(previous.minimum)} m；本次变化 ${fmt(minimum-previous.minimum)} m。不同拓扑的最低点可能不同。`:'这是首个有效方案；调整管径或需水量后可比较最低压力变化。';
  if(r.analysis_complete)previous={minimum};exports.forEach(id=>$(id).disabled=!r.analysis_complete);message(r.analysis_complete?(r.warnings.length?'计算完成但有警告，请先核对；导出将包含警告。':'求解完成。结果对应当前模型，可导出。'):'未完成可靠求解，结果仅供诊断；导出已禁用。',!r.analysis_complete);
}
async function load(name){invalidate();const epoch=inputEpoch;try{const response=await fetch(`${name}.json`);if(!response.ok)throw Error();const text=await response.text();if(epoch!==inputEpoch)return;imported=text;source.value=text;selectors();message('已载入公开虚构模型；点击运行稳态求解。');}catch{if(epoch===inputEpoch)message('无法读取本地示例。',true);}}
$('example').onclick=()=>load('loop');$('single').onclick=()=>load('one-pipe');
source.addEventListener('input',()=>{invalidate();selectors();});$('pipe').onchange=selectors;$('junction').onchange=selectors;$('diameter').oninput=()=>change('pipe');$('demand').oninput=()=>change('junction');
$('restore').onclick=()=>{source.value=imported;invalidate();selectors();message('已恢复导入原文；请重新运行求解。');};
$('file').onchange=async e=>{const f=e.target.files[0];if(!f)return;invalidate();const epoch=inputEpoch;if(f.size>65536){message('文件超过 64 KiB；当前文本未覆盖。',true);return;}try{const text=await f.text();if(epoch!==inputEpoch)return;parseModel(text);source.value=text;imported=text;selectors();message('已导入模型，原文件未修改。');}catch(err){if(epoch===inputEpoch)message(`${err.message || '文件读取失败'}（${err.code || 'read_failed'}）`,true);}finally{e.target.value='';}};
$('run').onclick=()=>{invalidate();try{parseModel(source.value);}catch(e){message(`${e.message}（${e.code}）`,true);return;}$('run').disabled=true;$('cancel').disabled=false;$('state').textContent='正在计算';message('本地 EPANET 引擎正在求解…');try{worker=new Worker(new URL('./worker.js',import.meta.url),{type:'module'});worker.onmessage=({data})=>{stop();if(data.ok)display(data.result);else{$('state').textContent='计算失败';message(`${data.error.message}（${data.error.code}）`,true);}};worker.onerror=()=>{stop();$('state').textContent='引擎不可用';message('本地计算线程未能载入；请核对安装文件，并使用支持 WebAssembly SIMD 的新版浏览器。（worker_failed）',true);};timer=setTimeout(()=>{stop();$('state').textContent='已超时';message('计算超过 12 秒，已结束线程；请简化模型后重试。',true);},12000);worker.postMessage({text:source.value});}catch{stop();message('无法启动浏览器计算线程。',true);}};
$('cancel').onclick=()=>{invalidate();$('state').textContent='已取消';message('计算已取消，线程已释放；输入保留。');};
function download(name,mime,text){if(!result?.analysis_complete)return;const url=URL.createObjectURL(new Blob([text],{type:mime}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('json').onclick=()=>download('管网模型.json','application/json;charset=utf-8',JSON.stringify(result?.model,null,2));$('report').onclick=()=>download('管网水力结果.json','application/json;charset=utf-8',JSON.stringify(result,null,2));$('csv').onclick=()=>download('管网水力结果.csv','text/csv;charset=utf-8',resultsCSV(result));$('svg').onclick=()=>download('管网流向与压力.svg','image/svg+xml;charset=utf-8',networkSVG(result));
load('loop');
