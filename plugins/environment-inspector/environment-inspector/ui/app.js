const CONFIG = {"name": "本机环境探针", "description": "主动观测本机系统、标准位置工具链和 TCP 监听端口，保存与比较快照，提供中文筛选界面；不结束进程、不读取密钥。", "version": "1.0.0"};
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

let toolFilter='',portFilter='';
$('content').innerHTML='<div class="metrics" id="metrics"></div><div class="toolbar" id="probeactions"></div><div class="grid"><section><div class="panel"><h2>快照对比</h2><div id="compareform"></div><div class="toolbar" id="compareactions"></div><div id="comparison" class="pre">至少保留两份快照后，可以比较工具版本与监听端口变化。</div></div><div class="panel"><h2>观测边界</h2><p class="muted">所有观测由你主动触发。不读取密钥、配置文件、用户名、设备名或网卡地址；不结束进程、不修改系统。</p><p id="limits" class="muted"></p></div></section><section><div class="panel"><h2>工具链可用性</h2><div id="toolfilter"></div><div id="tools"></div></div><div class="panel"><h2>TCP 监听端口</h2><p id="port-note" class="muted"></p><div id="portfilter"></div><div id="ports"></div></div></section></div>';
$('probeactions').append(button('执行一次只读探测',()=>call('probe',revision()),''),button('导出观测快照',async()=>{const r=await call('export_snapshots',{},false);if(r)download('本机环境快照.json',r.export);}));
$('compareform').append(field('之前的快照','before-id','select'),field('之后的快照','after-id','select'));
$('compareactions').append(button('比较两份快照',async()=>{const r=await call('compare',{before_id:$('before-id').value,after_id:$('after-id').value},false);if(r)$('comparison').textContent=JSON.stringify(r.comparison,null,2);}));
$('toolfilter').append(field('筛选工具名称','tool-filter'));$('tool-filter').addEventListener('input',()=>{toolFilter=$('tool-filter').value.toLowerCase();renderTables();});
$('portfilter').append(field('筛选端口或程序名称','port-filter'));$('port-filter').addEventListener('input',()=>{portFilter=$('port-filter').value.toLowerCase();renderTables();});
async function refresh(){await call('status');}
function renderTables(){const s=state.snapshots.at(-1);clear($('tools'));clear($('ports'));if(!s){$('tools').append(node('div','尚无观测。点击“执行一次只读探测”。','empty'));$('ports').append(node('div','未观测','empty'));return;}const tools=s.tools.filter(t=>t.name.toLowerCase().includes(toolFilter));$('tools').append(table(['工具','状态','版本 / 说明'],tools.map(t=>[t.name,({available:'可用',missing:'标准位置未找到',unavailable:'暂不可用'})[t.status],t.version||t.note])));const ports=s.ports.filter(p=>(p.port+' '+p.command).toLowerCase().includes(portFilter));if(ports.length)$('ports').append(table(['端口','程序','PID','绑定范围'],ports.map(p=>[p.port,p.command,p.pid,({'all-interfaces':'所有接口',loopback:'本机回环','other-interface':'其他接口'})[p.bind]])));else $('ports').append(node('div',s.port_status==='observed'?'当前筛选没有匹配记录。':'端口观测不可用，不能断言没有监听服务。','empty'));}
function render(){const s=state.snapshots.at(-1);clear($('metrics'));for(const[v,l]of [[state.snapshots.length,'已保存快照'],[s?s.tools.filter(t=>t.status==='available').length:'—','标准位置可用工具'],[s?.port_status==='observed'?s.ports.length:'未观测','已观测监听端口']])$('metrics').append(metric(v,l));$('port-note').textContent=s?.port_note||'待执行观测。';$('limits').textContent=s?`${s.platform} / ${s.architecture} · ${s.observed_at}\n${s.limits}`:'';for(const [target,last]of [['before-id',false],['after-id',true]]){const sel=$(target),old=sel.value;clear(sel);for(const item of state.snapshots){const opt=node('option',`${item.id} · ${new Date(item.observed_at).toLocaleTimeString('zh-CN')}`);opt.value=item.id;sel.append(opt);}if(state.snapshots.some(x=>x.id===old))sel.value=old;else sel.value=(last?state.snapshots.at(-1):state.snapshots.at(-2))?.id||state.snapshots[0]?.id||'';}renderTables();}
refresh();
