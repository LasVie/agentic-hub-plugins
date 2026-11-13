import { numberText, utcText, groundTrackSvg, elevationSvg, exportSvg, exportCsv } from './presentation.js';

const VERSION = '1.0.0';
const ENGINE_VERSION = '7.2.0';
const TIMEOUT_MS = 12000;
const PAGE_SIZE = 30;
const exampleElements = 'VANGUARD 1（历史核验示例）\n1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753\n2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667';
const fields = ['format', 'elements', 'start', 'duration', 'step', 'latitude', 'longitude', 'height', 'threshold'];
const nodes = Object.fromEntries([...fields, 'orbit-form', 'run', 'cancel', 'message', 'state', 'ground', 'elevation', 'sample-controls', 'sample-index', 'sample-label', 'azimuth', 'sample-elevation', 'range', 'altitude', 'sample-count', 'interval-count', 'epoch', 'warnings', 'intervals', 'samples', 'page', 'previous', 'next', 'satellite-name', 'window-label', 'export-json', 'export-csv', 'export-svg', 'file', 'example', 'omm-example', 'restore'].map(id => [id, document.getElementById(id)]));
let currentResult = null;
let worker = null;
let timer = null;
let generation = 0;
let requestId = 0;
let selectedIndex = 0;
let pageIndex = 0;
let originalInput = { format: 'tle', elements: exampleElements };
let originalRawInput = null;

function setMessage(text, type = '') {
  nodes.message.textContent = text;
  nodes.message.className = `message ${type}`.trim();
}

function setState(text, type = '') {
  nodes.state.textContent = text;
  nodes.state.className = `state ${type}`.trim();
}

function stopWorker() {
  if (timer !== null) clearTimeout(timer);
  timer = null;
  if (worker) worker.terminate();
  worker = null;
  nodes.run.disabled = false;
  nodes.cancel.disabled = true;
  nodes['orbit-form'].removeAttribute('aria-busy');
}

function empty(container, title, description) {
  const box = document.createElement('div'); box.className = 'empty compact';
  const heading = document.createElement('strong'); heading.textContent = title;
  const detail = document.createElement('span'); detail.textContent = description;
  box.append(heading, detail); container.replaceChildren(box);
}

function emptyRow(container, span, text) {
  const row = document.createElement('tr');
  const cell = document.createElement('td'); cell.colSpan = span; cell.className = 'table-empty'; cell.textContent = text;
  row.append(cell); container.replaceChildren(row);
}

function clearResult() {
  currentResult = null;
  selectedIndex = 0;
  pageIndex = 0;
  for (const id of ['export-json', 'export-csv', 'export-svg', 'previous', 'next']) nodes[id].disabled = true;
  nodes['sample-controls'].hidden = true;
  for (const id of ['sample-count', 'interval-count', 'epoch', 'satellite-name', 'azimuth', 'sample-elevation', 'range', 'altitude']) nodes[id].textContent = '—';
  nodes['window-label'].textContent = '等待计算'; nodes.page.textContent = '0 / 0';
  nodes.warnings.replaceChildren();
  empty(nodes.ground, '尚未生成有效轨道', '调整输入后，请重新计算。旧结果不可导出。');
  empty(nodes.elevation, '等待轨道计算', '横轴为 UTC 时间；仰角从本地地平线起算。');
  emptyRow(nodes.intervals, 4, '等待计算几何区间');
  emptyRow(nodes.samples, 7, '暂无有效数据');
}

function invalidate(message = '输入已变更。旧结果与导出已失效，请重新计算。') {
  generation += 1;
  stopWorker();
  clearResult();
  setState('需要重新计算');
  setMessage(message, 'stale');
}

function rawInput() {
  return fields.map(id => nodes[id].value);
}

