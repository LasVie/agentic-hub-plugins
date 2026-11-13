'use strict';
const $ = id => document.getElementById(id);
const LIMIT = 256 * 1024;
const format = value => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('zh-CN', {maximumFractionDigits: 4}) : '—';
const clone = value => JSON.parse(JSON.stringify(value));
const actionIds = ['run', 'save', 'download', 'validate', 'import', 'preset', 'reset', 'close'];
let project = null, examples = {}, result = null, resultProject = null;
let generation = 0, pending = null, ready = false, closed = false, dirty = false, jsonDirty = false;

function status(message, error = false) {
  $('status').textContent = message;
  $('status').classList.toggle('error', error);
}
function projectWarnings(warnings) {
  $('project-warnings').replaceChildren();
  for (const warning of warnings) {
    const item = document.createElement('li'); item.textContent = warning;
    $('project-warnings').append(item);
  }
  $('project-warnings').hidden = !warnings.length;
}
function refreshControls() {
  for (const id of actionIds) $(id).disabled = !ready || closed || !!pending;
  $('project-json').disabled = !ready || closed;
  $('structured').disabled = !ready || closed || jsonDirty;
  $('cancel').disabled = !pending || pending.kind !== 'solve' || closed;
  $('csv').disabled = closed || !result || !['optimal', 'feasible'].includes(result.status) || !Array.isArray(result.jobs);
  $('save-state').textContent = dirty ? '有未保存修改' : '已保存项目';
  $('save-state').className = 'tag ' + (dirty ? 'warning' : 'neutral');
}
async function request(path, options = {}) {
  const response = await fetch('api/' + path, {
    credentials: 'same-origin',
    headers: {'Accept': 'application/json', ...(options.body !== undefined ? {'Content-Type': 'application/json'} : {})},
    ...options
  });
  let data;
  try { data = await response.json(); } catch { throw new Error('本机服务未返回有效结果，请重新启动工作台。'); }
  if (!response.ok || !data.ok) throw new Error(typeof data.error?.message === 'string' ? data.error.message : '操作未完成，请检查项目或重新启动工作台。');
  return data;
}
function cancelRequest(silent = false) {
  const active = pending;
  if (!active) return;
  pending = null;
  generation++;
  active.controller.abort();
  if (active.kind === 'solve') {
    request('cancel', {method: 'POST', body: JSON.stringify({request_id: active.requestId})})
      .then(() => { if (!silent && !pending && generation === active.cancelGeneration) status('取消请求已确认，本次结果已清除。可重新计算。'); })
      .catch(() => { if (!silent && !pending && generation === active.cancelGeneration) status('已停止等待且清除结果；无法确认后台取消状态。本机求解仍受运行时限约束。', true); });
  }
  active.cancelGeneration = generation;
  refreshControls();
}
function invalidate() {
  cancelRequest(true);
  generation++;
  clearResult();
}
function clearResult() {
  result = null;
  resultProject = null;
  $('result-content').hidden = true;
  $('empty').hidden = false;
  $('csv').disabled = true;
}
function edited() {
  invalidate();
  dirty = true;
  refreshControls();
  status('项目已修改，旧结果已清除。请保存或重新计算。');
}
function numericInput(value, label, onChange) {
  const input = document.createElement('input');
  input.type = 'number'; input.min = '0'; input.max = '1000000'; input.step = '1'; input.inputMode = 'numeric';
  input.value = String(value); input.setAttribute('aria-label', label);
  input.addEventListener('input', () => onChange(input.value === '' ? null : Number(input.value)));
  return input;
}
function cell(row, value, tag = 'td') {
  const element = document.createElement(tag);
  element.textContent = String(value);
  row.append(element);
  return element;
}
function writeJson() { $('project-json').value = JSON.stringify(project, null, 2); }
function renderEditor() {
  $('project-name').textContent = project.name;
  $('resource-inputs').replaceChildren();
  project.resources.forEach((resource, index) => {
    const box = document.createElement('div'); box.className = 'resource-input';
    const label = document.createElement('label'); label.htmlFor = 'capacity-' + index; label.textContent = resource.name + ' · 容量';
    const input = numericInput(resource.capacity, resource.name + '容量', value => { resource.capacity = value; writeJson(); edited(); });
    input.id = label.htmlFor;
    box.append(label, input); $('resource-inputs').append(box);
  });
  $('min-jobs').value = project.min_jobs;
  $('min-jobs').max = project.jobs.length;
  $('job-count').textContent = project.jobs.length + ' 项 · ' + project.resources.length + ' 种资源';
  const head = $('jobs-head'); head.replaceChildren();
  ['编号', '作业名称', '收益', ...project.resources.map(resource => resource.name + '用量')].forEach(name => cell(head, name, 'th').scope = 'col');
  $('jobs-body').replaceChildren();
  project.jobs.forEach(job => {
    const row = document.createElement('tr'); cell(row, job.id);
    const nameCell = cell(row, ''), name = document.createElement('input'); name.type = 'text'; name.className = 'job-name-input'; name.value = job.name; name.maxLength = 80; name.setAttribute('aria-label', job.id + '作业名称');
    name.addEventListener('input', () => { job.name = name.value; writeJson(); edited(); }); nameCell.append(name);
    cell(row, '').append(numericInput(job.value, job.id + '收益', value => { job.value = value; writeJson(); edited(); }));
    project.resources.forEach(resource => cell(row, '').append(numericInput(job.uses[resource.id] ?? 0, job.id + '的' + resource.name + '用量', value => { job.uses[resource.id] = value; writeJson(); edited(); })));
    $('jobs-body').append(row);
  });
}
function setProject(value, saved = false) {
  invalidate();
  project = clone(value); jsonDirty = false; dirty = !saved;
  writeJson(); renderEditor(); refreshControls();
}
function rawProject() {
  const raw = $('project-json').value;
  if (new TextEncoder().encode(raw).length > LIMIT) throw new Error('项目超过 256 KiB 上限。请减少作业或内容。');
  // Keep the original JSON text for the service's strict duplicate-key validation.
  try { JSON.parse(raw); } catch { throw new Error('JSON 格式无效，请检查引号、逗号与括号。'); }
  return raw;
}
function begin(kind) {
  if (!ready || closed || pending) return null;
  const active = {kind, controller: new AbortController(), revision: generation, requestId: crypto.randomUUID()};
  pending = active; refreshControls(); return active;
}
function current(active) { return pending === active && generation === active.revision; }
function finish(active) { if (pending === active) { pending = null; refreshControls(); } }
function showError(error, active) {
  if (current(active) && error.name !== 'AbortError') status(error instanceof TypeError ? '无法连接本机服务，请重新启动工作台。' : error.message, true);
}
function download(name, value, type) {
  const url = URL.createObjectURL(new Blob([value], {type}));
  const link = document.createElement('a'); link.href = url; link.download = name;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function saveProject(mode) {
  let raw;
  try { raw = rawProject(); } catch (error) { status(error.message, true); return; }
  const active = begin('save'); if (!active) return;
  status('正在校验并保存项目……');
  try {
    const data = await request('project', {method: 'POST', signal: active.controller.signal, body: '{"project":' + raw + '}'});
    if (!current(active)) return;
    project = clone(data.project); jsonDirty = false; dirty = false;
    projectWarnings([]);
    writeJson(); renderEditor();
    if (mode === 'download') download('资源配置项目.json', JSON.stringify(project, null, 2), 'application/json;charset=utf-8');
    status(mode === 'download' ? '项目已校验、保存并下载。刷新后会恢复该有效项目。' : '项目已校验并保存。刷新后恢复此项目；计算结果需重新生成。');
  } catch (error) { showError(error, active); }
  finally { finish(active); }
}
function showResult(value, input, warnings) {
  result = value; resultProject = clone(input);
  const hasSolution = ['optimal', 'feasible'].includes(value.status) && Array.isArray(value.jobs);
  const proved = value.status === 'optimal' && value.optimality_proven === true;
  const labels = {optimal: proved ? '已证明最优' : '可行方案 · 未证明最优', feasible: '可行方案 · 未证明最优', infeasible: '无可行解', limit: '已达运行限制', error: '求解未完成'};
  const tone = proved ? '' : ['optimal', 'feasible', 'limit'].includes(value.status) ? 'warning' : 'error';
  $('outcome').className = 'outcome ' + tone;
  $('result-badge').className = 'tag ' + tone;
  $('result-badge').textContent = labels[value.status] || '未知求解状态';
  $('result-message').textContent = value.message || '本次计算已返回。';
  $('proof-message').textContent = proved ? '在本次输入及约束下，求解器已证明不存在收益更高的可行组合。' : hasSolution ? '这是已找到的可行组合，仍可能存在更高收益。请保留“未证明最优”的状态说明。' : value.status === 'infeasible' ? '没有组合能同时满足资源容量与最低作业数量。请检查或放宽约束后重新计算。' : '本次没有可导出的有效方案。请查看状态说明，调整输入后重新计算。';
  const selected = hasSolution ? value.jobs.filter(job => job.selected) : [];
  $('objective').textContent = hasSolution ? format(value.objective) : '—';
  $('selected-count').textContent = hasSolution ? selected.length + ' / ' + value.jobs.length : '—';
  $('mip-gap').textContent = hasSolution && typeof value.mip_gap === 'number' && Number.isFinite(value.mip_gap) ? format(value.mip_gap * 100) + '%' : '—';
  $('solution-content').hidden = !hasSolution;
  $('usage').replaceChildren();
  if (hasSolution) {
    (value.usage || []).forEach(resource => {
      const card = document.createElement('div'); card.className = 'usage-card';
      const line = document.createElement('div'); line.className = 'usage-label';
      const name = document.createElement('strong'); name.textContent = resource.name;
      const numbers = document.createElement('span'); numbers.textContent = format(resource.used) + ' / ' + format(resource.capacity);
      line.append(name, numbers);
      const bar = document.createElement('progress'); bar.max = 1;
      bar.value = resource.capacity > 0 ? Math.min(1, Math.max(0, resource.used / resource.capacity)) : 0;
      bar.setAttribute('aria-label', resource.name + '：已用' + resource.used + '，容量' + resource.capacity);
      const remaining = document.createElement('p'); remaining.textContent = '剩余容量 ' + format(resource.capacity - resource.used) + (resource.capacity === 0 ? ' · 此资源容量为 0' : ' · 使用率 ' + format(resource.used / resource.capacity * 100) + '%');
      card.append(line, bar, remaining); $('usage').append(card);
    });
    $('selected-summary').textContent = selected.length ? '已选：' + selected.map(job => job.id).join('、') : '当前最优或可行方案未选择作业。';
    const head = $('result-head'); head.replaceChildren();
    ['状态', '编号', '作业', '收益', ...input.resources.map(resource => resource.name + '用量')].forEach(name => cell(head, name, 'th').scope = 'col');
    $('result-body').replaceChildren();
    value.jobs.forEach(job => {
      const row = document.createElement('tr'); row.classList.toggle('selected', !!job.selected);
      const badge = document.createElement('span'); badge.className = 'tag ' + (job.selected ? '' : 'neutral'); badge.textContent = job.selected ? '已选' : '未选'; cell(row, '').append(badge);
      cell(row, job.id); cell(row, job.name).className = 'job-name'; cell(row, format(job.value)).className = 'numeric';
      input.resources.forEach(resource => { cell(row, format(job.uses?.[resource.id] ?? 0)).className = 'numeric'; });
      $('result-body').append(row);
    });
  }
  $('warnings').replaceChildren();
  for (const warning of Array.isArray(warnings) ? warnings : []) { const item = document.createElement('li'); item.textContent = typeof warning === 'string' ? warning : '本次计算返回了额外提示，请检查输入。'; $('warnings').append(item); }
  $('warnings').hidden = !$('warnings').children.length;
  $('evidence-project').textContent = input.name;
  const engineVersion = String(value.engine_version || '版本未报告');
  $('evidence-engine').textContent = /^HiGHS\b/i.test(engineVersion) ? engineVersion : 'HiGHS ' + engineVersion;
  $('evidence-time').textContent = format(value.elapsed_seconds) + ' 秒';
  $('evidence-bound').textContent = format(value.dual_bound);
  $('evidence-hash').textContent = value.input_sha256 || '未报告';
  $('empty').hidden = true; $('result-content').hidden = false; refreshControls();
}
async function solve() {
  let raw;
  try { raw = rawProject(); } catch (error) { status(error.message, true); return; }
  invalidate();
  const active = begin('solve'); if (!active) return;
  status('HiGHS 正在本机搜索作业组合……可以取消本次计算。');
  try {
    const data = await request('solve', {method: 'POST', signal: active.controller.signal, body: '{"request_id":' + JSON.stringify(active.requestId) + ',"project":' + raw + '}'});
    if (!current(active)) return;
    project = clone(data.project); jsonDirty = false; dirty = false; projectWarnings([]); writeJson(); renderEditor();
    showResult(data.result, project, data.warnings);
    status(data.result.status === 'optimal' && data.result.optimality_proven ? '计算完成，已证明当前组合最优。项目已保存。' : data.result.status === 'feasible' ? '已找到可行组合，但未证明最优。项目已保存。' : '本次计算已返回，请查看方案状态与约束说明。');
  } catch (error) { showError(error, active); }
  finally { finish(active); }
}
function csvCell(value) {
  let text = String(value ?? '');
  if (/^[\s\uFEFF]*[=+\-@]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
  return '"' + text.replace(/"/g, '""') + '"';
}
function exportCsv() {
  if (!result || !resultProject || !['optimal', 'feasible'].includes(result.status)) return;
  const proved = result.status === 'optimal' && result.optimality_proven;
  const rows = [
    ['项目', resultProject.name], ['求解状态', proved ? '已证明最优' : '可行方案，未证明最优'],
    ['总收益', result.objective], ['引擎版本', result.engine_version], ['输入SHA-256', result.input_sha256], [],
    ['作业编号', '作业名称', '是否选择', '收益', ...resultProject.resources.map(resource => resource.name + '用量')]
  ];
  result.jobs.forEach(job => rows.push([job.id, job.name, job.selected ? '是' : '否', job.value, ...resultProject.resources.map(resource => job.uses?.[resource.id] ?? 0)]));
  rows.push([], ['资源编号', '资源名称', '已用', '容量', '剩余']);
  (result.usage || []).forEach(resource => rows.push([resource.resource_id, resource.name, resource.used, resource.capacity, resource.capacity - resource.used]));
  download('资源配置结果.csv', '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n'), 'text/csv;charset=utf-8');
  status('已导出当前方案 CSV，包含求解状态与输入哈希。');
}
async function load() {
  ready = false; $('reload').hidden = true; refreshControls();
  try {
    const data = await request('bootstrap');
    examples = data.examples || {};
    $('preset').replaceChildren();
    const custom = document.createElement('option'); custom.value = ''; custom.textContent = '当前项目'; $('preset').append(custom);
    Object.keys(examples).forEach(key => { const option = document.createElement('option'); option.value = key; option.textContent = key; $('preset').append(option); });
    $('app-name').textContent = data.name || '离线资源配置优化台';
    $('version').textContent = data.version || '1.0.0'; $('engine').textContent = data.engine || 'HiGHS 1.16.0';
    const warnings = Array.isArray(data.warnings) ? data.warnings.filter(warning => typeof warning === 'string') : [];
    ready = true; setProject(data.project, !warnings.length); projectWarnings(warnings);
    status(warnings.length ? '工作台返回了项目恢复提示。当前项目尚未保存，请查看提示并保存有效项目。' : '项目已载入。调整资源或作业后点击计算；刷新不会沿用旧结果。');
  } catch (error) { status(error.message || '无法连接工作台，请通过插件工具重新启动。', true); $('reload').hidden = false; }
  finally { refreshControls(); }
}
$('min-jobs').addEventListener('input', () => { project.min_jobs = $('min-jobs').value === '' ? null : Number($('min-jobs').value); writeJson(); edited(); });
$('project-json').addEventListener('input', () => { jsonDirty = true; edited(); status('JSON 已修改，旧结果已清除。请校验更新表格，或直接保存、计算。'); });
$('preset').addEventListener('change', () => {
  const key = $('preset').value; if (!key || !Object.hasOwn(examples, key)) return;
  if (dirty && !confirm('载入示例会替换当前未保存的修改。继续？')) { $('preset').value = ''; return; }
  setProject(examples[key]); status('示例已载入。可修改容量，再计算组合。保存前不会替换原已存项目。');
});
$('run').addEventListener('click', solve);
$('cancel').addEventListener('click', () => { cancelRequest(); clearResult(); refreshControls(); status('已请求取消，旧结果已清除。正在确认后台取消状态……'); });
$('save').addEventListener('click', () => saveProject('save'));
$('download').addEventListener('click', () => saveProject('download'));
$('validate').addEventListener('click', () => saveProject('validate'));
$('csv').addEventListener('click', exportCsv);
$('import').addEventListener('click', () => $('file').click());
$('file').addEventListener('change', async () => {
  const file = $('file').files[0]; if (!file) return;
  try {
    if (file.size > LIMIT) throw new Error('文件超过 256 KiB 上限。');
    const raw = new TextDecoder('utf-8', {fatal: true}).decode(await file.arrayBuffer());
    if (new TextEncoder().encode(raw).length > LIMIT) throw new Error('文件超过 256 KiB 上限。');
    try { JSON.parse(raw); } catch { throw new Error('文件不是有效 JSON，请检查格式。'); }
    if (dirty && !confirm('导入会替换当前未保存的修改。继续？')) return;
    $('project-json').value = raw; jsonDirty = true; edited(); $('json-details').open = true;
    status('JSON 已载入待校验区域。请校验、保存或计算；通过严格校验前不覆盖已存项目。');
  } catch (error) { status(error instanceof TypeError ? '导入失败：仅支持 UTF-8 JSON 文件。' : error.message, true); }
  finally { $('file').value = ''; }
});
$('reset').addEventListener('click', async () => {
  if (!confirm('恢复默认示例并清除本工作台已保存的项目与结果？已下载的文件会保留。')) return;
  invalidate(); const active = begin('reset'); if (!active) return;
  status('正在恢复默认示例……');
  try {
    let data = await request('reset', {method: 'POST', body: '{}', signal: active.controller.signal});
    if (!data.project) data = await request('bootstrap', {signal: active.controller.signal});
    if (!current(active)) return;
    pending = null; setProject(data.project, true); projectWarnings([]); $('preset').value = '';
    status('已恢复并保存默认示例。请重新计算。');
  } catch (error) { showError(error, active); }
  finally { finish(active); }
});
$('close').addEventListener('click', async () => {
  if (!confirm('关闭本插件的本机工作台？未保存修改会丢失，已保存项目与下载文件保留。')) return;
  invalidate(); const active = begin('close'); if (!active) return;
  try {
    await request('close', {method: 'POST', body: '{}', signal: active.controller.signal});
    if (!current(active)) return;
    closed = true; dirty = false; status('工作台已关闭。可通过插件工具重新启动。');
  } catch (error) { showError(error, active); }
  finally { finish(active); }
});
$('reload').addEventListener('click', load);
window.addEventListener('beforeunload', event => { if (dirty && !closed) { event.preventDefault(); event.returnValue = ''; } });
load();
