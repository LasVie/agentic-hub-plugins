'use strict';

// Plugin-owned Chinese interface. Numerical paths and measurements come only
// from the local engine; this file contains drawing and editor logic, no solver.
const $ = id => document.getElementById(id);
const TYPES = {
  SingleRay: {label: '单条光线', symbol: '↗', group: 'ray', tip: '从端点 1 沿端点 2 的方向发射。亮度是相对量。'},
  Beam: {label: '平行光束', symbol: '⇉', group: 'ray', tip: '端点确定光源线段。光束沿线段的法向发射；对调端点可翻转方向。'},
  Mirror: {label: '平面反射镜', symbol: '╱', group: 'mirror', tip: '理想双面平面镜；入射角与反射角相等。'},
  IdealLens: {label: '理想薄透镜', symbol: '↕', group: 'glass', tip: '端点确定透镜口径。正焦距会聚、负焦距发散；使用理想近轴模型。'},
  PlaneGlass: {label: '半平面玻璃', symbol: '◩', group: 'glass', tip: '端点确定无限长的玻璃边界；半透明区域表示玻璃一侧。改变折射率后重新追迹。'},
  Glass: {label: '多边形玻璃', symbol: '◇', group: 'glass', tip: '顶点按边界顺序排列并自动闭合；只支持简单直边多边形，不允许自相交。'},
  Detector: {label: '探测器', symbol: '┊', group: 'detector', tip: '探测器记录穿过线段的光线，不吸收光。默认记录两侧入射；分箱用于沿线分布。'}
};
const COLORS = {ray:'#f4cf7a', glass:'#7ac5c0', mirror:'#b7cad5', detector:'#e4a8c1'};
const canvas = $('scene-canvas');
const ctx = canvas.getContext('2d');
let scene = null, examples = [], selectedId = null, result = null;
let revision = 0, busy = false, drag = null, unsaved = false, hasSavedScene = false;
let view = {x:-35,y:-20,w:1070,h:700};
let projection = {scale:1,x:0,y:0};
let currentPreset = null;

