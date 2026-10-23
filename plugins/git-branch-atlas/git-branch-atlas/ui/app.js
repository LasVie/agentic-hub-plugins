const CONFIG = {"name": "Git 分支全景", "description": "只读本地 Git 分支拓扑、父提交与关联工作树，比较两个引用的独有提交和共同祖先，提供可搜索、可点选的中文图谱。", "version": "1.0.0"};
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

let graphFilter='',selectedOid='';
$('content').innerHTML='<div class="metrics" id="metrics"></div><div class="grid"><section><div class="panel"><h2>读取分支拓扑</h2><p class="muted">只读本地分支、提交父节点与工作树；不会切换、拉取、提交或删除分支。</p><div id="scanform"></div><div class="toolbar" id="scanactions"></div></div><div class="panel"><h2>比较两个引用</h2><div id="compareform"></div><div class="toolbar" id="compareactions"></div><div id="compare-result" class="detail">可比较分支名、标签或已有提交的 OID。</div></div><div class="panel"><h2>关联工作树</h2><div id="worktrees"></div></div></section><section><div class="panel"><h2>分支与提交图</h2><div id="graphfilter"></div><div id="graph"></div><p id="graph-note" class="muted"></p></div><div class="panel"><h2>选中提交</h2><div id="commit-detail" class="detail">点击提交行，查看完整父节点和引用。</div></div></section></div>';
$('scanform').append(field('仓库相对工作目录路径','repo-dir','input','.'),field('最多读取的提交数（1–200）','graph-limit','input','80'));
$('scanactions').append(button('读取拓扑',()=>call('scan',revision({repo_dir:$('repo-dir').value,limit:Number($('graph-limit').value)})),''),button('导出图数据',async()=>{const r=await call('export_graph',{},false);if(r)download('Git分支拓扑.json',r.export);}));
$('compareform').append(field('基准引用','base-ref','input','main'),field('目标引用','head-ref','input','HEAD'));
$('compareactions').append(button('比较引用',async()=>{const r=await call('compare_branches',{repo_dir:$('repo-dir').value,base:$('base-ref').value,head:$('head-ref').value},false);if(r){clear($('compare-result'));$('compare-result').append(node('p',`基准独有 ${r.base_only} · 目标独有 ${r.head_only}`),node('p',r.message,'muted'),node('p',`共同祖先：${r.merge_bases.length?r.merge_bases.join(', '):'无'}`,'mono'));}}));
$('graphfilter').append(field('搜索摘要、作者、引用或 OID','graph-filter'));$('graph-filter').addEventListener('input',()=>{graphFilter=$('graph-filter').value.toLowerCase();renderGraph();});
async function refresh(){await call('status');}
function snapshot(){return state?.snapshot||state?.state?.snapshot||null;}
function renderGraph(){clear($('graph'));const s=snapshot();if(!s){$('graph').append(node('div','在仓库工作目录执行一次拓扑读取。','empty'));return;}let found=0;for(const[cidx,c]of s.commits.entries()){if(!(c.subject+' '+c.author+' '+c.refs.join(' ')+' '+c.oid).toLowerCase().includes(graphFilter))continue;found++;const row=node('div',undefined,'graphrow'+(c.oid===selectedOid?' selected':''));row.tabIndex=0;row.setAttribute('role','button');row.setAttribute('aria-label',`查看提交 ${c.oid.slice(0,7)} ${c.subject}`);const lane=s.lanes[cidx];row.append(node('div',lane.columns.map(v=>({node:'●',merge:'◆',pass:'│',gap:' '})[v]).join(' '),'lanes'));const info=node('div');info.append(node('div',c.subject||'（无摘要）'),node('small',`${c.oid.slice(0,8)} · ${c.author} · ${c.refs.join(' / ')}`));row.append(info);function select(){selectedOid=c.oid;clear($('commit-detail'));$('commit-detail').append(node('h3',c.subject),node('p',`OID：${c.oid}`,'mono'),node('p',`父节点：${c.parents.length?c.parents.join('\n'):'根提交'}`,'mono'),node('p',`引用：${c.refs.join(' / ')||'无'}`,'muted'));renderGraph();}row.addEventListener('click',select);row.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});$('graph').append(row);}if(!found)$('graph').append(node('div','没有匹配的提交。','empty'));}
function render(){const s=snapshot();clear($('metrics'));for(const[v,l]of [[s?.branches.length||0,'本地分支'],[s?.commits.length||0,'已读取提交'],[s?.commits.filter(c=>c.parents.length>1).length||0,'合并提交']])$('metrics').append(metric(v,l));renderGraph();$('graph-note').textContent=s?(s.has_more?'已达到读取上限；边界外父节点没有被删除。 ':'')+s.note:'';clear($('worktrees'));if(s?.worktrees.length)$('worktrees').append(table(['路径','分支','状态'],s.worktrees.map(w=>[w.path,w.branch||'分离 HEAD',w.locked?'已锁定':'可读'])));else $('worktrees').append(node('div','尚无记录。','empty'));}
refresh();