function readInput() {
  const labels = { elements: '轨道根数', start: '开始时刻', duration: '窗口长度', step: '采样间隔', latitude: '纬度', longitude: '经度', height: '观测点椭球高', threshold: '最低仰角' };
  for (const [id, label] of Object.entries(labels)) {
    if (!nodes[id].value.trim()) {
      const error = new Error(`请填写${label}。（input_required）`); error.code = 'input_required'; nodes[id].focus(); throw error;
    }
  }
  if (new TextEncoder().encode(nodes.elements.value).length > 16384) {
    const error = new Error('轨道根数超过 16 KiB 限制。（input_too_large）'); error.code = 'input_too_large'; throw error;
  }
  return {
    format: nodes.format.value,
    elements: nodes.elements.value,
    startUtc: nodes.start.value.trim(),
    durationHours: Number(nodes.duration.value),
    stepSeconds: Number(nodes.step.value),
    observer: { latitudeDeg: Number(nodes.latitude.value), longitudeDeg: Number(nodes.longitude.value), heightM: Number(nodes.height.value) },
    minimumElevationDeg: Number(nodes.threshold.value),
  };
}

function tableRow(values, className) {
  const row = document.createElement('tr');
  if (className) row.className = className;
  values.forEach(value => { const cell = document.createElement('td'); cell.textContent = String(value); row.append(cell); });
  return row;
}

function renderSampleTable() {
  if (!currentResult) return;
  const result = currentResult;
  const totalPages = Math.ceil(result.samples.length / PAGE_SIZE);
  pageIndex = Math.max(0, Math.min(pageIndex, totalPages - 1));
  nodes.page.textContent = `${pageIndex + 1} / ${totalPages}`;
  nodes.previous.disabled = pageIndex === 0;
  nodes.next.disabled = pageIndex >= totalPages - 1;
  const first = pageIndex * PAGE_SIZE;
  nodes.samples.replaceChildren(...result.samples.slice(first, first + PAGE_SIZE).map((sample, offset) => tableRow([utcText(sample.utc), numberText(sample.latitudeDeg, 5), numberText(sample.longitudeDeg, 5), numberText(sample.heightKm), numberText(sample.azimuthDeg), numberText(sample.elevationDeg), numberText(sample.rangeKm)], first + offset === selectedIndex ? 'selected-row' : '')));
}

function renderSelectedSample() {
  if (!currentResult) return;
  selectedIndex = Math.max(0, Math.min(selectedIndex, currentResult.samples.length - 1));
  const sample = currentResult.samples[selectedIndex];
  nodes['sample-label'].textContent = `${selectedIndex + 1} / ${currentResult.samples.length} · ${utcText(sample.utc)}`;
  nodes.azimuth.textContent = numberText(sample.azimuthDeg);
  nodes['sample-elevation'].textContent = numberText(sample.elevationDeg);
  nodes.range.textContent = numberText(sample.rangeKm);
  nodes.altitude.textContent = numberText(sample.heightKm);
  nodes.ground.replaceChildren(groundTrackSvg(currentResult, selectedIndex));
  nodes.elevation.replaceChildren(elevationSvg(currentResult, selectedIndex));
  renderSampleTable();
}

function renderResult(result) {
  currentResult = result;
  selectedIndex = 0; pageIndex = 0;
  nodes['sample-index'].max = String(result.samples.length - 1); nodes['sample-index'].value = '0';
  nodes['sample-controls'].hidden = false;
  nodes['sample-count'].textContent = result.samples.length.toLocaleString('zh-CN');
  nodes['interval-count'].textContent = String(result.intervals.length);
  nodes.epoch.textContent = utcText(result.element.epochUtc);
  nodes['satellite-name'].textContent = `${result.element.name || '未命名卫星'} · ${result.element.catalogId}`;
  nodes['window-label'].textContent = `${result.input.durationHours} 小时 · 每 ${result.input.stepSeconds} 秒采样`;
  if (result.warnings?.length) {
    const list = document.createElement('ul');
    result.warnings.forEach(text => { const item = document.createElement('li'); item.textContent = text; list.append(item); });
    nodes.warnings.replaceChildren(list);
  }
  if (result.intervals.length) {
    nodes.intervals.replaceChildren(...result.intervals.map(interval => tableRow([utcText(interval.startUtc), utcText(interval.endUtc), numberText(interval.peakElevationDeg), interval.startClipped || interval.endClipped ? `${interval.startClipped ? '起点已截断' : ''}${interval.startClipped && interval.endClipped ? '；' : ''}${interval.endClipped ? '终点已截断' : ''}` : '区间未被窗口截断'])));
  } else emptyRow(nodes.intervals, 4, `本次采样未发现达到 ${result.minimumElevationDeg}° 的几何区间；不代表其他时间不存在过境。`);
  renderSelectedSample();
  for (const id of ['export-json', 'export-csv', 'export-svg']) nodes[id].disabled = false;
  setState('计算完成', 'ready');
  setMessage(`已完成 ${result.samples.length.toLocaleString('zh-CN')} 个采样点。结果与当前输入一致，可以检查和导出。`);
}