function make(tag, attrs = {}, text = '') {
  const element = document.createElement(tag);
  for (const [key,value] of Object.entries(attrs)) {
    if (key === 'class') element.className = value;
    else element.setAttribute(key, value);
  }
  if (text !== '') element.textContent = String(text);
  return element;
}
function notify(text, kind = 'neutral') {
  $('message').textContent = text;
  $('message').className = 'message ' + kind;
}
function confirmAction(title, message) {
  return new Promise(resolve=>{
    const dialog=$('confirm-dialog');$('confirm-title').textContent=title;$('confirm-message').textContent=message;
    const finish=value=>{dialog.close();$('confirm-accept').removeEventListener('click',accept);$('confirm-cancel').removeEventListener('click',cancel);dialog.removeEventListener('cancel',cancel);resolve(value);};
    const accept=()=>finish(true),cancel=event=>{if(event)event.preventDefault();finish(false);};
    $('confirm-accept').addEventListener('click',accept);$('confirm-cancel').addEventListener('click',cancel);dialog.addEventListener('cancel',cancel);dialog.showModal();$('confirm-cancel').focus();
  });
}
async function canReplaceEditor(){return !unsaved||await confirmAction('替换尚未保存的场景？','当前编辑尚未保存。继续会替换编辑器中的场景；已保存在工作目录中的记录不会被更改。');}
function describeError(value) {
  if (typeof value === 'string') return value;
  return value?.message || value?.detail || '本机工具未能完成操作，请检查输入后重试。';
}
async function request(path, data) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(new URL('api/' + path, document.baseURI), {
      method: data === undefined ? 'GET' : 'POST',
      headers: data === undefined ? {} : {'Content-Type':'application/json'},
      body: data === undefined ? undefined : JSON.stringify(data),
      credentials:'same-origin', cache:'no-store', redirect:'error', signal:controller.signal
    });
    let payload;
    try { payload = await response.json(); }
    catch (_) { throw new Error('本机服务返回了无法读取的响应。请检查会话是否仍在运行。'); }
    if (!response.ok || !payload.ok) throw new Error(describeError(payload.error || payload.message));
    return payload;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('本机请求超时；旧结果已清除。请减少场景复杂度，或查询服务状态。');
    if (error instanceof TypeError) throw new Error('无法连接本机服务。请在 WorkSwarm 查询本插件状态，再打开实际返回的地址。');
    throw error;
  } finally { clearTimeout(timer); }
}
function selected() { return scene?.objects.find(object => object.id === selectedId); }
function number(value, digits = 6) {
  return Number.isFinite(value) ? Number(value.toPrecision(digits)).toString() : '—';
}
function clearResults() {
  result = null;
  $('ray-count').textContent = '—';
  $('segment-count').textContent = '—';
  $('detector-count').textContent = '—';
  $('calculation-state').textContent = '尚未计算';
  $('canvas-state').textContent = '场景已修改 · 待追迹';
  $('run-detail').textContent = '修改参数后重新计算';
  $('truncation-note').textContent = '旧路径与测量已清除。点击“追迹光路”取得当前场景的真实结果。';
  $('export-csv').disabled = true;
  renderDetectors();
}
function changed(message = '场景已修改，请重新追迹；旧结果已清除。') {
  revision += 1;
  unsaved = true;
  currentPreset = null;
  clearResults();
  renderPresets();
  notify(message);
  draw();
}
function chooseScene(value, message, presetId = null, dirty = false) {
  scene = structuredClone(value);
  selectedId = scene.objects[0]?.id || null;
  revision += 1;
  currentPreset = presetId;
  unsaved = dirty;
  clearResults();
  $('scene-name').value = scene.title || '';
  renderPresets();
  renderEditor();
  fitView();
  notify(message);
}
function renderPresets() {
  $('presets').replaceChildren();
  for (const example of examples) {
    const button = make('button', {type:'button', class:example.id === currentPreset ? 'active' : '', 'aria-pressed':String(example.id === currentPreset)}, example.name);
    button.addEventListener('click', async () => {
      if (busy || !await canReplaceEditor()) return;
      chooseScene(example.scene, '已载入“' + example.name + '”。点击追迹，观察实际路径与结果。', example.id, true);
    });
    $('presets').append(button);
  }
}
function renderEditor() {
  const list = $('object-list');
  list.replaceChildren();
  $('object-count').textContent = (scene?.objects.length || 0) + ' 个';
  for (const object of scene?.objects || []) {
    const info = TYPES[object.type] || {label:object.type,symbol:'?',group:'ray'};
    const button = make('button',{type:'button',class:'object-row' + (object.id === selectedId ? ' active' : ''),'aria-pressed':String(object.id === selectedId)});
    button.append(make('span',{class:'object-symbol ' + info.group, 'aria-hidden':'true'},info.symbol),make('span',{class:'object-name'},object.id),make('span',{class:'object-label'},info.label));
    button.addEventListener('click',()=>{selectedId=object.id;renderEditor();draw();});
    list.append(button);
  }
  renderInspector();
}
function field(container, label, value, setter, options = {}) {
  const wrapper = make('label',{class:'field' + (options.full ? ' full' : '')},label);
  const input = make('input',{type:options.text ? 'text' : 'number','aria-label':label, ...(options.text ? {maxlength:'32',autocomplete:'off'} : {step:'any'})});
  input.value = options.text ? value : (Number.isFinite(value) ? value : '');
  if (options.min !== undefined) input.min = options.min;
  if (options.max !== undefined) input.max = options.max;
  if (options.step !== undefined) input.step = options.step;
  input.addEventListener('input',()=>{
    const problem=options.check?.(input.value)||'';
    input.setCustomValidity(problem);
    if(problem){changed(problem);return;}
    setter(options.text ? input.value : input.valueAsNumber);
    changed();
    if (options.refreshList) {
      const row = Array.from($('object-list').children).find(x=>x.getAttribute('aria-pressed')==='true');
      if (row) row.querySelector('.object-name').textContent = input.value;
    }
  });
  wrapper.append(input);
  container.append(wrapper);
}
function pointFields(container, point, heading) {
  container.append(make('span',{class:'subheading'},heading));
  field(container,heading + ' X',point.x,value=>point.x=value,{min:-2000,max:2000});
  field(container,heading + ' Y',point.y,value=>point.y=value,{min:-2000,max:2000});
}
function renderInspector() {
  const target = $('inspector'), object = selected();
  target.replaceChildren();
  $('delete-object').disabled = !object;
  $('selected-type').textContent = TYPES[object?.type]?.label || '尚未选择';
  $('object-tip').textContent = TYPES[object?.type]?.tip || '';
  if (!object) {target.append(make('p',{class:'muted full'},'选择一个元件以编辑。'));return;}
  field(target,'标识（字母开头，唯一）',object.id,value=>{object.id=value;selectedId=value;},{text:true,full:true,refreshList:true,check:value=>{
    if(!/^\p{L}[\p{L}\p{N}_-]{0,31}$/u.test(value))return '标识须以字母开头，最多 32 个字母、数字、下划线或连字符。';
    return scene.objects.some(item=>item!==object&&item.id===value)?'标识已存在，请使用唯一标识。':'';
  }});
  if (object.type === 'Glass') {
    object.path.forEach((point,index)=>pointFields(target,point,'顶点 ' + (index+1)));
    const controls=make('div',{class:'full vertex-actions'});
    const add=make('button',{type:'button'},'＋ 顶点');
    add.addEventListener('click',()=>{
      if(object.path.length>=16){notify('多边形最多 16 个顶点。','error');return;}
      const last=object.path.at(-1),first=object.path[0],dx=first.x-last.x,dy=first.y-last.y,length=Math.hypot(dx,dy)||1;
      const area=object.path.reduce((sum,p,i)=>{const q=object.path[(i+1)%object.path.length];return sum+p.x*q.y-q.x*p.y;},0),side=area>=0?1:-1;
      object.path.push({x:(last.x+first.x)/2+20*dy/length*side,y:(last.y+first.y)/2-20*dx/length*side});
      changed();renderInspector();
    });
    const remove=make('button',{type:'button'},'移除末尾顶点');
    remove.disabled=object.path.length<=3;
    remove.addEventListener('click',()=>{if(object.path.length>3){object.path.pop();changed();renderInspector();}});
    controls.append(add,remove);target.append(controls);
  } else {
    pointFields(target,object.p1,'端点 1');pointFields(target,object.p2,'端点 2');
    const swap=make('button',{type:'button',class:'full quiet'},'⇄ 对调两个端点');
    swap.addEventListener('click',()=>{[object.p1,object.p2]=[object.p2,object.p1];changed();renderInspector();});target.append(swap);
  }
  if (object.type==='SingleRay'||object.type==='Beam') field(target,object.type==='Beam'?'光束总相对亮度':'相对亮度',object.brightness??1,value=>object.brightness=value,{min:0.001,max:10,full:true});
  if (object.type==='Beam') field(target,'发射光线数',object.rayCount??9,value=>object.rayCount=value,{min:1,max:64,step:1,full:true});
  if (object.type==='IdealLens') field(target,'焦距（与坐标同单位）',object.focalLength??100,value=>object.focalLength=value,{full:true});
  if (object.type==='PlaneGlass'||object.type==='Glass') field(target,'折射率',object.refIndex??1.5,value=>object.refIndex=value,{min:1,max:3,full:true});
  if (object.type==='Detector') {
    field(target,'分箱数量',object.bins??20,value=>object.bins=value,{min:1,max:100,step:1,full:true});
    const label=make('label',{class:'checkbox-field full'});
    const input=make('input',{type:'checkbox','aria-label':'双向探测'});
    input.checked=object.twoSided!==false;input.addEventListener('change',()=>{object.twoSided=input.checked;changed();});
    label.append(input,document.createTextNode('双向探测'));target.append(label);
  }
}
function allPoints() { return (scene?.objects || []).flatMap(object=>object.type==='Glass'?object.path:[object.p1,object.p2]).filter(point=>Number.isFinite(point?.x)&&Number.isFinite(point?.y)); }
function fitView() {
  const points=allPoints();
  const minX=Math.min(0,...points.map(p=>p.x)),maxX=Math.max(1000,...points.map(p=>p.x));
  const minY=Math.min(0,...points.map(p=>p.y)),maxY=Math.max(650,...points.map(p=>p.y));
  view={x:minX-35,y:minY-25,w:maxX-minX+70,h:maxY-minY+50};draw();
}
function project(point) {return {x:(point.x-view.x)*projection.scale+projection.x,y:(point.y-view.y)*projection.scale+projection.y};}
function unproject(x,y) {return {x:(x-projection.x)/projection.scale+view.x,y:(y-projection.y)/projection.scale+view.y};}
function line(a,b,color,width=1,dash=[]) {
  if (![a.x,a.y,b.x,b.y].every(Number.isFinite)) return;
  const p=project(a),q=project(b);ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash(dash);ctx.stroke();ctx.setLineDash([]);
}
function dot(point,color,radius=3) {const p=project(point);ctx.beginPath();ctx.arc(p.x,p.y,radius,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();}
function arrow(a,b,color,size=6) {
  const p=project(a),q=project(b),dx=q.x-p.x,dy=q.y-p.y,length=Math.hypot(dx,dy);if(length<26)return;
  const mx=(p.x+q.x)/2,my=(p.y+q.y)/2,ux=dx/length,uy=dy/length;
  ctx.beginPath();ctx.moveTo(mx-ux*size-uy*size/2,my-uy*size+ux*size/2);ctx.lineTo(mx,my);ctx.lineTo(mx-ux*size+uy*size/2,my-uy*size-ux*size/2);ctx.strokeStyle=color;ctx.lineWidth=1.3;ctx.stroke();
}
function draw() {
  const bounds=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
  if(!bounds.width||!bounds.height)return;
  canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
  const width=bounds.width,height=bounds.height;projection.scale=Math.min((width-30)/view.w,(height-58)/view.h);projection.x=(width-view.w*projection.scale)/2;projection.y=(height-view.h*projection.scale)/2+3;
  ctx.clearRect(0,0,width,height);ctx.fillStyle='#102a30';ctx.fillRect(0,0,width,height);
  const step=100;ctx.lineWidth=.5;ctx.strokeStyle='#254047';
  for(let x=Math.ceil(view.x/step)*step;x<view.x+view.w;x+=step)line({x,y:view.y},{x,y:view.y+view.h},'#254047',.5);
  for(let y=Math.ceil(view.y/step)*step;y<view.y+view.h;y+=step)line({x:view.x,y},{x:view.x+view.w,y},'#254047',.5);
  // Reference viewport only. Escaping engine segments extend beyond it and are
  // clipped by the canvas; this does not alter numerical detector measurements.
  const origin=project({x:0,y:0}),end=project({x:1000,y:650});ctx.strokeStyle='#375059';ctx.setLineDash([4,5]);ctx.strokeRect(origin.x,origin.y,end.x-origin.x,end.y-origin.y);ctx.setLineDash([]);
  for(const object of scene?.objects||[])drawObject(object,false);
  for(const segment of result?.segments||[]) {
    if(!segment.from||!segment.to)continue;
    ctx.globalAlpha=Math.max(.18,Math.min(1,Math.sqrt(Math.max(0,segment.brightness??1))));
    line(segment.from,segment.to,COLORS.ray,1.3);arrow(segment.from,segment.to,COLORS.ray,5);
  }
  ctx.globalAlpha=1;
  for(const object of scene?.objects||[])drawObject(object,true);
}
function drawObject(object,foreground) {
  const info=TYPES[object.type];if(!info)return;
  const color=COLORS[info.group],isSelected=object.id===selectedId;
  if(object.type==='Glass') {
    if(!object.path?.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)))return;
    const points=object.path.map(project);
    if(!foreground){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle='#31676855';ctx.fill();ctx.strokeStyle=color;ctx.lineWidth=isSelected?2:1;ctx.stroke();}
  } else {
    if(![object.p1?.x,object.p1?.y,object.p2?.x,object.p2?.y].every(Number.isFinite))return;
    const p1=object.p1,p2=object.p2,dx=p2.x-p1.x,dy=p2.y-p1.y,length=Math.hypot(dx,dy)||1;
    if(!foreground){
      if(object.type==='PlaneGlass'){
        const reach=10000;const vertices=[{x:p1.x-dx/length*reach,y:p1.y-dy/length*reach},{x:p2.x+dx/length*reach,y:p2.y+dy/length*reach},{x:p2.x+dx/length*reach-dy/length*reach,y:p2.y+dy/length*reach+dx/length*reach},{x:p1.x-dx/length*reach-dy/length*reach,y:p1.y-dy/length*reach+dx/length*reach}].map(project);
        ctx.save();const a=project({x:view.x,y:view.y}),b=project({x:view.x+view.w,y:view.y+view.h});ctx.beginPath();ctx.rect(a.x,a.y,b.x-a.x,b.y-a.y);ctx.clip();ctx.beginPath();vertices.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fillStyle='#31676840';ctx.fill();ctx.restore();
        line({x:p1.x-dx/length*5000,y:p1.y-dy/length*5000},{x:p2.x+dx/length*5000,y:p2.y+dy/length*5000},'#6ba5a5',1,[4,5]);
      }
      if(object.type==='SingleRay'){line(p1,p2,'#f4cf7a88',1,[4,4]);arrow(p1,p2,COLORS.ray);dot(p1,COLORS.ray,4);}
      else if(object.type==='Detector')line(p1,p2,color,isSelected?3:2,[4,4]);
      else line(p1,p2,color,isSelected?3:2);
      if(object.type==='IdealLens'){
        const normal={x:-dy/length,y:dx/length};
        for(const [point,sign] of [[p1,1],[p2,-1]]){
          const inward={x:point.x+dx/length*sign*12,y:point.y+dy/length*sign*12};
          line(point,{x:inward.x+normal.x*8,y:inward.y+normal.y*8},color,1.5);line(point,{x:inward.x-normal.x*8,y:inward.y-normal.y*8},color,1.5);
        }
      }
      if(object.type==='Beam'){
        const middle={x:(p1.x+p2.x)/2,y:(p1.y+p2.y)/2};
        arrow(middle,{x:middle.x+dy/length*60,y:middle.y-dx/length*60},COLORS.ray);
      }
    }
  }
  if(foreground){
    const points=object.type==='Glass'?object.path:[object.p1,object.p2];
    if(isSelected)points.forEach(point=>{dot(point,'#f5f9e8',5);dot(point,color,2);});
    const center=object.type==='Glass'?{x:object.path.reduce((s,p)=>s+p.x,0)/object.path.length,y:object.path.reduce((s,p)=>s+p.y,0)/object.path.length}:{x:(object.p1.x+object.p2.x)/2,y:(object.p1.y+object.p2.y)/2};
    const p=project(center);ctx.font='11px -apple-system, sans-serif';ctx.fillStyle=isSelected?'#f5f4d9':'#a9c1c1';ctx.fillText(object.id,p.x+8,p.y-9);
  }
}
function distanceToLine(point,a,b) {
  const dx=b.x-a.x,dy=b.y-a.y,length=dx*dx+dy*dy;
  const t=length?Math.max(0,Math.min(1,((point.x-a.x)*dx+(point.y-a.y)*dy)/length)):0;
  return Math.hypot(point.x-a.x-t*dx,point.y-a.y-t*dy);
}
function hitTest(point) {
  let best=null,limit=13/projection.scale;
  for(const object of [...(scene?.objects||[])].reverse()){
    const points=object.type==='Glass'?object.path:[object.p1,object.p2];
    for(let index=0;index<points.length;index++){
      const distance=Math.hypot(point.x-points[index].x,point.y-points[index].y);
      if(distance<limit){limit=distance;best={object,index,endpoint:true};}
    }
  }
  if(best)return best;
  for(const object of [...(scene?.objects||[])].reverse()){
    const points=object.type==='Glass'?[...object.path,object.path[0]]:[object.p1,object.p2];
    for(let i=1;i<points.length;i++)if(distanceToLine(point,points[i-1],points[i])<limit)return {object,endpoint:false};
  }
  return null;
}
canvas.addEventListener('pointerdown',event=>{
  if(event.button!==0||!scene)return;
  const bounds=canvas.getBoundingClientRect(),point=unproject(event.clientX-bounds.left,event.clientY-bounds.top),hit=hitTest(point);
  if(!hit)return;
  selectedId=hit.object.id;renderEditor();draw();canvas.focus();
  if(hit.endpoint){drag={...hit,moved:false};canvas.setPointerCapture(event.pointerId);}
});
canvas.addEventListener('pointermove',event=>{
  const bounds=canvas.getBoundingClientRect(),point=unproject(event.clientX-bounds.left,event.clientY-bounds.top);
  $('coordinate').textContent='X '+number(point.x,4)+' · Y '+number(point.y,4);
  if(!drag)return;
  const target=drag.object.type==='Glass'?drag.object.path[drag.index]:drag.object[drag.index?'p2':'p1'];
  target.x=Math.round(Math.max(-2000,Math.min(2000,point.x)));target.y=Math.round(Math.max(-2000,Math.min(2000,point.y)));
  drag.moved=true;changed('端点已移动；旧结果已清除，请重新追迹。');renderInspector();
});
function endDrag(){drag=null;}
canvas.addEventListener('pointerup',endDrag);canvas.addEventListener('pointercancel',endDrag);canvas.addEventListener('lostpointercapture',endDrag);
canvas.addEventListener('keydown',event=>{
  const directions={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
  if(!directions[event.key]||!selected())return;
  event.preventDefault();const [x,y]=directions[event.key],object=selected(),step=event.shiftKey?1:5;
  for(const point of object.type==='Glass'?object.path:[object.p1,object.p2]){point.x=Math.max(-2000,Math.min(2000,point.x+x*step));point.y=Math.max(-2000,Math.min(2000,point.y+y*step));}
  changed('元件已移动；请重新追迹。');renderInspector();
});
function formIsValid(){
  if(!scene)return false;
  for(const input of $('inspector').querySelectorAll('input'))if(!input.checkValidity()){input.reportValidity();return false;}
  return true;
}
function setBusy(value){busy=value;$('simulate').disabled=value;for(const id of ['save-scene','load-scene','import-json','add-object'])$(id).disabled=value;}
async function simulate(){
  if(busy||!formIsValid())return;
  const runRevision=revision,snapshot=structuredClone(scene);clearResults();setBusy(true);notify('正在本机计算真实光路…','busy');$('canvas-state').textContent='引擎运行中';
  try{
    const payload=await request('simulate',{scene:snapshot});
    if(runRevision!==revision){notify('计算期间场景已改变；已丢弃过期结果，请再次追迹。');return;}
    result=payload;
    $('ray-count').textContent=number(payload.stats?.emitted_rays??payload.stats?.processed_segments??0);
    $('segment-count').textContent=String(payload.segments?.length??0);
    $('detector-count').textContent=String(payload.detectors?.length??0);
    const partial=Boolean(payload.stats?.truncated);
    $('calculation-state').textContent=partial?'达到边界':'计算完成';$('canvas-state').textContent=partial?'实际结果 · 有截断':'实际结果 · 已完成';
    $('run-detail').textContent='引擎版本 '+(payload.version||'未返回');
    const notes=Array.isArray(payload.warnings)?payload.warnings:[];
    $('truncation-note').textContent=notes.length?notes.join(' '):'本次结果由本机引擎返回；未报告达到计算边界。逃逸光线以有限长度绘制；画布可见范围不改变数值计算。';
    notify(partial?'本次计算达到限制。结果为部分追迹，请查看边界说明。':'追迹完成。编辑元件后可再次运行，对比光路与探测器结果。',partial?'busy':'success');
    $('export-csv').disabled=!(payload.detectors?.length);renderDetectors();draw();
  }catch(error){clearResults();notify(error.message,'error');$('canvas-state').textContent='追迹失败 · 无结果';draw();}
  finally{setBusy(false);}
}
function renderDetectors(){
  const target=$('detector-results');target.replaceChildren();
  if(!result?.detectors?.length){
    const empty=make('div',{class:'empty-state'});empty.append(make('span',{'aria-hidden':'true'},'⌁'));
    const text=make('div');text.append(make('h3',{},result?'场景中没有探测器':'等待真实追迹结果'),make('p',{},result?'可添加探测器，再次运行以取得数值测量。':'放置探测器并运行仿真，查看光功率和沿探测线的分布。'));empty.append(text);target.append(empty);return;
  }
  const grid=make('div',{class:'detector-grid'});
  for(const detector of result.detectors){
    const card=make('section',{class:'detector-card'}),heading=make('div',{class:'detector-title'});heading.append(make('h3',{},detector.id),make('span',{},'本次真实测量'));card.append(heading);
    const values=make('div',{class:'detector-values'});
    for(const [label,key] of [['带方向相对功率','power'],['法向分量','normal'],['切向分量','shear']]){const item=make('div');item.append(make('label',{},label),make('strong',{},number(detector[key])));values.append(item);}card.append(values);
    const bins=detector.binData||[];
    if(bins.length){
      const chart=make('canvas',{class:'detector-chart',width:'500',height:'140','aria-label':detector.id+' 探测线分箱分布'});card.append(chart);
      const details=make('details',{class:'bin-details'});details.append(make('summary',{},'查看 '+bins.length+' 个分箱数值'));
      const table=make('table'),head=make('tr');for(const text of ['序号','沿线位置','分箱值'])head.append(make('th',{},text));table.append(head);
      bins.forEach((value,index)=>{const row=make('tr');for(const val of [index+1,number(detector.binPositions?.[index]??index*detector.binSize),number(value)])row.append(make('td',{},val));table.append(row);});details.append(table);card.append(details);
      const c=chart.getContext('2d'),max=Math.max(1e-12,...bins.map(Math.abs));c.fillStyle='#eef1e4';c.fillRect(0,0,500,140);c.strokeStyle='#b4c4a4';c.beginPath();c.moveTo(0,70);c.lineTo(500,70);c.stroke();const width=500/bins.length;
      bins.forEach((value,index)=>{const h=value/max*58;c.fillStyle=value>=0?'#35775c':'#92734c';c.fillRect(index*width+1,h>=0?70-h:70,Math.max(.5,width-2),Math.abs(h));});
    }
    grid.append(card);
  }
  target.append(grid);
}
function download(name,text,type){const url=URL.createObjectURL(new Blob([text],{type}));const link=make('a',{href:url,download:name});document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function defaultObject(type){
  let index=1;while(scene.objects.some(o=>o.id===type+index))index++;
  const object={id:type+index,type};
  if(type==='Glass')return {...object,path:[{x:420,y:180},{x:620,y:180},{x:620,y:470},{x:420,y:470}],refIndex:1.5};
  object.p1={x:500,y:200};object.p2={x:500,y:450};
  if(type==='SingleRay'){object.p1={x:100,y:325};object.p2={x:200,y:325};object.brightness=1;}
  if(type==='Beam'){object.p1={x:150,y:200};object.p2={x:150,y:450};object.brightness=1;object.rayCount=9;}
  if(type==='IdealLens')object.focalLength=150;
  if(type==='PlaneGlass')object.refIndex=1.5;
  if(type==='Detector'){object.p1={x:850,y:120};object.p2={x:850,y:530};object.bins=20;object.twoSided=true;}
  return object;
}
for(const [type,info] of Object.entries(TYPES))$('add-type').append(make('option',{value:type},info.label));
$('add-object').addEventListener('click',()=>{
  if(!scene)return;
  if(scene.objects.length>=32){notify('场景最多 32 个元件，请先移除不需要的元件。','error');return;}
  const object=defaultObject($('add-type').value);scene.objects.push(object);selectedId=object.id;changed('已添加元件。请调整参数并重新追迹。');renderEditor();
});
$('delete-object').addEventListener('click',()=>{if(!selected())return;scene.objects=scene.objects.filter(object=>object.id!==selectedId);selectedId=scene.objects[0]?.id||null;changed('已移除元件；请重新追迹。');renderEditor();});
$('scene-name').addEventListener('input',()=>{if(scene){scene.title=$('scene-name').value;changed();}});
$('fit-view').addEventListener('click',fitView);$('simulate').addEventListener('click',simulate);
$('help-toggle').addEventListener('click',()=>{const box=$('quick-help');box.hidden=!box.hidden;$('help-toggle').setAttribute('aria-expanded',String(!box.hidden));});
$('save-scene').addEventListener('click',async()=>{
  if(busy||!formIsValid())return;
  if(hasSavedScene&&!await confirmAction('替换已保存的场景？','当前工作目录只保留一个场景记录。继续会用当前场景替换该记录；如需保留旧版本，请先导出 JSON。'))return;
  setBusy(true);const snapshot=structuredClone(scene),savedRevision=revision;
  try{await request('state',{scene:snapshot});hasSavedScene=true;if(savedRevision===revision)unsaved=false;notify(savedRevision===revision?'当前场景已保存到本机工作目录。':'已保存点击时的场景；之后的修改尚未保存。','success');}catch(error){notify(error.message,'error');}finally{setBusy(false);}
});
$('load-scene').addEventListener('click',async()=>{
  if(busy||!await canReplaceEditor())return;setBusy(true);const loadedRevision=revision;
  try{const saved=await request('state');hasSavedScene=Boolean(saved.scene);if(!saved.scene)notify('当前工作目录尚无已保存场景。');else if(loadedRevision===revision||await canReplaceEditor())chooseScene(saved.scene,'已读取保存的场景；请重新追迹。');}catch(error){notify(error.message,'error');}finally{setBusy(false);}
});
$('export-json').addEventListener('click',()=>{if(!scene||!formIsValid())return;download('离线光学实验室-场景.json',JSON.stringify(scene,null,2)+'\n','application/json;charset=utf-8');notify('场景 JSON 已交给浏览器下载。');});
$('import-json').addEventListener('click',()=>{$('import-file').value='';$('import-file').click();});
$('import-file').addEventListener('change',async()=>{
  const file=$('import-file').files?.[0];if(!file||busy)return;
  if(file.size>131072){notify('JSON 文件超过 128 KiB 上限，未导入。','error');return;}
  setBusy(true);
  try{
    const input=JSON.parse(await file.text());const response=await request('validate',{scene:input});
    if(await canReplaceEditor())chooseScene(response.scene||input,'JSON 已通过本机工具校验并导入；请重新追迹。',null,true);
  }catch(error){notify(error instanceof SyntaxError?'JSON 格式无效，当前场景保持不变。':error.message,'error');}
  finally{setBusy(false);}
});
$('export-csv').addEventListener('click',()=>{
  if(!result?.detectors?.length)return;
  const rows=[['探测器','相对功率','法向分量','切向分量','分箱序号','沿线位置','分箱值']];
  for(const d of result.detectors){if(d.binData?.length)d.binData.forEach((value,index)=>rows.push([d.id,d.power,d.normal,d.shear,index+1,d.binPositions?.[index]??index*d.binSize,value]));else rows.push([d.id,d.power,d.normal,d.shear,'','','']);}
  const csv=rows.map(row=>row.map(value=>'"'+String(value??'').replaceAll('"','""')+'"').join(',')).join('\r\n');
  download('离线光学实验室-探测器.csv','\ufeff'+csv+'\r\n','text/csv;charset=utf-8');notify('本次实际探测器结果已交给浏览器下载。');
});
new ResizeObserver(draw).observe(canvas);
async function initialize(){
  setBusy(true);
  try{
    const data=await request('examples');examples=data.examples||[];
    if(!examples.length)throw new Error('本机服务未提供示例场景。');
    const saved=await request('state');
    hasSavedScene=Boolean(saved.scene);
    if(saved.scene)chooseScene(saved.scene,'已恢复本机保存的场景。请重新追迹以取得本次结果。');
    else chooseScene(examples[0].scene,'实验台已就绪。选择示例，点击“追迹光路”开始。',examples[0].id);
  }catch(error){notify(error.message,'error');}
  finally{setBusy(false);}
}
initialize();
