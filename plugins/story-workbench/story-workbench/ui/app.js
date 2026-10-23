const CONFIG = {"name": "小说创作台", "description": "管理本地小说项目、人物、章节与修订历史；在中文编辑器中添加可重新定位的原文批注，不自动生成或改写正文。", "version": "1.0.0"};
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

let activeChapter = '', activeHash = '', dirty = false, quoteSelection = null;
$('content').innerHTML = '<div class="grid"><section><div class="panel"><h2>故事项目</h2><div id="projectform"></div><div class="toolbar" id="projectactions"></div><div id="projectmeta" class="muted"></div></div><div class="panel"><h2>人物设定</h2><div id="characterform"></div><div class="toolbar" id="characteractions"></div><div id="characters"></div></div></section><section><div class="panel"><h2>章节编辑</h2><div id="chapterform"></div><div class="toolbar" id="chapteractions"></div><div id="chapters" class="toolbar"></div><div id="editorinfo" class="muted"></div></div><div class="panel"><h2>原文批注</h2><p class="muted">保存正文后，在编辑区选中原文，再填写批注。重复引文不会随意绑定第一处。</p><div id="annotationform"></div><div class="toolbar" id="annotationactions"></div><div id="annotations"></div></div></section></div>';
$('projectform').append(field('项目名称','project-name'));
$('projectactions').append(button('创建项目',()=>call('create_project',revision({name:$('project-name').value})),''),button('导出全部',async()=>{if(dirty){notice('请先保存正文；导出只包含已保存的记录。',true);return;}const r=await call('export_project',{},false);if(r)download('小说项目.json',r.export);}));
$('characterform').append(field('人物编号','character-id','input','hero'),field('人物姓名','character-name'),field('身份','character-role'),field('动机与目标','character-goal','textarea'));
$('characteractions').append(button('保存人物',()=>call('save_character',revision({id:$('character-id').value,name:$('character-name').value,role:$('character-role').value,goal:$('character-goal').value})),''));
$('chapterform').append(field('章节编号','chapter-id','input','chapter-1'),field('章节标题','chapter-title'),field('正文','chapter-content','textarea'));
$('chapter-content').className='editor';
for(const n of ['chapter-id','chapter-title','chapter-content'])$(n).addEventListener('input',()=>{dirty=true;$('editorinfo').textContent='有未保存修改 · 保存后才能批注 / 切换章节';});
$('chapter-content').addEventListener('select',()=>{const e=$('chapter-content');quoteSelection={start:e.selectionStart,end:e.selectionEnd,text:e.value.slice(e.selectionStart,e.selectionEnd)};});
$('chapteractions').append(button('保存章节',async()=>{const r=await call('save_chapter',revision({id:$('chapter-id').value,title:$('chapter-title').value,content:$('chapter-content').value,chapter_revision:activeChapter===$('chapter-id').value?activeHash:''}),false);if(r){dirty=false;state=r;activeChapter=$('chapter-id').value;activeHash=r.chapters.find(c=>c.id===activeChapter).hash;render();}},''),button('新建章节',()=>{if(dirty){notice('请先保存当前修改。',true);return;}activeChapter='';activeHash='';$('chapter-id').value='chapter-'+((state?.chapters.length||0)+1);$('chapter-title').value='';$('chapter-content').value='';quoteSelection=null;}));
$('annotationform').append(field('批注内容','annotation-note','textarea'));
$('annotationactions').append(button('为选中原文添加批注',async()=>{if(dirty){notice('正文尚未保存，请先保存再批注。',true);return;}if(!quoteSelection?.text){notice('请先在正文编辑器中选中原文。',true);return;}const r=await call('annotate',revision({chapter_id:activeChapter,chapter_revision:activeHash,quote:quoteSelection.text,start_hint:quoteSelection.start,end_hint:quoteSelection.end,note:$('annotation-note').value}));if(r)$('annotation-note').value='';},''));
async function refresh(){if(dirty){notice('请先保存当前修改，再刷新记录。',true);return;}await call('status');}
function loadChapter(c){if(dirty){notice('请先保存当前修改，再切换章节。',true);return;}activeChapter=c.id;activeHash=c.hash;$('chapter-id').value=c.id;$('chapter-title').value=c.title;$('chapter-content').value=c.content;quoteSelection=null;$('editorinfo').textContent=`已保存 · ${c.writing_units} 非空白字（含标点） · ${c.hash.slice(0,12)}`;renderAnnotations();}
function renderAnnotations(){clear($('annotations'));for(const a of state.annotations.filter(a=>a.chapter_id===activeChapter)){const el=node('div',undefined,'annotation');el.append(node('blockquote',a.quote),node('p',a.note),node('span',(a.status==='resolved'?'已解决 · ':'待处理 · ')+({attached:'已定位',relocated:'已重新定位',detached:'已脱离原文，需重新定位'}[a.anchor.state]||a.anchor.state),'tag'));if(a.status!=='resolved')el.append(button('标记解决',()=>call('resolve_annotation',revision({annotation_id:a.id}))));$('annotations').append(el);}}
function render(){ $('projectmeta').textContent=state.project_name?`${state.project_name} · ${state.chapters.length} 章 · ${state.history.length} 份历史修订`:'每个工作目录独立保存一个项目。';clear($('characters'));for(const c of state.characters){const e=node('div',undefined,'card');e.append(node('h3',c.name),node('p',c.role,'muted'),node('p',c.goal));e.append(button('编辑设定',()=>{$('character-id').value=c.id;$('character-name').value=c.name;$('character-role').value=c.role;$('character-goal').value=c.goal;}));$('characters').append(e);}clear($('chapters'));for(const c of state.chapters)$('chapters').append(button(c.title,()=>loadChapter(c)));if(activeChapter&&!dirty){const c=state.chapters.find(c=>c.id===activeChapter);if(c)loadChapter(c);}renderAnnotations();}
refresh();
