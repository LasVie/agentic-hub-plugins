const CONFIG = {"name": "流程执行台", "description": "校验多阶段流程模板，冻结每次运行快照，以实际文件 SHA-256 记录环节完成证据，提供中文交互看板。", "version": "1.0.0"};
const C = CONFIG;
const key = location.hash.slice(1);
history.replaceState(null, '', location.pathname);
let state = null, busy = false;
const $ = id => document.getElementById(id);
function node(tag, content, cls) { const e = document.createElement(tag); if (content !== undefined) e.textContent = String(content); if (cls) e.className = cls; return e; }
function clear(e) { e.replaceChildren(); }
function notice(message, error = false) { $('notice').textContent = message; $('notice').className = error ? 'error' : ''; }
function button(label, handler, cls = 'secondary') { const b = node('button', label, cls); b.type = 'button'; b.addEventListener('click', handler); return b; }
function field(label, id, kind = 'input', value = '') { const wrap = node('div'), l = node('label', label), input = node(kind); l.htmlFor = id; input.id = id; input.value = value; wrap.append(l, input); return wrap; }
function metric(value, label) { const box = node('div', undefined, 'metric'); box.append(node('strong', value), node('span', label)); return box; }
function table(headers, rows) { const wrap = node('div', undefined, 'tablewrap'), t = node('table'), head = node('thead'), hr = node('tr'); for (const x of headers) hr.append(node('th', x)); head.append(hr); t.append(head); const body = node('tbody'); for (const row of rows) { const tr = node('tr'); for (const x of row) { const td = node('td'); if (x instanceof Node) td.append(x); else td.textContent = String(x ?? ''); tr.append(td); } body.append(tr); } t.append(body); wrap.append(t); return wrap; }
function download(name, data) { const u = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type:'application/json'})), a = node('a'); a.href = u; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(u), 5000); }
async function call(action, payload = {}, redraw = true) {
  if (busy) return null;
  if (!/^[a-f0-9]{64}$/.test(key)) { notice('缺少有效访问凭据。请在 WorkSwarm 重新调用 open_ui，使用它返回的完整链接。', true); return null; }
  busy = true; document.querySelectorAll('button').forEach(b => b.disabled = true);
  try {
    const response = await fetch('/api', {method:'POST',headers:{authorization:'Bearer '+key,'content-type':'application/json'},body:JSON.stringify({action,payload})});
    const r = await response.json();
    if (!r.ok) { notice(r.message || '操作未成功，请刷新后重试。', true); return null; }
    if (redraw) { state = r; render(); }
    notice(r.message || '已读取本地最新记录。'); return r;
  } catch { notice('无法连接本地工作台。数据不会自动丢弃；请重新调用 open_ui。', true); return null; }
  finally { busy = false; document.querySelectorAll('button').forEach(b => { b.disabled = b.dataset.finished === 'true'; }); }
}
function revision(extra = {}) { return {expected_revision:state?.revision ?? 0,...extra}; }
$('title').textContent = C.name; $('subtitle').textContent = C.description; $('aside-title').textContent = C.name; $('version').textContent = '本地 · '+C.version;
$('refresh').addEventListener('click', refresh);
$('shutdown').addEventListener('click', async () => { if (busy) return; try { const r = await fetch('/stop',{method:'POST',headers:{authorization:'Bearer '+key,'content-type':'application/json'},body:'{}'}); const out = await r.json(); notice(out.message); } catch { notice('服务已关闭或不可连接。'); } });

