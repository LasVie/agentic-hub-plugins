'use strict';
const $ = id => document.getElementById(id);
const STORAGE = 'queue-capacity-workbench/v1';
const examples = {
  four: {schema: STORAGE, name: '四项作业容量对照', units: 'minutes', capacities: [1, 2], jobs: [0, 1, 2, 3].map((arrival, i) => ({id: `作业${i + 1}`, arrival, service: 4}))},
  burst: {schema: STORAGE, name: '集中到达高峰', units: 'minutes', capacities: [1, 2, 3], jobs: Array.from({length: 10}, (_, i) => ({id: `客户${i + 1}`, arrival: i < 6 ? 0 : 5, service: 2 + i % 3}))},
  idle: {schema: STORAGE, name: '间歇到达的空闲容量', units: 'minutes', capacities: [1, 2], jobs: [0, 8, 16, 24].map((arrival, i) => ({id: `订单${i + 1}`, arrival, service: 3}))}
};
let result = null, selected = 0, index = 0, timer = null, busy = false, generation = 0;
const format = n => Number(n).toLocaleString('zh-CN', {maximumFractionDigits: 3});
const kindName = {arrival: '到达', start: '开始服务', finish: '服务结束'};
function status(message, error = false) { $('status').textContent = message; $('status').classList.toggle('error', error); }
function pause() { if (timer) clearInterval(timer); timer = null; $('play').textContent = '播放'; }
function invalidate() { pause(); generation++; result = null; $('content').hidden = true; $('empty').hidden = false; $('csv').disabled = true; }
function setProject(project) { invalidate(); $('project').value = JSON.stringify(project, null, 2); status('场景已载入，请重新计算。'); }
function tableCell(row, value) { const cell = document.createElement('td'); cell.textContent = String(value); row.append(cell); return cell; }
function svgNode(tag, attrs, text) { const node = document.createElementNS('http://www.w3.org/2000/svg', tag); for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value)); if (text !== undefined) node.textContent = text; return node; }
function timeline(run) {
  const total = run.metrics.completion_time;
  const shown = run.jobs.slice(0, 80), width = 920, left = 125, chartWidth = 770;
  const height = 45 + shown.length * 28;
  const svg = svgNode('svg', {viewBox: `0 0 ${width} ${height}`, height});
  const x = time => left + chartWidth * time / total;
  for (let n = 0; n <= 5; n++) { const time = total * n / 5; svg.append(svgNode('line', {x1: x(time), y1: 28, x2: x(time), y2: height, stroke: '#dce5ee'}), svgNode('text', {x: x(time), y: 17, fill: '#5d7485', 'font-size': 11, 'text-anchor': 'middle'}, format(time))); }
  shown.forEach((job, n) => {
    const y = 35 + n * 28;
    svg.append(svgNode('text', {x: 8, y: y + 13, fill: '#24415b', 'font-size': 12}, job.id.length > 12 ? job.id.slice(0, 11) + '…' : job.id));
    svg.append(svgNode('rect', {x: left, y, width: chartWidth, height: 18, fill: '#eff3f7', rx: 3}));
    const wait = svgNode('rect', {x: x(job.arrival), y, width: Math.max(0, x(job.start) - x(job.arrival)), height: 18, fill: '#df9c32', rx: 2});
    const serve = svgNode('rect', {x: x(job.start), y, width: Math.max(1, x(job.finish) - x(job.start)), height: 18, fill: '#3978bc', rx: 2});
    serve.append(svgNode('title', {}, `${job.id} · 服务台 ${job.server} · 等待 ${format(job.wait)} 分 · 服务 ${format(job.start)}–${format(job.finish)} 分`));
    svg.append(wait, serve);
  });
  const when = index ? run.events[index - 1].time : 0;
  svg.append(svgNode('line', {x1: x(when), y1: 25, x2: x(when), y2: height, stroke: '#bc3f65', 'stroke-width': 2}));
  $('timeline').replaceChildren(svg);
  $('timeline-limit').textContent = run.jobs.length > 80 ? `图中显示前 80 项作业；完整 ${run.jobs.length} 项见 CSV 与事件轨迹。` : `共 ${run.jobs.length} 项作业。横轴为分钟；每行展示该项作业的等候与服务区间。`;
}
function replay() {
  if (!result) return;
  const run = result.runs[selected];
  index = Math.max(0, Math.min(index, run.events.length));
  $('step').max = run.events.length; $('step').value = index;
  const event = index ? run.events[index - 1] : {time: 0, waiting: 0, active: 0, completed: 0};
  $('waiting').textContent = event.waiting; $('active').textContent = event.active; $('completed').textContent = event.completed;
  $('event-summary').textContent = index ? `第 ${index}/${run.events.length} 个事件 · ${format(event.time)} 分钟 · ${event.job_id} ${kindName[event.kind]}${event.server ? `（服务台 ${event.server}）` : ''}` : '回放起点 · 尚未处理事件';
  $('previous').disabled = index === 0; $('next').disabled = index === run.events.length;
  $('events').querySelectorAll('tr').forEach((row, n) => row.classList.toggle('current', n === index - 1));
  timeline(run);
}
function chooseRun(i) {
  pause(); selected = i; index = 0;
  const run = result.runs[selected];
  $('capacities').replaceChildren();
  result.runs.forEach((r, n) => { const button = document.createElement('button'); button.textContent = `${r.capacity} 台`; button.classList.toggle('selected', n === i); button.setAttribute('aria-pressed', String(n === i)); button.onclick = () => chooseRun(n); $('capacities').append(button); });
  $('comparison').querySelectorAll('tbody tr').forEach((row, n) => row.classList.toggle('selected', n === i));
  $('scenario-name').textContent = `${result.project.name} · 当前查看 ${run.capacity} 台服务台 · ${result.engine}`;
  $('event-count').textContent = `${run.events.length} 个事件；按实际引擎顺序排列`;
  $('events').replaceChildren();
  run.events.forEach(event => { const row = document.createElement('tr'); [event.seq, format(event.time), kindName[event.kind], event.job_id, event.server ?? '—', `${event.waiting} / ${event.active} / ${event.completed}`].forEach(v => tableCell(row, v)); $('events').append(row); });
  replay();
}
function showResults(data) {
  result = data; $('empty').hidden = true; $('content').hidden = false; $('csv').disabled = false;
  const body = $('comparison').querySelector('tbody'); body.replaceChildren();
  data.runs.forEach(run => { const row = document.createElement('tr'), m = run.metrics; [run.capacity, format(m.mean_wait), format(m.max_wait), format(m.completion_time), m.max_queue, `${format(m.utilization * 100)}%`].forEach(v => tableCell(row, v)); body.append(row); });
  chooseRun(0);
}
async function calculate() {
  if (busy) return;
  invalidate(); const revision = generation;
  busy = true; $('run').disabled = true; status('正在使用本地 SimPy 引擎计算……');
  try {
    const raw = $('project').value;
    if (new TextEncoder().encode(raw).length > 256 * 1024) throw new Error('场景超过 256 KiB 上限。');
    // Send original JSON bytes so the server can reject duplicate keys.
    const response = await fetch('api/calculate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: `{"request_id":${JSON.stringify(crypto.randomUUID())},"project":${raw}}`});
    const data = await response.json();
    if (revision !== generation) { status('计算期间场景已改变，请重新计算。'); return; }
    if (!response.ok || !data.ok) throw new Error(data.error || '计算失败，请检查场景。');
    showResults(data); status(data.message);
    try { localStorage.setItem(STORAGE, JSON.stringify(data.project)); } catch { status(data.message + ' 浏览器未允许保存场景，请导出 JSON。'); }
  } catch (error) { if (revision === generation) status(error instanceof TypeError || error instanceof SyntaxError ? '无法取得计算结果，请检查场景或重新启动工作台。' : error.message, true); }
  finally { busy = false; $('run').disabled = false; }
}
function download(name, value, type) { const blob = new Blob([value], {type}); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
$('run').onclick = calculate;
$('project').oninput = () => { invalidate(); status('场景已修改，旧结果已清除，请重新计算。'); };
$('reset').onclick = () => { try { localStorage.removeItem(STORAGE); } catch {} $('preset').value = 'four'; setProject(examples.four); };
$('preset').onchange = () => setProject(examples[$('preset').value]);
$('import').onclick = () => $('file').click();
$('file').onchange = async () => { const file = $('file').files[0]; if (!file) return; try { if (file.size > 256 * 1024) throw new Error('场景超过 256 KiB 上限。'); const raw = new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer()); invalidate(); $('project').value = raw; status('已载入待校验的场景。点击计算进行严格验证；无效场景不会覆盖已保存场景。'); } catch { status('导入失败：只支持不超过 256 KiB 的 UTF-8 JSON 文件。', true); } finally { $('file').value = ''; } };
$('save').onclick = () => { if (!result) { status('请先成功计算当前场景，再保存经过校验的 JSON。', true); return; } download('排队场景.json', JSON.stringify(result.project, null, 2), 'application/json;charset=utf-8'); };
$('csv').onclick = () => { if (result) download('容量比较结果.csv', '\uFEFF' + result.csv, 'text/csv;charset=utf-8'); };
$('begin').onclick = () => { pause(); index = 0; replay(); };
$('end').onclick = () => { pause(); index = result.runs[selected].events.length; replay(); };
$('previous').onclick = () => { pause(); index--; replay(); };
$('next').onclick = () => { pause(); index++; replay(); };
$('step').oninput = () => { pause(); index = Number($('step').value); replay(); };
$('play').onclick = () => { if (timer) { pause(); return; } if (index === result.runs[selected].events.length) index = 0; $('play').textContent = '暂停'; timer = setInterval(() => { index++; replay(); if (index === result.runs[selected].events.length) pause(); }, 500); };
$('close').onclick = async () => { if (!confirm('关闭本插件的本机工作台？已导出的文件会保留。')) return; pause(); try { const response = await fetch('api/stop', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: '{}'}); const data = await response.json(); if (!response.ok || !data.ok) throw new Error(); invalidate(); $('run').disabled = true; $('close').disabled = true; status('工作台已关闭。可通过插件工具重新启动。'); } catch { status('无法确认关闭结果，请通过插件工具查询状态。', true); } };
setProject(examples.four);
try { const raw = localStorage.getItem(STORAGE); if (raw && new TextEncoder().encode(raw).length <= 256 * 1024) { const saved = JSON.parse(raw); if (saved.schema === STORAGE) { $('project').value = raw; status('已恢复上次有效计算的场景。请重新计算生成结果。'); } } } catch { status('浏览器保存的场景无效，已恢复默认示例。'); }
