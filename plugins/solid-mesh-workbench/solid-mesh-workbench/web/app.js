// Original plugin UI: all geometry is computed by the bundled Manifold engine.
import {formatMetric as fmt, serializeProject, meshFrame} from './ui_helpers.mjs';
const $ = (id) => document.getElementById(id);
const SCHEMA = 'solid-mesh-workbench/v1';
const STORAGE = 'solid-mesh-workbench/v1/project';
const MAX_FILE = 2 * 1024 * 1024;
const MAX_OBJ = 1024 * 1024;
const defaults = () => ({schema: SCHEMA, units: 'mm', operation: 'union', a: {kind: 'box', size: [20,20,20], translate: [0,0,0], rotate: [0,0,0]}, b: {kind: 'box', size: [20,20,20], translate: [10,0,0], rotate: [0,0,0]}});
let draft = defaults();
let output = null;
let active = null;
let generation = 0;
let stopped = false;
let lifecyclePending = false;
let readEpoch = 0;
const reads = {a: 0, b: 0, project: 0};
const readUtf8 = async (file) => new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer());
const errorMessage = (e) => typeof e === 'string' ? e : e?.message || '操作未完成，请检查输入或本机服务。';
function status(text, type='') { $('status').textContent = text; $('status').className = 'status ' + type; }
function exportState() {
  for (const id of ['export-obj','save-project','save-report']) $(id).disabled = !output || !!active || lifecyclePending || stopped || (id === 'export-obj' && output.metrics.empty);
}
function invalidate(message='参数已修改。请重新计算后导出。') {
  ++readEpoch;
  output = null; renderer.set(null); exportState();
  for (const id of ['volume','area','triangles','bounds']) $(id).textContent = '—';
  $('empty-view').textContent = '输入已改变，等待重新计算'; $('empty-view').hidden = false;
  status(message);
}
function setBusy(busy) {
  document.querySelectorAll('.inputs input,.inputs select,.inputs button,#load-project,#reset').forEach(el => { el.disabled = busy || lifecyclePending || stopped; });
  $('cancel').disabled = !active || lifecyclePending || stopped;
  $('stop').disabled = lifecyclePending || stopped;
  exportState();
}
function syncOperation() { document.querySelectorAll('[data-operation]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.operation === draft.operation))); }
function numberFields(parent, title, key, values, id, labels=['X','Y','Z']) {
  const heading = document.createElement('p'); heading.className = 'field-heading'; heading.textContent = title; parent.append(heading);
  const grid = document.createElement('div'); grid.className = 'field-grid'; parent.append(grid);
  values.forEach((value, i) => {
    const label = document.createElement('label'); label.textContent = labels[i];
    const input = document.createElement('input'); input.type = 'number'; input.step = 'any'; input.value = value;
    input.id = `${id}-${key}-${i}`; input.setAttribute('aria-label', `${id.toUpperCase()} ${title} ${labels[i]}`);
    input.addEventListener('input', () => { const n = input.value === '' ? null : Number(input.value); if (Array.isArray(draft[id][key])) draft[id][key][i] = n; else draft[id][key] = n; invalidate(); });
    label.append(input); grid.append(label);
  });
}
function renderOperands() {
  $('operands').replaceChildren();
  for (const id of ['a','b']) {
    const operand = draft[id];
    const section = document.createElement('section'); section.className = 'operand'; section.dataset.operand = id;
    const heading = document.createElement('h3'); const badge = document.createElement('span'); badge.className = 'label-dot'; badge.textContent = id.toUpperCase(); heading.append(badge, document.createTextNode(id === 'a' ? '主体网格' : '组合 / 刀具网格')); section.append(heading);
    const kind = document.createElement('select'); kind.id = `${id}-kind`; kind.setAttribute('aria-label', `${id.toUpperCase()} 网格类型`);
    for (const [value, name] of [['box','长方体'],['cylinder','圆柱体'],['obj','导入三角 OBJ'],['mesh','项目中的网格']]) { const option = document.createElement('option'); option.value = value; option.textContent = name; option.disabled = value === 'mesh' && operand.kind !== 'mesh'; kind.append(option); }
    kind.value = operand.kind; section.append(kind);
    kind.addEventListener('change', () => {
      const transform = {translate: [...(operand.translate || [0,0,0])], rotate: [...(operand.rotate || [0,0,0])]};
      draft[id] = kind.value === 'box' ? {kind:'box',size:[20,20,20],...transform} : kind.value === 'cylinder' ? {kind:'cylinder',radius:6,height:30,segments:48,...transform} : {kind:'obj',text:'',...transform};
      invalidate(); renderOperands();
    });
    if (operand.kind === 'box') numberFields(section,'尺寸 / mm','size',operand.size,id);
    if (operand.kind === 'cylinder') { numberFields(section,'半径 / mm','radius',[operand.radius],id,['R']); numberFields(section,'高度 / mm','height',[operand.height],id,['H']); numberFields(section,'圆周分段','segments',[operand.segments],id,['段数']); }
    if (operand.kind === 'obj') {
      const file = document.createElement('input'); file.type = 'file'; file.accept = '.obj,text/plain'; file.id = `${id}-obj`; file.className = 'obj-upload'; file.setAttribute('aria-label',`${id.toUpperCase()} 导入 OBJ 文件`);
      const info = document.createElement('p'); info.className = 'mesh-info'; info.textContent = operand.text ? `已载入 OBJ 文本（${operand.text.length.toLocaleString()} 字符）` : '选择已有闭合三角网格。按毫米解释。';
      file.addEventListener('change', async () => {
        const selection = ++reads[id]; const selected = file.files[0]; if (!selected) return;
        if (selected.size > MAX_OBJ) { status('OBJ 文件超过 1 MiB 限制，请使用更小的网格。','error'); file.value=''; return; }
        const epoch = readEpoch; const target = draft[id];
        const current = () => selection === reads[id] && epoch === readEpoch && target === draft[id] && !active && !lifecyclePending && !stopped;
        try { const text = await readUtf8(selected); if (!current()) return; draft[id].text=text; invalidate(); info.textContent=`已载入：${selected.name}（待计算校验）`; }
        catch { if (current()) status('无法读取 OBJ 文件，请确认文件采用 UTF-8 编码。','error'); }
      }); section.append(file,info);
    }
    if (operand.kind === 'mesh') { const info=document.createElement('p'); info.className='mesh-info'; info.textContent=`项目网格：${operand.positions.length/3} 个顶点，${operand.triangles.length/3} 个三角面`; section.append(info); }
    numberFields(section,'平移 / mm','translate',operand.translate || [0,0,0],id);
    numberFields(section,'旋转 / °','rotate',operand.rotate || [0,0,0],id);
    $('operands').append(section);
  }
  syncOperation();
}
async function api(path, data, signal) {
  let result;
  try {
    const response = await fetch(new URL('api/' + path, location.href), {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),signal,credentials:'omit',cache:'no-store'});
    result=await response.json();
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('无法连接本机工作台或响应无效。请通过插件工具查看状态，必要时重新启动并打开新地址。');
  }
  if (!result.ok) throw new Error(errorMessage(result.error));
  return result;
}
async function run(project=draft, imported=false) {
  if (active || lifecyclePending || stopped) return false;
  const current = ++generation;
  const request_id='mesh_' + crypto.randomUUID().replaceAll('-','');
  const controller=new AbortController(); active={request_id,controller};
  invalidate('正在计算真实网格，请稍候…'); setBusy(true);
  try {
    const result=await api('calculate',{request_id,project},controller.signal);
    if (current !== generation || stopped) return;
    output=result;
    if (imported) { draft=result.project; renderOperands(); }
    renderer.set(result); renderer.fit();
    const m=result.metrics;
    $('volume').textContent=fmt(m.volume_mm3); $('area').textContent=fmt(m.area_mm2); $('triangles').textContent=fmt(m.triangles);
    $('bounds').textContent=m.bounds ? m.bounds.max.map((v,i)=>fmt(v-m.bounds.min[i])).join(' × ') : '空';
    $('empty-view').hidden=!m.empty; $('empty-view').textContent='有效空结果：运算结果为空';
    status(m.empty ? '计算完成：有效空结果。可保存项目与测量报告。' : '计算完成。结果可旋转检查、测量和导出。','success');
    try { localStorage.setItem(STORAGE,serializeProject(result.project)); } catch { status('计算完成。浏览器未保存恢复副本，请下载项目 JSON。','success'); }
    return true;
  } catch (error) {
    if (current === generation) status(error.name === 'AbortError' ? '本次计算已取消。' : errorMessage(error),'error');
    return false;
  } finally { if (current === generation) { active=null; setBusy(false); } }
}
async function cancel() {
  if (!active || lifecyclePending || stopped) return;
  lifecyclePending=true;
  const job=active; ++generation; active=null; job.controller.abort();
  invalidate('正在结束本次计算…'); setBusy(true);
  try { await api('cancel',{request_id:job.request_id}); status('本次计算已取消；可调整输入后重试。'); }
  catch (e) { status('取消请求未获确认：'+errorMessage(e),'error'); }
  finally { lifecyclePending=false; setBusy(false); }
}
function download(text,name,type) {
  const url=URL.createObjectURL(new Blob([text],{type})); const a=document.createElement('a'); a.href=url; a.download=name; document.body.append(a); a.click(); a.remove(); setTimeout(()=>URL.revokeObjectURL(url),10000);
}
$('calculate').addEventListener('click',()=>run()); $('cancel').addEventListener('click',cancel);
document.querySelectorAll('[data-operation]').forEach(button=>button.addEventListener('click',()=>{draft.operation=button.dataset.operation;syncOperation();invalidate();}));
$('export-obj').addEventListener('click',()=>{if(output&&!active)download(output.obj,'布尔结果.obj','text/plain;charset=utf-8');});
$('save-project').addEventListener('click',()=>{if(!output||active||lifecyclePending)return;try{download(serializeProject(output.project),'网格项目.json','application/json');}catch(e){status(errorMessage(e),'error');}});
$('save-report').addEventListener('click',()=>{if(!output||active)return;const m=output.metrics;download(JSON.stringify({名称:'立体网格布尔工坊',版本:'1.0.0',引擎:'Manifold 3.5.4',单位:'毫米',运算:{union:'并集',difference:'差集',intersection:'交集'}[output.project.operation],体积_mm3:m.volume_mm3,表面积_mm2:m.area_mm2,三角面数:m.triangles,顶点数:m.vertices,包围盒:m.bounds,空结果:m.empty,说明:'数值计算结果；不构成网格修复或可打印性认证。'},null,2)+'\n','几何测量报告.json','application/json');});
$('load-project').addEventListener('change',async()=>{
  const selection=++reads.project;
  const file=$('load-project').files[0]; $('load-project').value=''; if(!file||active||lifecyclePending||stopped)return;
  if(file.size>MAX_FILE){status('项目文件超过 2 MiB 限制。','error');return;}
  const epoch=readEpoch;
  const current=()=>selection===reads.project&&epoch===readEpoch&&!active&&!lifecyclePending&&!stopped;
  try { const text=await readUtf8(file); if(!current())return; const project=JSON.parse(text); await run(project,true); } catch {if(current())status('项目不是有效 UTF-8 JSON；当前输入保留。','error');}
});
function loadExample() {
  ++generation; draft=defaults();
  if($('example').value==='bore'){draft.operation='difference';draft.b={kind:'cylinder',radius:6,height:30,segments:48,translate:[10,10,-5],rotate:[0,0,0]};}
  if($('example').value==='empty'){draft.operation='intersection';draft.b.translate=[40,0,0];}
  renderOperands(); invalidate('示例已载入。点击“计算结果”。');
}
$('example').addEventListener('change',loadExample);
$('reset').addEventListener('click',()=>{try{localStorage.removeItem(STORAGE);}catch{}$('example').value='boxes';loadExample();});
$('stop').addEventListener('click',async()=>{
  if(stopped||lifecyclePending)return;
  lifecyclePending=true; ++generation;
  const job=active; active=null; job?.controller.abort();
  invalidate('正在关闭本机工作台…');setBusy(true);
  try {if(job)await api('cancel',{request_id:job.request_id});await api('stop',{});stopped=true;status('工作台已关闭。重新使用时，请通过原生插件工具启动新会话。');}
  catch(e){status(errorMessage(e),'error');}
  finally {lifecyclePending=false;setBusy(false);}
});

// Small original WebGL viewer. It displays computed triangles, not a mock scene.
class MeshView {
  constructor(canvas) {
    this.canvas=canvas; this.gl=canvas.getContext('webgl',{antialias:true,alpha:false}); this.items=[]; this.center=[0,0,0]; this.radius=20; this.rx=-.52;this.ry=.65;this.zoom=1;
    if(!this.gl){status('浏览器无法创建 WebGL 预览；几何计算与导出仍可使用。','error');return;}
    const gl=this.gl;
    const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error('预览着色器不可用');return s;};
    this.program=gl.createProgram();
    gl.attachShader(this.program,shader(gl.VERTEX_SHADER,'attribute vec3 position;attribute vec3 normal;uniform mat3 rotation;uniform vec3 center;uniform float scale;uniform float aspect;varying float light;void main(){vec3 p=rotation*(position-center);gl_Position=vec4(p.x*scale/aspect,p.y*scale,-p.z*scale*.15,1.0);vec3 n=rotation*normal;light=.38+.62*abs(dot(n,normalize(vec3(.4,.7,1.))));}'));
    gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,'precision mediump float;uniform vec3 color;uniform bool line;varying float light;void main(){gl_FragColor=vec4(color*(line?1.0:light),1.0);}'));
    gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw new Error('预览初始化失败');
    this.locations={};for(const n of ['rotation','center','scale','aspect','color','line'])this.locations[n]=gl.getUniformLocation(this.program,n);
    this.position=gl.getAttribLocation(this.program,'position');this.normal=gl.getAttribLocation(this.program,'normal');
    let drag=null;canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
    canvas.addEventListener('pointermove',e=>{if(!drag)return;this.ry+=(e.clientX-drag[0])*.009;this.rx+=(e.clientY-drag[1])*.009;drag=[e.clientX,e.clientY];this.draw();});
    for(const name of ['pointerup','pointercancel'])canvas.addEventListener(name,()=>{drag=null;});
    canvas.addEventListener('wheel',e=>{e.preventDefault();this.zoom=Math.max(.2,Math.min(7,this.zoom*Math.exp(-e.deltaY*.001)));this.draw();},{passive:false});
    canvas.addEventListener('dblclick',()=>this.fit());
    canvas.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','Home'].includes(e.key))return;e.preventDefault();if(e.key==='ArrowLeft')this.ry-=.1;if(e.key==='ArrowRight')this.ry+=.1;if(e.key==='ArrowUp')this.rx-=.1;if(e.key==='ArrowDown')this.rx+=.1;if(e.key==='+')this.zoom=Math.min(7,this.zoom*1.1);if(e.key==='-')this.zoom=Math.max(.2,this.zoom/1.1);if(e.key==='Home')this.fit();this.draw();});
    new ResizeObserver(()=>this.draw()).observe(canvas);$('show-operands').addEventListener('change',()=>this.fit());$('fit').addEventListener('click',()=>this.fit());
  }
  frame(){const frame=meshFrame(this.items.filter(item=>!item.line||$('show-operands').checked).map(item=>item.mesh));this.center=frame.center;this.radius=frame.radius;}
  fit(){this.frame();this.rx=-.52;this.ry=.65;this.zoom=1;this.draw();}
  set(result){
    if(!this.gl)return;const gl=this.gl;for(const item of this.items)gl.deleteBuffer(item.buffer);this.items=[];
    const meshes=result?[{mesh:result.mesh,color:[.04,.53,.48],line:false},{mesh:result.operands.a,color:[.38,.54,.72],line:true},{mesh:result.operands.b,color:[.78,.52,.25],line:true}]:[];
    for(const {mesh,color,line} of meshes){
      const p=mesh.positions,t=mesh.triangles;
      const data=[];
      for(let i=0;i<t.length;i+=3){const a=t[i]*3,b=t[i+1]*3,c=t[i+2]*3;const u=[p[b]-p[a],p[b+1]-p[a+1],p[b+2]-p[a+2]],v=[p[c]-p[a],p[c+1]-p[a+1],p[c+2]-p[a+2]];const n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],len=Math.hypot(...n)||1;for(const index of (line?[a,b,b,c,c,a]:[a,b,c]))data.push(p[index],p[index+1],p[index+2],n[0]/len,n[1]/len,n[2]/len);}
      const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data),gl.STATIC_DRAW);this.items.push({buffer,count:data.length/6,color,line,mesh});
    }
    this.frame();
    this.draw();
  }
  draw(){
    if(!this.gl)return;const gl=this.gl,c=this.canvas;const width=Math.max(1,Math.round(c.clientWidth*devicePixelRatio)),height=Math.max(1,Math.round(c.clientHeight*devicePixelRatio));if(c.width!==width||c.height!==height){c.width=width;c.height=height;}
    gl.viewport(0,0,width,height);gl.clearColor(.94,.965,.956,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.useProgram(this.program);
    const x=this.rx,y=this.ry,cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y);
    gl.uniformMatrix3fv(this.locations.rotation,false,new Float32Array([cy,sx*sy,-cx*sy,0,cx,sx,sy,-sx*cy,cx*cy]));gl.uniform3fv(this.locations.center,this.center);gl.uniform1f(this.locations.aspect,width/height);gl.uniform1f(this.locations.scale,.8*this.zoom/this.radius);
    for(const item of this.items){if(item.line&&!$('show-operands').checked)continue;gl.bindBuffer(gl.ARRAY_BUFFER,item.buffer);gl.enableVertexAttribArray(this.position);gl.enableVertexAttribArray(this.normal);gl.vertexAttribPointer(this.position,3,gl.FLOAT,false,24,0);gl.vertexAttribPointer(this.normal,3,gl.FLOAT,false,24,12);gl.uniform3fv(this.locations.color,item.color);gl.uniform1i(this.locations.line,item.line?1:0);if(item.line)gl.disable(gl.POLYGON_OFFSET_FILL);else{gl.enable(gl.POLYGON_OFFSET_FILL);gl.polygonOffset(1,1);}gl.drawArrays(item.line?gl.LINES:gl.TRIANGLES,0,item.count);}
  }
}
const renderer=new MeshView($('viewport'));
renderOperands();
let restored=null;
try {const raw=localStorage.getItem(STORAGE);if(raw&&raw.length<=MAX_FILE)restored=JSON.parse(raw);else if(raw)localStorage.removeItem(STORAGE);} catch {try{localStorage.removeItem(STORAGE);}catch{}}
if(restored) {
  status('正在校验浏览器保存的上次项目…');
  const recovery=run(restored,true); const recoveryGeneration=generation;
  recovery.then(ok=>{if(!ok&&generation===recoveryGeneration&&!active&&!lifecyclePending&&!stopped){status($('status').textContent+' 默认输入和原恢复副本已保留；可重试、打开有效项目或重置示例。','error');}});
} else run();