function runAnalysis(event) {
  event?.preventDefault();
  invalidate('正在校验输入并计算轨道……');
  let input;
  try { input = readInput(); }
  catch (error) { setState('输入未通过'); setMessage(error.message, 'error'); return; }
  const thisGeneration = generation;
  const thisRequest = ++requestId;
  const thisRawInput = JSON.stringify(rawInput());
  originalRawInput = thisRawInput;
  setState('计算中', 'busy'); setMessage('正在本机独立计算线程中传播轨道……', 'pending');
  nodes.run.disabled = true; nodes.cancel.disabled = false; nodes['orbit-form'].setAttribute('aria-busy', 'true');
  try {
    worker = new Worker('./worker.js', { type: 'module' });
    worker.onmessage = ({ data }) => {
      if (generation !== thisGeneration || data?.id !== thisRequest || JSON.stringify(rawInput()) !== thisRawInput) return;
      stopWorker();
      if (data.error) {
        setState('计算未完成'); setMessage(`${data.error.message || '轨道计算失败。'}${data.error.code ? `（${data.error.code}）` : ''}`, 'error'); return;
      }
      const result = data.result;
      if (result?.version !== VERSION || result?.engineVersion !== ENGINE_VERSION || !Array.isArray(result.samples) || !result.samples.length) {
        setState('结果不可用'); setMessage('计算线程未返回本版本的完整结果。（invalid_engine_result）', 'error'); return;
      }
      try { renderResult(result); }
      catch { clearResult(); setState('结果不可用'); setMessage('结果显示失败，未启用导出。请重新计算。（render_failed）', 'error'); }
    };
    worker.onerror = event => {
      event.preventDefault();
      if (generation !== thisGeneration) return;
      stopWorker(); clearResult(); setState('引擎不可用');
      setMessage('本地轨道引擎未能载入或计算线程发生错误。请确认完整安装包已启用，并重新打开工具实际返回的地址。（worker_failed）', 'error');
    };
    timer = setTimeout(() => {
      if (generation !== thisGeneration) return;
      stopWorker(); clearResult(); setState('计算已超时'); setMessage('计算超过 12 秒，线程已停止，未保留可导出的结果。请缩短窗口或增大采样间隔后重试。（calculation_timeout）', 'error');
    }, TIMEOUT_MS);
    worker.postMessage({ id: thisRequest, input });
  } catch {
    stopWorker(); clearResult(); setState('计算未启动'); setMessage('无法启动本地计算线程。请使用工具返回的本机地址与支持模块线程的浏览器。（worker_unavailable）', 'error');
  }
}