const example={process:{name:'delivery',display_name:'小型交付流程',version:'1.0.0'},phases:[{id:'prepare',name:'准备',links:[{id:'draft',name:'整理草案',prompt:'整理需求与初稿，并保存证据文件。',on_success:'next'}]},{id:'verify',name:'验收',links:[{id:'check',name:'核对结果',prompt:'核对交付与要求一致，提交验证文件。',on_success:'end'}]}]};
let selectedRun='';
$('content').innerHTML='<div class="grid"><section><div class="panel"><h2>流程模板</h2><p class="muted">保留多阶段、环节与 next/end/break/跳转。每次运行冻结模板快照，不自动调用模型或执行命令。</p><div id="templateform"></div><div class="toolbar" id="templateactions"></div><div id="validation"></div></div><div class="panel"><h2>开始一次运行</h2><div id="runform"></div><div class="toolbar" id="runactions"></div></div></section><section><div class="panel"><h2>运行看板</h2><div id="runs" class="toolbar"></div><div id="board" class="cards"></div></div><div class="panel"><h2>完成当前环节</h2><p class="muted">记录实际完成情况与文件 SHA-256。这是证据日志，不代替人对工作质量的判断。</p><div id="evidenceform"></div><div class="toolbar" id="completeactions"></div><div id="trail"></div></div></section></div>';
$('templateform').append(field('JSON 模板','template','textarea',JSON.stringify(example,null,2)));$('template').className='code';
function parsed(){try{return JSON.parse($('template').value);}catch{notice('模板 JSON 无效，请检查逗号、引号与括号。',true);return null;}}
$('templateactions').append(button('校验',async()=>{const t=parsed();if(!t)return;const r=await call('validate_template',{template:t},false);if(r){clear($('validation'));$('validation').append(node('p',r.valid?`校验通过 · ${r.meta.phaseCount} 阶段 / ${r.meta.linkCount} 环节`:r.errors.map(e=>`${e.path}：${e.message}`).join('\n'),r.valid?'tag':'warning'));}}),button('保存模板',()=>{const t=parsed();if(t)return call('save_template',revision({template:t}));},''),button('导出记录',async()=>{const r=await call('export_process',{},false);if(r)download('流程执行记录.json',r.export);}));
$('runform').append(field('本次运行编号','run-id','input','run-1'));
$('runactions').append(button('开始运行',async()=>{const r=await call('start_run',revision({run_id:$('run-id').value}));if(r){selectedRun=$('run-id').value;render();}},''));
$('evidenceform').append(field('实际执行说明','evidence-note','textarea'),field('证据文件相对路径（每行一份）','evidence-files','textarea'));
$('completeactions').append(button('记录证据并完成当前环节',()=>{const r=state?.runs.find(r=>r.id===selectedRun);if(!r){notice('请先选择一个运行。',true);return;}return call('complete_step',revision({run_id:r.id,step_id:r.current,note:$('evidence-note').value,evidence_files:$('evidence-files').value.split('\n').map(x=>x.trim()).filter(Boolean)}));},''),button('恢复暂停的运行',()=>call('resume_run',revision({run_id:selectedRun}))));
async function refresh(){await call('status');}
function render(){clear($('runs'));for(const r of state.runs)$('runs').append(button(`${r.id} · ${({running:'进行中',paused:'已暂停',done:'已完成'})[r.status]||r.status}`,()=>{selectedRun=r.id;render();}));if(!selectedRun)selectedRun=state.runs.at(-1)?.id||'';const r=state.runs.find(r=>r.id===selectedRun);clear($('board'));clear($('trail'));if(!r){$('board').append(node('div','保存模板后，开始一次运行。','empty'));return;}for(const s of r.steps){const done=r.trail.some(t=>t.step_id===s.id),card=node('div',undefined,'card'+(r.current===s.id?' current':done?' done':''));card.append(node('small',s.phase_name),node('h3',s.name||s.id),node('p',s.prompt),node('span',r.current===s.id?'当前环节':done?'已留存证据':'等待','tag'));$('board').append(card);}if(r.trail.length)$('trail').append(table(['环节','执行说明','证据文件','SHA-256'],r.trail.map(t=>[t.step_id,t.note,t.evidence.map(e=>e.path).join('\n'),t.evidence.map(e=>e.sha256).join('\n')])));}
refresh();
