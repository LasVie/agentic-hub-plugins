'use strict';
const $ = id => document.getElementById(id);
let worker = null, timer = null, sequence = 0, result = null, baseline = '', display = null;
const message = (text, error=false) => { $('message').textContent=text; $('message').classList.toggle('error',error); };
function stop() { sequence++; if(worker)worker.terminate();worker=null;clearTimeout(timer);$('run').disabled=false;$('cancel').disabled=true; }
function clearResult() {
  stop();result=null;display=null;$('export-geojson').disabled=true;$('export-svg').disabled=true;
  for(const id of ['before-vertices','after-vertices','reduction','output-bytes'])$(id).textContent='—';
  $('losses').hidden=true;$('detail').textContent='运行后显示要素、环、组成部分及文件大小的前后对照。';$('state').textContent='待重新计算';$('feature').replaceChildren(new Option('暂无要素',''));$('feature').disabled=true;$('properties').textContent='输入已更改；旧结果已清除。';
  $('map').replaceChildren();const p=document.createElement('p');p.className='muted';p.textContent='输入或设置更改后，请运行简化。';$('map').append(p);
}
function invalidate() {clearResult();message('输入或设置已更改，旧结果与导出已失效。');}
function load(text) {clearResult();baseline=text;$('source').value=text;$('reset').disabled=false;message('已载入原文；点击“运行简化”。原文件不会被修改。');}
function draw() {
  if(!display)return;
  const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 960 600');svg.setAttribute('role','img');svg.setAttribute('aria-label','原图与简化结果边界对照');
  const original=GeoLab.drawing(display.original);
  // Results drawn first; original dashed outlines remain visible above them.
  for(const [kind,fc,show] of [['result',display.result,$('show-result').checked],['original',display.original,$('show-original').checked]]) {
    if(!fc||!show)continue;const group=document.createElementNS(ns,'g');group.setAttribute('class',kind);
    for(const d of GeoLab.drawing(fc,original.bounds).paths){const path=document.createElementNS(ns,'path');path.setAttribute('d',d);group.append(path);}svg.append(group);
  }
  $('map').replaceChildren(svg);
}
function properties() {
  if(!display)return;const i=Number($('feature').value);const f=(display.result||display.original).features[i];
  $('properties').textContent=JSON.stringify({index:i,...(Object.prototype.hasOwnProperty.call(f,'id')?{id:f.id}:{}),properties:f.properties},null,2);
}
function showFeatures(fc) {$('feature').replaceChildren(...fc.features.map((f,i)=>new Option(`${i+1} · ${Object.prototype.hasOwnProperty.call(f,'id')?String(f.id):'无 id'}`,String(i))));$('feature').disabled=false;properties();}
$('source').addEventListener('input',invalidate);
$('percent').addEventListener('input',()=>{$('percent-label').textContent=$('percent').value+'%';invalidate();});
$('file').addEventListener('change',async()=>{const f=$('file').files[0];if(!f)return;clearResult();const current=sequence;if(f.size>GeoLab.LIMITS.bytes){message('文件超过 2 MiB 限制。(input_limit)',true);return;}try{const text=await f.text();if(current===sequence)load(text);}catch(_){if(current===sequence)message('无法读取本地文件。',true);}});
$('example').addEventListener('click',async()=>{clearResult();const current=sequence;try{const r=await fetch('../examples/adjacent-regions.geojson');if(!r.ok)throw Error();const text=await r.text();if(current===sequence)load(text);}catch(_){if(current===sequence)message('无法载入本地示例；请检查插件安装。',true);}});
$('reset').addEventListener('click',()=>{load(baseline);$('percent').value='100';$('percent-label').textContent='100%';message('已恢复导入原文，比例设为 100%；运行后可重新检查结果。');});
$('cancel').addEventListener('click',()=>{clearResult();$('state').textContent='已取消';message('计算已取消，旧结果不可导出。');});
$('feature').addEventListener('change',properties);
for(const id of ['show-original','show-result'])$(id).addEventListener('change',draw);
$('run').addEventListener('click',()=>{
  const text=$('source').value,percent=Number($('percent').value);clearResult();const current=sequence;
  try {const original=GeoLab.read(text);display={original};draw();showFeatures(original);if(!baseline){baseline=text;$('reset').disabled=false;}}
  catch(e){message(`${e.message} (${e.code||'invalid_input'})`,true);$('state').textContent='输入无效';return;}
  $('run').disabled=true;$('cancel').disabled=false;$('state').textContent='计算中';message('正在独立工作线程内简化；原文未修改。');
  const failed=(code,text)=>{clearResult();$('state').textContent='未完成';message(`${text} (${code})`,true);};
  try{worker=new Worker('simplify-worker.js');}catch(_){failed('worker_unavailable','无法启动本地计算线程；请检查浏览器及插件完整性。');return;}
  timer=setTimeout(()=>{if(current===sequence)failed('timeout','计算超过 12 秒，已终止线程。请减少输入。');},GeoLab.LIMITS.timeout);
  worker.onerror=()=>{if(current===sequence)failed('engine_load_failed','引擎未能加载或运行；请检查插件文件及浏览器支持。');};
  worker.onmessage=event=>{
    if(current!==sequence)return;const data=event.data;
    if(!data.ok){failed(data.error.code,data.error.message);return;}stop();result=data.value;display=result;
    $('state').textContent='简化完成';draw();showFeatures(result.result);
    $('before-vertices').textContent=result.before.vertices.toLocaleString();$('after-vertices').textContent=result.after.vertices.toLocaleString();
    $('reduction').textContent=(100*(1-result.after.vertices/result.before.vertices)).toFixed(1)+'%';$('output-bytes').textContent=result.after.bytes.toLocaleString();
    $('detail').textContent=`要素 ${result.before.features} → ${result.after.features}；环 ${result.before.rings} → ${result.after.rings}；组成部分 ${result.before.parts} → ${result.after.parts}。紧凑 JSON ${result.before.bytes} → ${result.after.bytes} 字节；原文件 ${result.original_file_bytes} 字节。顶点不计闭合重复点。`;
    if(result.losses.length){$('losses').hidden=false;$('losses').textContent='简化损失提醒：小岛或孔洞可能消失。\n'+result.losses.map(x=>`要素 ${x.index+1}：减少 ${x.removed_rings} 个环、${x.removed_parts} 个组成部分。`).join('\n');}
    $('export-geojson').disabled=false;$('export-svg').disabled=false;message(result.losses.length?'计算完成，但存在环或组成部分损失。请对照原图后决定是否导出。':'计算完成。结果与当前输入和比例一致，可以导出。');
  };
  worker.postMessage({text,percent});
});
function download(kind){if(!result)return;const content=kind==='geojson'?JSON.stringify(result.result):GeoLab.svg(result.result),blob=new Blob([content],{type:kind==='geojson'?'application/geo+json;charset=utf-8':'image/svg+xml;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`地图简化-${result.percent}pct.${kind}`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('export-geojson').addEventListener('click',()=>download('geojson'));$('export-svg').addEventListener('click',()=>download('svg'));
