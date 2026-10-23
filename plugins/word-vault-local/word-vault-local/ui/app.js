const CONFIG = {"name": "词汇练习室", "description": "按学习者保存英文词条、出现次数与连对掌握状态；在中文交互界面完成四选一、错词复习和导出，无需额外账号。", "version": "1.0.0"};
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

let learner = 'learner-1', filter = '';
$('content').innerHTML = '<div class="metrics" id="metrics"></div><div class="grid"><section class="panel"><h2>把新词放进练习库</h2><p class="muted">释义由你或当前会话提供，不调用外部词典。重复词元会计次；释义变更会重置连对。</p><div id="wordform"></div><div class="toolbar" id="wordactions"></div><div class="warning">仅处理你提供的词条。不包含课本图片、第三方记忆卡模板或语音服务。</div></section><section><div class="panel"><h2>词库与掌握进度</h2><div id="wordfilter"></div><div id="wordtable"></div></div><div class="panel"><h2>四选一练习</h2><div class="toolbar" id="quizactions"></div><div id="quiz"></div></div></section></div>';
$('wordform').append(field('学习者编号（彼此独立）','learner','input',learner),field('英文单词 / 词组','term'),field('中文释义','meaning'));
$('learner').addEventListener('change', () => { learner = $('learner').value.trim(); refresh(); });
$('wordactions').append(button('保存并计次',async()=>{ const r = await call('add_words',revision({learner,entries:[{term:$('term').value,meaning:$('meaning').value}]})); if(r){$('term').value='';$('meaning').value='';} },''));
$('wordfilter').append(field('搜索词条或释义','search-word'));
$('search-word').addEventListener('input',()=>{filter=$('search-word').value.toLowerCase();renderWords();});
$('quizactions').append(button('开始练习',()=>call('start_quiz',revision({learner,size:4})),''),button('复习错词',()=>call('start_quiz',revision({learner,size:4,wrong_only:true}))),button('导出此词库',async()=>{const r=await call('export_bank',{learner},false);if(r)download('词汇练习库.json',r.export);}));
async function refresh(){await call('status',{learner});}
function renderWords(){clear($('wordtable'));const rows=(state?.words||[]).filter(w=>(w.term+' '+w.meaning).toLowerCase().includes(filter)).map(w=>[w.term,w.meaning,w.seen_count,w.streak>=3?'已掌握':`${w.streak}/3 连对`,w.wrong_count]);if(rows.length)$('wordtable').append(table(['词条','释义','出现','掌握','错题'],rows));else $('wordtable').append(node('div','当前没有匹配的词条。','empty'));}
function render(){clear($('metrics'));for(const [v,l]of [[state.summary.total,'词条'],[state.summary.mastered,'三次连对已掌握'],[state.summary.wrong,'曾答错的词']])$('metrics').append(metric(v,l));renderWords();clear($('quiz'));const quiz=state.quiz;if(!quiz){$('quiz').append(node('div','添加至少四个不同释义的词条，开始第一轮练习。','empty'));return;}
  $('quiz').append(node('p',`${quiz.finished?'本轮完成':'练习进行中'} · 已答对 ${quiz.correct}/${quiz.questions.length} 题`,'muted'));
  for(const q of quiz.questions){const card=node('div',undefined,'question');card.append(node('h3',`${q.id+1}. ${q.term}`));const opts=node('div',undefined,'options');for(const [i,value]of q.options.entries()){const b=button(value,()=>call('answer',revision({learner,quiz_id:quiz.id,question_id:q.id,option_index:i})),'');if(q.chosen_index!==null){b.dataset.finished='true';b.disabled=true;if(i===q.chosen_index)b.className=q.is_correct?'correct':'wrong';}opts.append(b);}card.append(opts);if(q.chosen_index!==null)card.append(node('p',q.is_correct?'回答正确':`正确释义：${q.correct_meaning}`,'muted'));$('quiz').append(card);}}
refresh();
