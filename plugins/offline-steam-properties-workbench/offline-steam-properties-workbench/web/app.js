import {exampleProject,clone,displayNumber as fmt,pressureKpa,temperatureC,temperatureK,kiloEnergy,validateProject,projectJson,parseProject,phaseLabel,chartData,nearestIndex,resultCsv,MAX_PROJECT_BYTES} from './ui_helpers.mjs';

const $=id=>document.getElementById(id);
const VERSION='1.0.0';
let draft=exampleProject(),result=null,saved=null,ready=false,closed=false,pending=null,generation=0;
let plot=null,pointIndex=0;
let examples={saturated:exampleProject(),mixture:{...exampleProject(),name:'湿蒸汽',state:{pair:'PQ',pressure_pa:101325,quality:.5}},superheated:{...exampleProject(),name:'过热蒸汽',state:{pair:'PT',pressure_pa:101325,temperature_k:473.15}},temperature:{...exampleProject(),name:'温度扫描',state:{pair:'TQ',temperature_k:373.15,quality:1},sweep:{variable:'temperature_k',start:300,end:620,points:25}}};
function stable(value){if(Array.isArray(value))return '['+value.map(stable).join(',')+']';if(value&&typeof value==='object')return '{'+Object.keys(value).sort().map(key=>JSON.stringify(key)+':'+stable(value[key])).join(',')+'}';return JSON.stringify(value);}
function status(message,kind=''){ $('status').textContent=message;$('status').className='status '+kind; }
function message(error){return typeof error==='string'?error:typeof error?.message==='string'?error.message:'操作未完成，请检查输入或本机服务。';}
function controls(){
  const locked=!ready||closed||!!pending;
  $('editor-fields').disabled=locked;
  for(const id of ['calculate','save','reset','import','export-project','shutdown'])$(id).disabled=locked;
  $('cancel').disabled=closed||pending?.kind!=='calculate';
  for(const id of ['export-csv','export-svg','curve'])$(id).disabled=locked||!result;
  const dirty=saved!==stable(draft);$('saved-status').textContent=closed?'已关闭':!ready?'正在读取':dirty?'输入有修改':'输入已保存';$('saved-status').className='tag'+(dirty?' dirty':'');
}
function clearResult(){
  result=null;plot=null;pointIndex=0;
  for(const id of ['state-results','saturation-results','chart-content'])$(id).hidden=true;
  for(const id of ['state-empty','saturation-empty','chart-empty'])$(id).hidden=false;
  $('phase').textContent='尚未计算';$('saturation-point').textContent='尚未计算';
  $('raw-body').replaceChildren();$('chart').replaceChildren();$('chart-readout').textContent='';
  controls();
}
function edited(){if(!ready||closed||pending)return;generation++;clearResult();$('example').value='custom';status('输入已修改，旧结果已清除。请保存或重新计算。');controls();}
function numberValue(id,convert=value=>value){const value=$(id).value;return value.trim()===''?null:convert(Number(value));}
function renderExamples(){
  $('example').replaceChildren();
  const custom=document.createElement('option');custom.value='custom';custom.textContent='自定义输入';$('example').append(custom);
  for(const [key,project]of Object.entries(examples)){const option=document.createElement('option');option.value=key;option.textContent=project.name;$('example').append(option);}
}
function renderForm(){
  const state=draft.state,sweep=draft.sweep;
  $('project-name').value=draft.name;$('pair').value=state.pair;
  $('pressure-field').hidden=state.pair==='TQ';$('temperature-field').hidden=state.pair==='PQ';$('quality-field').hidden=state.pair==='PT';
  $('pressure').value=state.pressure_pa===undefined?'':pressureKpa(state.pressure_pa);
  $('temperature').value=state.temperature_k===undefined?'':temperatureC(state.temperature_k);
  $('quality').value=state.quality??'';
  $('temperature').min='0.01';$('temperature').max=state.pair==='PT'?'526.85':'366.85';
  $('sweep-variable').value=sweep.variable;
  const isPressure=sweep.variable==='pressure_pa';
  for(const part of ['start','end']){$('sweep-'+part).value=isPressure?pressureKpa(sweep[part]):temperatureC(sweep[part]);$('sweep-'+part+'-unit').textContent=isPressure?'kPa':'°C';$('sweep-'+part).min=isPressure?'1':'0.01';$('sweep-'+part).max=isPressure?'20000':'366.85';}
  $('points').value=sweep.points;
  $('example').value=Object.keys(examples).find(key=>stable(examples[key])===stable(draft))||'custom';
  controls();
}
async function request(path,body,signal){
  let response,data;
  try{response=await fetch(new URL('api/'+path,location.href),{method:body===undefined?'GET':'POST',headers:{Accept:'application/json',...(body===undefined?{}:{'Content-Type':'application/json'})},...(body===undefined?{}:{body:JSON.stringify(body)}),credentials:'omit',cache:'no-store',signal});data=await response.json();}
  catch(error){if(error.name==='AbortError')throw error;throw new Error('本机服务未返回有效响应。请通过插件工具查询状态，必要时重新启动工作台。');}
  if(!response.ok||data?.ok!==true)throw new Error(message(data?.error));
  return data;
}
function begin(kind){const task={kind,epoch:++generation,controller:new AbortController(),request_id:'steam_'+crypto.randomUUID().replaceAll('-','')};pending=task;controls();return task;}
function current(task){return pending===task&&task.epoch===generation&&!closed;}
function finish(task){if(pending===task){pending=null;controls();}}
function requestedProject(){const project=clone(draft);project.name=project.name.trim();return validateProject(project);}
async function calculate(){
  if(!ready||closed||pending)return;
  let project;try{project=requestedProject();}catch(error){clearResult();status(message(error),'error');return;}
  clearResult();const task=begin('calculate');status('正在调用 CoolProp，计算单点状态与饱和曲线…');
  try{
    const answer=await request('calculate',{request_id:task.request_id,project},task.controller.signal);
    if(!current(task))return;
    if(answer.request_id!==task.request_id||answer.engine?.name!=='CoolProp'||answer.engine?.version!=='8.0.0'||answer.engine?.backend!=='HEOS'||answer.engine?.fluid!=='Water'||stable(answer.input)!==stable(project))throw new Error('计算响应与本次输入或固定引擎不匹配，已拒绝显示结果。');
    validateProject(answer.input);
    // Prepare the plot before publishing any result so malformed output cannot
    // leave a partially current report or an enabled download behind.
    chartData(answer.sweep,answer.input.sweep.variable,$('curve').value);
    result=answer;draft=clone(answer.input);saved=stable(draft);renderForm();renderResults();
    status('计算完成，输入已保存。当前数值与曲线均来自这次计算。','success');
  }catch(error){if(current(task)){clearResult();status(error.name==='AbortError'?'本次计算已取消。':message(error),'error');}}
  finally{finish(task);}
}
async function cancel(){
  const old=pending;if(old?.kind!=='calculate'||closed)return;
  old.controller.abort();const task=begin('cancel');clearResult();status('正在取消本次计算…');
  try{await request('cancel',{request_id:old.request_id},task.controller.signal);if(current(task))status('取消请求已确认，本次结果已清除。可以调整输入后重试。');}
  catch(error){if(current(task))status('取消请求未获确认；本次结果已清除。'+message(error),'error');}
  finally{finish(task);}
}
async function save(){
  if(!ready||closed||pending)return;
  let project;try{project=requestedProject();}catch(error){status(message(error),'error');return;}
  const before=stable(draft),task=begin('save');status('正在保存项目输入…');
  try{const answer=await request('project',{project},task.controller.signal);if(!current(task))return;validateProject(answer.project);draft=clone(answer.project);saved=stable(draft);if(stable(draft)!==before)clearResult();renderForm();$('load-warning').hidden=true;status('项目输入已保存。重新打开后需重新计算结果。','success');}
  catch(error){if(current(task))status(message(error),'error');}finally{finish(task);}
}
async function reset(){
  if(!ready||closed||pending)return;
  clearResult();const task=begin('reset');status('正在重置并保存默认项目…');
  try{const answer=await request('reset',{},task.controller.signal);if(!current(task))return;validateProject(answer.project);draft=clone(answer.project);saved=stable(draft);renderForm();$('load-warning').hidden=true;status('已重置并保存默认项目。请重新计算。','success');}
  catch(error){if(current(task))status(message(error),'error');}finally{finish(task);}
}
async function shutdown(){
  if(!ready||closed||pending)return;
  clearResult();const task=begin('shutdown');status('正在关闭本机工作台…');
  try{const answer=await request('shutdown',{},task.controller.signal);if(!current(task))return;if(answer.running!==false)throw new Error('服务尚未确认关闭，请重新查询状态。');closed=true;status('工作台已关闭。需要时请通过原生插件工具启动新会话。');}
  catch(error){if(current(task))status(message(error),'error');}finally{finish(task);}
}
function download(content,name,type){const url=URL.createObjectURL(new Blob([content],{type}));const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
function appendCell(row,text,tag='td'){const cell=document.createElement(tag);cell.textContent=String(text);row.append(cell);return cell;}
function renderResults(){
  const state=result.state,sat=result.saturation;
  $('phase').textContent=phaseLabel(state.phase);
  for(const [id,value]of [['state-pressure',pressureKpa(state.pressure_pa)],['state-temperature',temperatureC(state.temperature_k)],['state-density',state.density_kg_m3],['state-enthalpy',kiloEnergy(state.enthalpy_j_kg)],['state-entropy',kiloEnergy(state.entropy_j_kg_k)]])$(id).textContent=fmt(value);
  $('state-quality').textContent=state.quality===null?'不适用':fmt(state.quality);$('quality-note').textContent=state.quality===null?'当前为单相状态':'kg 蒸汽 / kg 混合物';
  $('result-source').textContent=`CoolProp ${result.engine.version} · HEOS / Water · 输入摘要 ${result.input_sha256?.slice(0,16)||'未提供'}`;
  $('saturation-point').textContent=`${fmt(pressureKpa(sat.pressure_pa))} kPa · ${fmt(temperatureC(sat.temperature_k))} °C`;
  $('saturation-body').replaceChildren();
  for(const [label,key,convert]of [['密度 / kg·m⁻³','density_kg_m3',value=>value],['比焓 / kJ·kg⁻¹','enthalpy_j_kg',kiloEnergy],['比熵 / kJ·kg⁻¹·K⁻¹','entropy_j_kg_k',kiloEnergy]]){const row=document.createElement('tr');appendCell(row,label);appendCell(row,fmt(convert(sat.liquid[key])));appendCell(row,fmt(convert(sat.vapor[key])));$('saturation-body').append(row);}
  $('latent-heat').textContent=fmt(kiloEnergy(sat.latent_heat_j_kg));
  $('raw-body').replaceChildren();result.sweep.forEach((point,index)=>{const row=document.createElement('tr');appendCell(row,index+1);for(const key of ['pressure_pa','temperature_k','liquid_density_kg_m3','vapor_density_kg_m3','liquid_enthalpy_j_kg','vapor_enthalpy_j_kg','latent_heat_j_kg'])appendCell(row,point[key]);$('raw-body').append(row);});
  $('sample-count').textContent=`${result.sweep.length} 个采样点 · 线性扫描`;
  for(const id of ['state-empty','saturation-empty','chart-empty'])$(id).hidden=true;
  for(const id of ['state-results','saturation-results','chart-content'])$(id).hidden=false;
  renderChart();controls();
}

const SVG='http://www.w3.org/2000/svg',BOX={width:900,height:420,left:88,right:28,top:48,bottom:68};
function svgNode(tag,attributes={},text){const node=document.createElementNS(SVG,tag);for(const [key,value]of Object.entries(attributes))node.setAttribute(key,String(value));if(text!==undefined)node.textContent=text;return node;}
function renderChart(){
  if(!result)return;
  plot=chartData(result.sweep,result.input.sweep.variable,$('curve').value);pointIndex=Math.min(pointIndex,plot.x.length-1);
  const svg=$('chart');svg.replaceChildren();svg.setAttribute('xmlns',SVG);
  const {width,height,left,right,top,bottom}=BOX,w=width-left-right,h=height-top-bottom;
  plot.px=value=>left+(value-plot.xMin)/(plot.xMax-plot.xMin)*w;
  plot.py=value=>top+(plot.yMax-value)/(plot.yMax-plot.yMin)*h;
  svg.append(svgNode('title',{},`${result.input.name}：${plot.yLabel}，横轴${plot.xLabel}`));
  svg.append(svgNode('desc',{},'所有标记均来自本次计算的采样点，相邻点用直线连接。使用左右方向键逐点查看。'));
  svg.append(svgNode('rect',{width,height,fill:'#fcfdfe'}));
  svg.append(svgNode('text',{x:left,y:22,fill:'#284d5d','font-family':'sans-serif','font-size':13},result.input.name.length>30?result.input.name.slice(0,30)+'…':result.input.name));
  for(let i=0;i<=5;i++){
    const x=plot.xMin+(plot.xMax-plot.xMin)*i/5,y=plot.yMin+(plot.yMax-plot.yMin)*i/5;
    svg.append(svgNode('line',{x1:plot.px(x),x2:plot.px(x),y1:top,y2:height-bottom,stroke:'#e5edf1','stroke-width':1}));
    svg.append(svgNode('line',{x1:left,x2:width-right,y1:plot.py(y),y2:plot.py(y),stroke:'#e5edf1','stroke-width':1}));
    svg.append(svgNode('text',{x:plot.px(x),y:height-bottom+22,'text-anchor':'middle',fill:'#607785','font-family':'sans-serif','font-size':11},fmt(x)));
    svg.append(svgNode('text',{x:left-12,y:plot.py(y)+4,'text-anchor':'end',fill:'#607785','font-family':'sans-serif','font-size':11},fmt(y)));
  }
  svg.append(svgNode('text',{x:left+w/2,y:height-14,'text-anchor':'middle',fill:'#375767','font-family':'sans-serif','font-size':12},plot.xLabel));
  svg.append(svgNode('text',{transform:`translate(18 ${top+h/2}) rotate(-90)`,'text-anchor':'middle',fill:'#375767','font-family':'sans-serif','font-size':12},plot.yLabel));
  $('chart-legend').replaceChildren();
  plot.series.forEach((series,index)=>{
    const path=series.values.map((value,i)=>(i?'L':'M')+plot.px(plot.x[i]).toFixed(3)+','+plot.py(value).toFixed(3)).join(' ');
    svg.append(svgNode('path',{d:path,fill:'none',stroke:series.color,'stroke-width':2.5,'stroke-linejoin':'round'}));
    for(let i=0;i<plot.x.length;i++)svg.append(svgNode('circle',{cx:plot.px(plot.x[i]),cy:plot.py(series.values[i]),r:2.5,fill:series.color}));
    const legendX=width-right-plot.series.length*116+index*116;
    svg.append(svgNode('line',{x1:legendX,x2:legendX+18,y1:20,y2:20,stroke:series.color,'stroke-width':3}));
    svg.append(svgNode('text',{x:legendX+24,y:24,fill:'#375767','font-family':'sans-serif','font-size':11},series.label));
    const entry=document.createElement('span'),swatch=document.createElement('i');swatch.className=index?'vapor':'liquid';entry.append(swatch,document.createTextNode(series.label));$('chart-legend').append(entry);
  });
  svg.append(svgNode('g',{id:'point-cursor'}));renderPoint();
}
function renderPoint(){
  if(!plot||!result)return;
  const cursor=$('point-cursor');cursor.replaceChildren();const x=plot.px(plot.x[pointIndex]);
  cursor.append(svgNode('line',{x1:x,x2:x,y1:BOX.top,y2:BOX.height-BOX.bottom,stroke:'#657e8b','stroke-width':1,'stroke-dasharray':'4 4'}));
  for(const series of plot.series)cursor.append(svgNode('circle',{cx:x,cy:plot.py(series.values[pointIndex]),r:5,fill:'white',stroke:series.color,'stroke-width':2}));
  $('chart-readout').textContent=`第 ${pointIndex+1} / ${plot.x.length} 点 · ${plot.xLabel}：${fmt(plot.x[pointIndex])} · `+plot.series.map(series=>`${series.label}：${fmt(series.values[pointIndex])} ${plot.yLabel.split(' / ').at(-1)}`).join('；');
  [...$('raw-body').children].forEach((row,index)=>row.classList.toggle('selected',index===pointIndex));
}
$('chart').addEventListener('pointermove',event=>{if(!plot)return;const matrix=$('chart').getScreenCTM();if(!matrix)return;const point=$('chart').createSVGPoint();point.x=event.clientX;point.y=event.clientY;const local=point.matrixTransform(matrix.inverse());const target=plot.xMin+(local.x-BOX.left)/(BOX.width-BOX.left-BOX.right)*(plot.xMax-plot.xMin);pointIndex=nearestIndex(plot.x,target);renderPoint();});
$('chart').addEventListener('keydown',event=>{if(!plot||!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;event.preventDefault();pointIndex=event.key==='Home'?0:event.key==='End'?plot.x.length-1:Math.max(0,Math.min(plot.x.length-1,pointIndex+(event.key==='ArrowRight'?1:-1)));renderPoint();});
$('curve').addEventListener('change',()=>{try{renderChart();}catch(error){clearResult();status(message(error),'error');}});
$('project-name').addEventListener('input',()=>{if(pending||closed)return;draft.name=$('project-name').value;edited();});
for(const [id,key,convert]of [['pressure','pressure_pa',value=>value*1000],['temperature','temperature_k',temperatureK],['quality','quality',value=>value]])$(id).addEventListener('input',()=>{if(pending||closed)return;draft.state[key]=numberValue(id,convert);edited();});
$('pair').addEventListener('change',()=>{if(pending||closed)return;const old=draft.state,pair=$('pair').value;draft.state={pair,...(pair==='TQ'?{}:{pressure_pa:old.pressure_pa??101325}),...(pair==='PQ'?{}:{temperature_k:old.temperature_k??373.15}),...(pair==='PT'?{}:{quality:old.quality??0})};edited();renderForm();});
$('sweep-variable').addEventListener('change',()=>{if(pending||closed)return;const variable=$('sweep-variable').value;draft.sweep={variable,start:variable==='pressure_pa'?10000:300,end:variable==='pressure_pa'?2000000:620,points:draft.sweep.points};$('curve').value=variable==='pressure_pa'?'temperature':'pressure';edited();renderForm();});
for(const part of ['start','end'])$('sweep-'+part).addEventListener('input',()=>{if(pending||closed)return;draft.sweep[part]=numberValue('sweep-'+part,value=>draft.sweep.variable==='pressure_pa'?value*1000:temperatureK(value));edited();});
$('points').addEventListener('input',()=>{if(pending||closed)return;draft.sweep.points=numberValue('points');edited();});
$('example').addEventListener('change',()=>{if(pending||closed||!examples[$('example').value])return;draft=clone(examples[$('example').value]);generation++;clearResult();renderForm();$('curve').value=draft.sweep.variable==='pressure_pa'?'temperature':'pressure';status('示例已载入，尚未保存。请计算或保存输入。');});
$('calculate').addEventListener('click',calculate);$('cancel').addEventListener('click',cancel);$('save').addEventListener('click',save);$('reset').addEventListener('click',reset);$('shutdown').addEventListener('click',shutdown);
$('export-project').addEventListener('click',()=>{if(pending||closed)return;try{download(projectJson(requestedProject()),'水蒸气项目.json','application/json;charset=utf-8');}catch(error){status(message(error),'error');}});
$('export-csv').addEventListener('click',()=>{if(!result||pending||closed)return;try{download(resultCsv(result),'水蒸气计算结果.csv','text/csv;charset=utf-8');}catch(error){status(message(error),'error');}});
$('export-svg').addEventListener('click',()=>{if(!result||pending||closed)return;const image=$('chart').cloneNode(true);image.removeAttribute('tabindex');image.removeAttribute('aria-describedby');download('<?xml version="1.0" encoding="UTF-8"?>\n'+new XMLSerializer().serializeToString(image),'水蒸气饱和曲线.svg','image/svg+xml;charset=utf-8');});
$('import').addEventListener('change',async()=>{
  const file=$('import').files[0];$('import').value='';if(!file||pending||closed)return;
  if(file.size>MAX_PROJECT_BYTES){status('项目文件超过 256 KiB 限制。','error');return;}
  const task=begin('import');status('正在读取项目文件…');
  try{const text=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());const project=parseProject(text);if(!current(task))return;draft=clone(project);clearResult();renderForm();$('curve').value=draft.sweep.variable==='pressure_pa'?'temperature':'pressure';status('项目已导入，尚未保存或计算。请核对输入后计算。');}
  catch(error){if(current(task))status((error instanceof TypeError?'文件不是有效 UTF-8 文本。':message(error))+' 当前输入已保留。','error');}
  finally{finish(task);}
});
async function initialize(){
  const task=begin('initial');
  try{const data=await request('initial',undefined,task.controller.signal);if(!current(task))return;validateProject(data.project);draft=clone(data.project);saved=data.load_error?null:stable(draft);
    if(data.examples&&typeof data.examples==='object'&&!Array.isArray(data.examples)){const accepted={};for(const [key,value]of Object.entries(data.examples)){try{validateProject(value);accepted[key]=clone(value);}catch{}}if(Object.keys(accepted).length)examples=accepted;}
    const warnings=[...(Array.isArray(data.warnings)?data.warnings.map(message):[]),...(data.load_error?[message(data.load_error)]:[])];$('load-warning').textContent=warnings.join(' ');$('load-warning').hidden=!warnings.length;status('项目输入已读取。点击“计算状态与曲线”取得本次结果。');
  }catch(error){if(current(task)){saved=null;$('load-warning').hidden=false;$('load-warning').textContent=message(error);status('暂未读取到保存项目。默认输入已显示，可重试保存或重置。','error');}}
  finally{if(current(task)){ready=true;pending=null;renderExamples();renderForm();$('curve').value=draft.sweep.variable==='pressure_pa'?'temperature':'pressure';clearResult();controls();}}
}
initialize();