function download(text, mime, extension) {
  if (!currentResult || originalRawInput !== JSON.stringify(rawInput())) {
    invalidate('当前输入没有对应的有效结果，请重新计算后导出。'); return;
  }
  let url;
  try {
    url = URL.createObjectURL(new Blob([text], { type: mime }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `卫星轨道-${currentResult.element.catalogId}-${currentResult.version}.${extension}`.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_');
    document.body.append(link); link.click(); link.remove();
    const blobUrl = url;
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
  } catch {
    if (url) URL.revokeObjectURL(url);
    setMessage('浏览器未能发起下载，请检查下载权限后重试。（download_failed）', 'error');
  }
}

function loadExample() {
  invalidate('已载入 2000 年的公开历史核验示例。请运行计算；该根数不代表当前轨道。');
  nodes.format.value = 'tle'; nodes.elements.value = exampleElements; nodes.start.value = '2000-06-27T18:50:19.733568Z';
  nodes.duration.value = '24'; nodes.step.value = '60'; nodes.latitude.value = '1.3521'; nodes.longitude.value = '103.8198'; nodes.height.value = '0'; nodes.threshold.value = '10';
  originalInput = { format: 'tle', elements: exampleElements };
}

function loadOmmExample() {
  loadExample();
  const elements = JSON.stringify({ OBJECT_NAME: '先锋一号（历史核验）', OBJECT_ID: '1958-002B', EPOCH: '2000-06-27T18:50:19.733568Z', NORAD_CAT_ID: 5, MEAN_MOTION: 10.82419157, ECCENTRICITY: 0.1859667, INCLINATION: 34.2682, RA_OF_ASC_NODE: 348.7242, ARG_OF_PERICENTER: 331.7664, MEAN_ANOMALY: 19.3264, BSTAR: 0.000028098, MEAN_MOTION_DOT: 0.00000023, MEAN_MOTION_DDOT: 0, CENTER_NAME: 'EARTH', REF_FRAME: 'TEME', TIME_SYSTEM: 'UTC', MEAN_ELEMENT_THEORY: 'SGP4', EPHEMERIS_TYPE: 0, CLASSIFICATION_TYPE: 'U', ELEMENT_SET_NO: 475, REV_AT_EPOCH: 41366 }, null, 2);
  nodes.format.value = 'omm'; nodes.elements.value = elements;
  originalInput = { format: 'omm', elements };
  setMessage('已载入同一历史卫星的 OMM 示例。请运行计算并核对结果；该根数不代表当前轨道。', 'stale');
}

for (const id of fields) {
  nodes[id].addEventListener('input', () => invalidate());
  nodes[id].addEventListener('change', () => invalidate());
}
nodes['orbit-form'].addEventListener('submit', runAnalysis);
nodes.cancel.addEventListener('click', () => { invalidate('计算已取消，旧结果与导出已清除。'); setState('计算已取消'); });
nodes.example.addEventListener('click', loadExample);
nodes['omm-example'].addEventListener('click', loadOmmExample);
nodes.restore.addEventListener('click', () => { invalidate('已恢复最近导入的根数原文；其他设置保留，请重新计算。'); nodes.elements.value = originalInput.elements; nodes.format.value = originalInput.format; });
nodes.file.addEventListener('change', async () => {
  invalidate('正在读取根数文件……');
  const myGeneration = generation;
  const file = nodes.file.files?.[0];
  nodes.file.value = '';
  if (!file) { setMessage('未选择文件。旧结果与导出已失效。', 'stale'); return; }
  if (file.size > 16384) { setMessage('文件超过 16 KiB 限制，未导入。（input_too_large）', 'error'); return; }
  try {
    const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer());
    if (generation !== myGeneration) return;
    const format = text.trimStart().startsWith('{') ? 'omm' : 'tle';
    nodes.elements.value = text; nodes.format.value = format;
    originalInput = { elements: text, format };
    setMessage('文件原文已导入。请核对根数格式、历元附近的 UTC 时间及观测点，再运行计算。', 'stale');
  } catch { if (generation === myGeneration) setMessage('文件不是有效的 UTF-8 文本或读取失败，未生成结果。（file_read_failed）', 'error'); }
});
nodes['sample-index'].addEventListener('input', () => { selectedIndex = Number(nodes['sample-index'].value); pageIndex = Math.floor(selectedIndex / PAGE_SIZE); renderSelectedSample(); });
nodes.previous.addEventListener('click', () => { pageIndex -= 1; renderSampleTable(); });
nodes.next.addEventListener('click', () => { pageIndex += 1; renderSampleTable(); });
nodes['export-json'].addEventListener('click', () => { if (currentResult) download(JSON.stringify(currentResult, null, 2), 'application/json;charset=utf-8', 'json'); });
nodes['export-csv'].addEventListener('click', () => { if (currentResult) download(exportCsv(currentResult), 'text/csv;charset=utf-8', 'csv'); });
nodes['export-svg'].addEventListener('click', () => { if (currentResult) download(exportSvg(currentResult, selectedIndex), 'image/svg+xml;charset=utf-8', 'svg'); });
loadExample();
