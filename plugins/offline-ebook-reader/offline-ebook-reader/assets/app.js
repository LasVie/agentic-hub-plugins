/* Adapted chapter/offset mathematics from dsh-novel 0.8.1, Copyright 2026 xrn1997.
 * Apache-2.0; see ../licenses/dsh-novel/LICENSE. Changed 2026-10-27 by Cai Zhenze:
 * independent text-only UI, native loopback API, explicit saves, optimistic revisions;
 * no DSH/React dependencies or online book sources. */
'use strict';
const $ = id => document.getElementById(id);
let state, bookId = null, chapters = [], loading = false, timer, queue = Promise.resolve();
const reader = $('reader');
function say(text, error = false) { $('message').textContent = text; $('message').className = error ? 'error' : ''; }
async function api(endpoint, body) {
  const response = await fetch('api/' + endpoint, body === undefined ? {cache:'no-store'} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  const value = await response.json();
  if (!response.ok || !value.ok) throw new Error(value.error?.message || value.message || '操作失败，请重新读取状态。');
  return value;
}
function preferences(p) {
  document.body.classList.remove('dark', 'light'); if (p.theme !== 'paper') document.body.classList.add(p.theme);
  document.documentElement.style.setProperty('--font', p.font_size + 'px');
  document.documentElement.style.setProperty('--line', String(p.line_height));
  document.documentElement.style.setProperty('--width', p.width + 'px');
  for (const [id, value] of [['font',p.font_size],['line',p.line_height],['width',p.width],['theme',p.theme]]) {
    const select = $(id); if (![...select.options].some(o => o.value === String(value))) { const option = document.createElement('option'); option.value = String(value); option.textContent = String(value); select.append(option); } select.value = String(value);
  }
}
function drawShelf() {
  $('shelf').replaceChildren();
  if (!state.books.length) { const p = document.createElement('p'); p.textContent = '书架为空；请先通过插件工具导入一本TXT或EPUB。'; $('shelf').append(p); }
  state.books.forEach(b => {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = b.title;
    const small = document.createElement('small'); small.textContent = `${b.format.toUpperCase()} · ${b.chapter_count}章 · 上次第${b.progress.chapter_index + 1}章`;
    button.append(small); button.classList.toggle('selected', b.book_id === bookId);
    button.addEventListener('click', () => openBook(b.book_id)); $('shelf').append(button);
  });
}
// Ratio uses this chapter's measured height on both save and restore, including the last chapter.
function anchors() { return [...reader.querySelectorAll('.chapter')].map((node,index) => ({index, node, start:node.getBoundingClientRect().top - reader.getBoundingClientRect().top + reader.scrollTop - reader.clientTop, height:node.getBoundingClientRect().height})); }
function position() {
  const list = anchors(); let a = list[0];
  for (const candidate of list) { if (candidate.start <= reader.scrollTop + 1) a = candidate; else break; }
  return a ? {chapter_index:a.index, offset_ratio:Math.min(1,Math.max(0,(reader.scrollTop-a.start)/a.height))} : {chapter_index:0, offset_ratio:0};
}
function showPosition() { if (bookId) { const p = position(); $('position').textContent = `当前：第${p.chapter_index + 1}章 / 共${chapters.length}章 · 章内约${Math.round(p.offset_ratio * 100)}%`; } }
function restore(p) {
  const a = anchors()[p.chapter_index]; if (!a) return;
  reader.scrollTop = Math.min(Math.max(0, reader.scrollHeight-reader.clientHeight), Math.max(0,a.start + p.offset_ratio*a.height)); showPosition();
}
function serial(job) { queue = queue.then(job, job); return queue; }
async function savePosition(explicit = false) {
  if (!bookId || loading) return;
  const id = bookId, p = position();
  return serial(async () => {
    if (id !== bookId) return;
    try { state = await api('save', {action:'progress',book_id:id,...p,expected_revision:state.revision}); if (explicit) say('阅读位置已保存；可刷新或关闭后从同一书架继续。'); drawShelf(); }
    catch(e) { say(e.message + ' 请刷新书架后重试；未宣称保存成功。', true); }
  });
}
async function openBook(id) {
  if (loading) return;
  clearTimeout(timer); await savePosition(false); loading = true; $('save').disabled = true;
  try {
    const value = await api('book', {book_id:id}); bookId=id; chapters=value.chapters; state.revision=value.revision;
    preferences(value.preferences); reader.replaceChildren(); $('toc').replaceChildren();
    chapters.forEach((chapter,index) => {
      const section=document.createElement('section'); section.className='chapter';
      const title=document.createElement('h3'); title.textContent=chapter.title;
      const text=document.createElement('div'); text.className='text'; text.textContent=chapter.text; section.append(title,text); reader.append(section);
      const button=document.createElement('button'); button.type='button'; button.textContent=`${index+1}. ${chapter.title}`;
      button.addEventListener('click',()=>{restore({chapter_index:index,offset_ratio:0}); savePosition(true);}); $('toc').append(button);
    });
    $('book-title').textContent=value.book.title;
    $('book-meta').textContent=`${value.book.original_name} · ${value.book.format.toUpperCase()} · ${chapters.length}章 · v${value.version}`;
    $('warning-list').replaceChildren(); (value.book.warnings.length ? value.book.warnings : ['TXT按标题行切章，未修改原始文件；无法识别的标题保留在正文中。']).forEach(w=>{ const li=document.createElement('li'); li.textContent=w; $('warning-list').append(li); });
    drawShelf(); await new Promise(requestAnimationFrame); restore(value.book.progress);
    say(`已打开「${value.book.title}」，恢复第${value.book.progress.chapter_index+1}章的已保存位置。请核对目录和实际正文。`);
  } catch(e) { say(e.message,true); }
  finally { loading=false; $('save').disabled=!bookId; }
}
async function refresh() {
  if (loading) return;
  clearTimeout(timer); await queue;
  try { state=await api('library'); preferences(state.preferences); drawShelf(); say(`书架已读取：${state.books.length}本 · v${state.version}`); if (!bookId && state.current_book && state.books.some(b=>b.book_id===state.current_book)) await openBook(state.current_book); }
  catch(e) { say(e.message,true); }
}
reader.addEventListener('scroll',()=>{ showPosition(); if (!loading) { clearTimeout(timer); timer=setTimeout(()=>savePosition(false),700); } });
$('save').addEventListener('click',()=>{clearTimeout(timer);savePosition(true);});
$('refresh').addEventListener('click',refresh);
$('preferences').addEventListener('click',async()=>{
  if (!state || loading) return;
  clearTimeout(timer); const p=position();
  const prefs={font_size:Number($('font').value),line_height:Number($('line').value),width:Number($('width').value),theme:$('theme').value};
  await savePosition(false);
  await serial(async()=>{try {state=await api('save',{action:'preferences',preferences:prefs,expected_revision:state.revision}); loading=true; preferences(prefs); await new Promise(requestAnimationFrame); restore(p); say('阅读设置已保存，正文位置按章节比例保持。');}catch(e){say(e.message,true);}finally{loading=false;}});
});
window.addEventListener('pagehide',()=>{if (bookId && !loading && state) {const data={action:'progress',book_id:bookId,...position(),expected_revision:state.revision};fetch('api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),keepalive:true}).catch(()=>{});}});
refresh();
