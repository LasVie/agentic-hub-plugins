'use strict';
const $ = id => document.getElementById(id), E = Mechanics;
let scene = E.example('fall'), selected = scene.bodies[0].id, result = null, frame = 0;
let worker = null, deadline = null, job = 0, playing = false, playStart = 0, playFrame = 0;
const colors = ['#dfb85e', '#80c1c0', '#a6ba8b', '#d69c86', '#aaa4ca'];
const fmt = v => Number.isFinite(v) ? Number(v.toFixed(4)).toString() : '—';
function message(text, error = false) { $('message').textContent = text; $('message').className = 'message' + (error ? ' error' : ''); }
function stopWorker() { if (worker) worker.terminate(); worker = null; clearTimeout(deadline); deadline = null; }
function pause() { playing = false; $('play').textContent = '播放'; }
function invalidate(text = '初始条件已改变；旧结果已清除。请重新计算。') {
  job++; stopWorker(); pause(); result = null; frame = 0;
  $('run').disabled = false; $('result-badge').textContent = '等待计算';
  for (const id of ['play', 'rewind', 'frame', 'csv']) $(id).disabled = true;
  $('frame').value = 0; message(text); draw();
}
function inputField(parent, text, value, update, options = {}) {
  const label = document.createElement('label'); label.textContent = text;
  let control;
  if (options.choices) {
    control = document.createElement('select');
    for (const [v, label] of options.choices) { const opt = document.createElement('option'); opt.value = v; opt.textContent = label; control.append(opt); }
    control.value = value;
  } else {
    control = document.createElement('input'); control.type = options.type || 'number';
    if (control.type === 'checkbox') control.checked = value; else control.value = value;
    if (control.type === 'number') control.step = 'any';
  }
  control.setAttribute('aria-label', text);
  control.addEventListener(control.type === 'checkbox' || options.choices ? 'change' : 'input', () => {
    const v = control.type === 'checkbox' ? control.checked : control.type === 'number' ? (control.value === '' ? NaN : Number(control.value)) : control.value;
    update(v); invalidate();
  }); label.append(control); parent.append(label); return control;
}
function renderForms() {
  $('title').value = scene.title; $('gravity').value = scene.gravity; $('duration').value = scene.duration;
  if (!scene.bodies.some(b => b.id === selected)) selected = scene.bodies[0].id;
  $('selected').replaceChildren();
  for (const b of scene.bodies) { const opt = document.createElement('option'); opt.value = b.id; opt.textContent = b.label + ' · ' + b.id; $('selected').append(opt); }
  $('selected').value = selected; renderBody(); renderConstraints(); draw();
}
function renderBody() {
  const b = scene.bodies.find(b => b.id === selected), root = $('body-fields'); root.replaceChildren();
  inputField(root, '名称', b.label, v => { b.label = v; $('selected').selectedOptions[0].textContent = v + ' · ' + b.id; }, {type: 'text'});
  inputField(root, '形状', b.shape, v => { b.shape = v; renderBody(); }, {choices: [['rectangle', '矩形'], ['circle', '近似圆']]});
  const pair = document.createElement('div'); pair.className = 'two'; root.append(pair);
  const fields = [['x','横坐标 X'],['y','纵坐标 Y'], ...(b.shape === 'circle' ? [['radius','圆半径']] : [['width','宽度'],['height','高度']]), ['angle','初始转角 · 度'], ['mass','质量 · 自定义单位'], ['vx','初速度 X · 单位/秒'], ['vy','初速度 Y · 单位/秒'], ['friction','摩擦系数 0—1'], ['frictionAir','空气阻尼 0—0.1'], ['restitution','恢复系数 0—1']];
  for (const [key, title] of fields) inputField(pair, title, b[key], value => { b[key] = value; });
  inputField(root, '锁定转动（理想平动约束）', b.rotationLocked, value => { b.rotationLocked = value; }, {type: 'checkbox'});
  inputField(root, '静止物体（速度必须为零）', b.static, value => { b.static = value; }, {type: 'checkbox'});
}
function renderConstraints() {
  $('constraint-count').textContent = '(' + scene.constraints.length + '/16)'; $('constraint-fields').replaceChildren();
  for (const c of scene.constraints) {
    const box = document.createElement('div'); box.className = 'joint'; const title = document.createElement('b'); title.textContent = c.id; box.append(title);
    const choices = scene.bodies.map(b => [b.id, b.label + ' · ' + b.id]);
    inputField(box, '端点甲', c.bodyA || '', v => { c.bodyA = v || null; }, {choices: [['', '固定点'], ...choices]});
    inputField(box, '端点乙', c.bodyB, v => { c.bodyB = v; }, {choices});
    const pair = document.createElement('div'); pair.className = 'two'; box.append(pair);
    for (const [key, label] of [['x','固定点 X'],['y','固定点 Y'],['length','约束长度'],['stiffness','刚度 0.1—1']]) inputField(pair, label, c[key], v => { c[key] = v; });
    const remove = document.createElement('button'); remove.textContent = '删除约束'; remove.className = 'danger'; remove.onclick = () => { scene.constraints = scene.constraints.filter(x => x !== c); renderConstraints(); invalidate(); }; box.append(remove); $('constraint-fields').append(box);
  }
}
function installScene(value, notice) { const checked = E.validate(value); scene = checked; selected = scene.bodies[0].id; invalidate(notice); renderForms(); }
for (const button of document.querySelectorAll('[data-example]')) button.onclick = () => installScene(E.example(button.dataset.example), '示例已载入；请计算后观察实际结果。');
for (const id of ['title', 'gravity', 'duration']) $(id).addEventListener('input', () => { scene[id] = id === 'title' ? $(id).value : $(id).value === '' ? NaN : Number($(id).value); invalidate(); });
$('selected').onchange = () => { selected = $('selected').value; renderBody(); draw(); };
for (const shape of ['rectangle', 'circle']) $('add-' + shape).onclick = () => {
  if (scene.bodies.length >= 32) return message('最多32个物体。', true);
  let i = 1; while (scene.bodies.some(b => b.id === 'body' + i)) i++;
  const b = E.body('body' + i, 500, 200, {shape, label: shape === 'circle' ? '新增圆' : '新增矩形'});
  scene.bodies.push(b); selected = b.id; invalidate(); renderForms();
};
$('remove').onclick = () => {
  if (scene.bodies.length === 1) return message('场景至少保留一个物体。', true);
  scene.bodies = scene.bodies.filter(b => b.id !== selected);
  scene.constraints = scene.constraints.filter(c => c.bodyA !== selected && c.bodyB !== selected);
  selected = scene.bodies[0].id; invalidate(); renderForms();
};
$('add-constraint').onclick = () => {
  if (scene.constraints.length >= 16) return message('最多16个约束。', true);
  const b = scene.bodies.find(b => b.id === selected); let i = 1;
  while (scene.constraints.some(c => c.id === 'joint' + i)) i++;
  scene.constraints.push({id: 'joint' + i, bodyA: null, bodyB: selected, x: b.x, y: Math.max(0, b.y - 150), length: 150, stiffness: 1});
  invalidate(); renderConstraints(); $('constraints').open = true;
};
$('edit').onclick = () => invalidate('已回到初始场景，可拖动或编辑参数；重新计算后才能播放。');
$('help').onclick = () => { $('boundaries').open = true; $('boundaries').scrollIntoView({behavior:'smooth'}); };
$('run').onclick = () => {
  invalidate('正在工作线程中计算；最多8秒，不调用模型。');
  try {
    const input = E.validate(scene), thisJob = job;
    worker = new Worker('worker.js'); $('run').disabled = true; $('result-badge').textContent = '正在计算';
    deadline = setTimeout(() => { if (job === thisJob) { invalidate(); message('计算超过8秒，已结束线程；没有可用结果。请减少物体或时长。', true); } }, 8000);
    worker.onmessage = event => {
      if (job !== thisJob || event.data.job !== thisJob) return;
      stopWorker(); $('run').disabled = false;
      if (event.data.error) { invalidate(); message(event.data.error, true); return; }
      result = event.data.result; frame = 0;
      $('frame').max = result.frames.length - 1; $('frame').value = 0;
      for (const id of ['play', 'rewind', 'frame', 'csv']) $(id).disabled = false;
      $('result-badge').textContent = '计算完成';
      message('计算完成：' + result.frames.length + '帧。点击播放或拖动时间滑块查看实际采样。' + (result.outside_view ? '部分运动超出画布，数值仍保留。' : ''));
      draw();
    };
    worker.onerror = () => { if (job === thisJob) { invalidate(); message('本地工作线程未正常完成；请检查插件文件与浏览器。没有替代结果。', true); } };
    worker.postMessage({job: thisJob, scene: input});
  } catch (error) { invalidate(); message(error.message, true); }
};
function tick(now) {
  if (!playing || !result) return;
  frame = Math.min(result.frames.length - 1, playFrame + Math.floor((now - playStart) * 120 / 1000));
  $('frame').value = frame; draw(); if (frame === result.frames.length - 1) pause(); else requestAnimationFrame(tick);
}
$('play').onclick = () => { if (playing) return pause(); if (!result) return; if (frame === result.frames.length - 1) frame = 0; playing = true; playFrame = frame; playStart = performance.now(); $('play').textContent = '暂停'; requestAnimationFrame(tick); };
$('rewind').onclick = () => { pause(); frame = 0; $('frame').value = 0; draw(); };
$('frame').oninput = () => { pause(); frame = Number($('frame').value); draw(); };
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
function positions() { return result ? result.frames[frame].bodies : scene.bodies.map(b => ({...b, angle: b.angle * Math.PI / 180})); }
function draw() {
  const ctx = $('world').getContext('2d'); ctx.clearRect(0,0,1000,650); ctx.fillStyle = '#102b35'; ctx.fillRect(0,0,1000,650);
  ctx.strokeStyle = '#25414a'; ctx.lineWidth = 1;
  for (let x = 0; x <= 1000; x += 100) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,650); ctx.stroke(); }
  for (let y = 0; y <= 650; y += 100) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(1000,y); ctx.stroke(); }
  const values = positions(), map = new Map(values.map(b => [b.id,b]));
  ctx.fillStyle = '#a8c3c5'; ctx.font = '13px sans-serif'; ctx.fillText(result ? '实际采样 · ' + fmt(result.frames[frame].time) + '秒' : '初始场景 · 可拖动物体', 18, 27);
  ctx.fillText('X →    Y ↓', 900, 27);
  for (const c of scene.constraints) {
    const a = c.bodyA === null ? c : map.get(c.bodyA), b = map.get(c.bodyB);
    if (!a || !b || ![a.x,a.y,b.x,b.y].every(Number.isFinite)) continue;
    ctx.strokeStyle = '#b7b0c9'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke();
    ctx.beginPath(); ctx.arc(a.x,a.y,5,0,2*Math.PI); ctx.stroke();
  }
  scene.bodies.forEach((initial,i) => {
    const b = map.get(initial.id); if (![b.x,b.y,b.angle,initial.radius,initial.width,initial.height].every(Number.isFinite)) return;
    ctx.save(); ctx.translate(b.x,b.y); ctx.rotate(b.angle); const color = initial.static ? '#5b7778' : colors[i % colors.length];
    ctx.fillStyle = color; ctx.strokeStyle = initial.id === selected ? '#fff8da' : color; ctx.lineWidth = initial.id === selected ? 3 : 1;
    ctx.beginPath();
    if (initial.shape === 'circle') {
      // Match Bodies.circle's even-sided polygon approximation (maxSides=25).
      let sides = Math.ceil(Math.max(10, Math.min(25, initial.radius))); if (sides % 2) sides++;
      for (let j=0;j<sides;j++) { const a=(j+0.5)*2*Math.PI/sides; const x=Math.cos(a)*initial.radius,y=Math.sin(a)*initial.radius; j?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.closePath();
    } else ctx.rect(-initial.width/2,-initial.height/2,initial.width,initial.height);
    ctx.fill(); ctx.stroke(); ctx.strokeStyle='#102b35'; ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(initial.shape==='circle'?initial.radius:initial.width/2,0);ctx.stroke();ctx.restore();
    ctx.fillStyle='#dbe8de';ctx.font='13px sans-serif';ctx.fillText(initial.label.slice(0,24),b.x+10,b.y-(initial.shape==='circle'?initial.radius:initial.height/2)-10);
  });
  $('body-name').textContent = scene.bodies.find(b=>b.id===selected)?.label || '—';
  $('frame-count').textContent = result ? result.frames.length : '—'; $('contacts').textContent = result ? result.contact_pairs.length : '—';
  $('time').textContent = result ? fmt(result.frames[frame].time) + ' / ' + scene.duration + '秒' : '—';
  const b = result && map.get(selected);
  $('position').textContent = b ? fmt(b.x)+' / '+fmt(b.y) : '—'; $('velocity').textContent = b ? fmt(b.vx)+' / '+fmt(b.vy) : '—'; $('angle').textContent = b ? fmt(b.angle*180/Math.PI) : '—';
  drawChart();
}
function drawChart() {
  const ctx = $('chart').getContext('2d'); ctx.clearRect(0,0,1100,230); ctx.fillStyle='#102b35';ctx.fillRect(0,0,1100,230);ctx.font='12px sans-serif';ctx.fillStyle='#b7cdce';
  if(!result){ctx.fillText('计算后显示真实纵坐标轨迹',30,115);return;}
  const ys=result.frames.map(f=>f.bodies.find(b=>b.id===selected).y),min=Math.min(...ys),max=Math.max(...ys),pad=Math.max(10,(max-min)*0.1),lo=min-pad,hi=max+pad;
  const X=i=>65+i/(ys.length-1)*1000,Y=y=>185-(y-lo)/(hi-lo)*160;
  ctx.strokeStyle='#36505a';ctx.lineWidth=1;
  for(let i=0;i<5;i++){const y=lo+(hi-lo)*i/4;ctx.beginPath();ctx.moveTo(60,Y(y));ctx.lineTo(1065,Y(y));ctx.stroke();ctx.fillText(fmt(y),6,Y(y)+4);}
  ctx.strokeStyle='#dfb85e';ctx.lineWidth=2;ctx.beginPath();ys.forEach((y,i)=>i?ctx.lineTo(X(i),Y(y)):ctx.moveTo(X(i),Y(y)));ctx.stroke();
  ctx.strokeStyle='#d9e3d8';ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(X(frame),20);ctx.lineTo(X(frame),190);ctx.stroke();ctx.setLineDash([]);ctx.fillText('0秒',60,215);ctx.fillText(scene.duration+'秒',1030,215);
}
let dragging=null;
function pointer(event){const r=$('world').getBoundingClientRect();return{x:(event.clientX-r.left)*1000/r.width,y:(event.clientY-r.top)*650/r.height};}
$('world').onpointerdown=event=>{
  if(result){message('拖动用于编辑初始位置。请先点击“编辑初始场景”；当前回放不会被施加外力。');return;}
  const p=pointer(event);
  const b=[...scene.bodies].reverse().find(b=>{const a=-b.angle*Math.PI/180,dx=p.x-b.x,dy=p.y-b.y,x=dx*Math.cos(a)-dy*Math.sin(a),y=dx*Math.sin(a)+dy*Math.cos(a);return b.shape==='circle'?Math.hypot(x,y)<=b.radius:Math.abs(x)<=b.width/2&&Math.abs(y)<=b.height/2;});
  if(!b)return; selected=b.id;dragging={id:b.id,dx:p.x-b.x,dy:p.y-b.y};$('world').setPointerCapture(event.pointerId);invalidate();renderForms();
};
$('world').onpointermove=event=>{if(!dragging)return;const p=pointer(event),b=scene.bodies.find(b=>b.id===dragging.id);b.x=Math.round(Math.max(0,Math.min(1000,p.x-dragging.dx)));b.y=Math.round(Math.max(0,Math.min(1000,p.y-dragging.dy)));renderBody();draw();};
$('world').onpointerup=$('world').onpointercancel=()=>{dragging=null;};
async function api(path, body) {
  const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const value=await response.json();if(!response.ok||!value.ok){const e=new Error(value.error?.message||'本机请求失败。');e.code=value.error?.code;throw e;}return value;
}
function download(data,name,type){const u=URL.createObjectURL(new Blob([data],{type})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
$('save').onclick=async()=>{try{const value=E.validate(scene);try{await api('api/save',{scene:value});}catch(e){if(e.code!=='overwrite_confirmation'||!confirm('此工作目录已有保存场景。明确替换该场景？'))throw e;await api('api/save',{scene:value,overwrite:true});}message('点击保存时的初始场景已保存；重新载入后须再次计算。');}catch(e){message(e.message,true);}};
$('load').onclick=async()=>{invalidate('正在读取保存场景；旧结果已清除。');const revision=job;try{const value=await api('api/saved');if(job!==revision)return message('读取期间场景已改变，已忽略迟到的读取结果。');if(!value.scene)return message('此工作目录尚未保存场景。');installScene(value.scene,'已读取保存的初始场景；旧结果已清除，请重新计算。');}catch(e){message(e.message,true);}};
$('export').onclick=()=>{try{download(JSON.stringify(E.validate(scene),null,2)+'\n','力学场景-1.0.0.json','application/json');message('已导出初始场景JSON；没有导出陈旧结果。');}catch(e){message(e.message,true);}};
$('import').onclick=()=>$('file').click();
$('file').onchange=async()=>{try{const file=$('file').files[0];if(!file)return;invalidate('正在导入场景；旧结果已清除。');const revision=job;if(file.size>32768)throw new Error('JSON文件不能超过32 KiB。');const value=JSON.parse(await file.text());if(job!==revision)return message('导入期间场景已改变，已忽略迟到的导入。');installScene(value,'JSON初始场景已导入；请重新计算并核对结果。');}catch(e){message('导入失败：'+(e instanceof SyntaxError?'JSON语法无效，请选择本插件导出的场景文件。':e.message),true);}finally{$('file').value='';}};
$('csv').onclick=()=>{try{download(E.csv(result),'力学采样-1.0.0.csv','text/csv;charset=utf-8');message('已导出本次实际采样：'+result.frames.length+'帧 × '+scene.bodies.length+'个物体。');}catch(e){message(e.message,true);}};
renderForms();
