/* Original Chinese interface for the bounded offline CircuitJS RLC port. */
"use strict";

const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";
const TYPE_NAMES = { R: "电阻 R", C: "电容 C", L: "电感 L", V: "电压源 V" };
const UNITS = { R: "Ω", C: "F", L: "H", V: "V" };
const DEFAULT_VALUES = { R: 1000, C: 1e-6, L: 0.01, V: 5 };
const PRESETS = {
  rc: { components: [
    { id: "V1", type: "V", a: "1", b: "0", value: 5 },
    { id: "R1", type: "R", a: "1", b: "2", value: 1000 },
    { id: "C1", type: "C", a: "2", b: "0", value: 1e-6 }
  ], duration_ms: 5, step_us: 5, probe: "2" },
  divider: { components: [
    { id: "V1", type: "V", a: "1", b: "0", value: 5 },
    { id: "R1", type: "R", a: "1", b: "2", value: 1000 },
    { id: "R2", type: "R", a: "2", b: "0", value: 1000 }
  ], duration_ms: 1, step_us: 10, probe: "2" },
  rlc: { components: [
    { id: "V1", type: "V", a: "1", b: "0", value: 5 },
    { id: "R1", type: "R", a: "1", b: "2", value: 100 },
    { id: "L1", type: "L", a: "2", b: "3", value: 0.01 },
    { id: "C1", type: "C", a: "3", b: "0", value: 1e-6 }
  ], duration_ms: 5, step_us: 2, probe: "3" }
};
const copy = (value) => JSON.parse(JSON.stringify(value));
let circuit = copy(PRESETS.rc);
let result = null;
let resultCircuit = null;
let busy = false;

function tell(message, kind = "normal") {
  $("notice").textContent = message;
  $("notice").className = "notice" + (kind === "normal" ? "" : " " + kind);
}

function confirmChange(message) {
  const dialog = $("change-dialog");
  if (dialog.open) return Promise.resolve(false);
  $("change-message").textContent = message;
  dialog.returnValue = "cancel";
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "continue"), { once: true });
    dialog.showModal();
  });
}

function pretty(number, digits = 5) {
  if (!Number.isFinite(number)) return "—";
  if (number === 0) return "0";
  if (Math.abs(number) >= 1e5 || Math.abs(number) < 1e-4) return number.toExponential(3);
  return Number(number.toPrecision(digits)).toString();
}

function engineering(number, unit) {
  if (!Number.isFinite(number)) return "? " + unit;
  if (number === 0) return "0 " + unit;
  for (const [scale, prefix] of [[1e9, "G"], [1e6, "M"], [1e3, "k"], [1, ""], [1e-3, "m"], [1e-6, "µ"], [1e-9, "n"]]) {
    if (Math.abs(number) >= scale) return pretty(number / scale, 4) + " " + prefix + unit;
  }
  return pretty(number) + " " + unit;
}

function nodesOf(value) {
  return [...new Set(value.components.flatMap((component) => [component.a, component.b]))]
    .sort((a, b) => a === "0" ? -1 : b === "0" ? 1 : a.localeCompare(b, "zh-CN", { numeric: true }));
}

function svgElement(name, attributes = {}, text) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  if (text !== undefined) element.textContent = text;
  return element;
}

function drawSchematic() {
  const svg = $("schematic");
  svg.replaceChildren();
  const nodes = nodesOf(circuit);
  const width = Math.max(580, 120 + nodes.length * 112);
  const height = Math.max(230, 110 + circuit.components.length * 60);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.setAttribute("aria-label", `电路连接图，${circuit.components.length} 个元件、${nodes.length} 个节点；连接由端点圆点表示`);
  if (!nodes.length) {
    svg.append(svgElement("text", { x: width / 2, y: 100, fill: "#a7b9ad", "text-anchor": "middle", "font-size": 15 }, "添加元件，建立第一条连接"));
    return;
  }
  const xOf = (node) => 70 + nodes.indexOf(node) * ((width - 140) / Math.max(1, nodes.length - 1));
  for (const node of nodes) {
    const x = xOf(node);
    svg.append(svgElement("line", { x1: x, y1: 54, x2: x, y2: height - 27, stroke: "#40695b", "stroke-width": 1.4 }));
    svg.append(svgElement("text", { x, y: 33, fill: node === "0" ? "#a5b7ac" : "#d5ed9c", "text-anchor": "middle", "font-size": 13, "font-family": "monospace" }, node === "0" ? "0 · 地" : `节点 ${node}`));
    if (node === "0") {
      for (let i = 0; i < 3; i++) svg.append(svgElement("line", { x1: x - 10 + i * 3, x2: x + 10 - i * 3, y1: height - 24 + i * 5, y2: height - 24 + i * 5, stroke: "#a5b7ac", "stroke-width": 1.4 }));
    }
  }
  circuit.components.forEach((component, index) => {
    const xa = xOf(component.a), xb = xOf(component.b), y = 85 + index * 60;
    // Place the symbol between adjacent node rails, never over an unrelated rail.
    const mid = Math.min(xa, xb) + Math.min(Math.abs(xa - xb), (width - 140) / Math.max(1, nodes.length - 1)) / 2;
    const line = { stroke: "#d5ed9c", "stroke-width": 2, fill: "none" };
    if (xa === xb) {
      svg.append(svgElement("path", { d: `M ${xa} ${y} h 26 v 17 h -26`, stroke: "#edaa88", fill: "none", "stroke-width": 2 }));
      svg.append(svgElement("text", { x: xa + 32, y: y + 12, fill: "#edaa88", "font-size": 11 }, `${component.id}：两端相同`));
    } else {
      svg.append(svgElement("line", { x1: Math.min(xa, xb), y1: y, x2: mid - 26, y2: y, ...line }));
      svg.append(svgElement("line", { x1: mid + 26, y1: y, x2: Math.max(xa, xb), y2: y, ...line }));
      // The opaque patch makes bus crossings unambiguous beneath the component.
      svg.append(svgElement("rect", { x: mid - 27, y: y - 15, width: 54, height: 30, fill: "#102d28" }));
      if (component.type === "R") {
        svg.append(svgElement("path", { d: `M ${mid - 26} ${y} h 6 l 5 -8 l 7 16 l 7 -16 l 7 16 l 5 -8 h 15`, ...line }));
      } else if (component.type === "C") {
        svg.append(svgElement("path", { d: `M ${mid - 26} ${y} H ${mid - 5} M ${mid - 5} ${y - 12} V ${y + 12} M ${mid + 5} ${y - 12} V ${y + 12} M ${mid + 5} ${y} H ${mid + 26}`, ...line }));
      } else if (component.type === "L") {
        svg.append(svgElement("path", { d: `M ${mid - 26} ${y} h 6 a 5 8 0 0 1 10 0 a 5 8 0 0 1 10 0 a 5 8 0 0 1 10 0 a 5 8 0 0 1 10 0 h 6`, ...line }));
      } else {
        svg.append(svgElement("circle", { cx: mid, cy: y, r: 15, ...line }));
        svg.append(svgElement("path", { d: `M ${mid - 26} ${y} h 11 M ${mid + 15} ${y} h 11`, ...line }));
        svg.append(svgElement("text", { x: mid - 6, y: y + 4, fill: "#d5ed9c", "text-anchor": "middle", "font-size": 11 }, xa < xb ? "+" : "−"));
        svg.append(svgElement("text", { x: mid + 6, y: y + 4, fill: "#d5ed9c", "text-anchor": "middle", "font-size": 11 }, xa < xb ? "−" : "+"));
      }
      svg.append(svgElement("text", { x: mid, y: y + 30, fill: "#c3d2c8", "text-anchor": "middle", "font-size": 11 }, `${component.id} · ${engineering(component.value, UNITS[component.type])}`));
    }
    for (const x of new Set([xa, xb])) svg.append(svgElement("circle", { cx: x, cy: y, r: 4, fill: "#d5ed9c" }));
  });
}

function refreshProbeOptions() {
  const nodes = nodesOf(circuit);
  if (!nodes.includes(circuit.probe)) nodes.push(circuit.probe);
  $("probe").replaceChildren(...nodes.map((node) => {
    const option = document.createElement("option");
    option.value = node;
    option.textContent = `节点 ${node}` + (!nodesOf(circuit).includes(node) ? "（未连接）" : node === "0" ? "（地）" : "");
    return option;
  }));
  $("probe").value = circuit.probe;
}

function renderEditor() {
  const body = $("component-rows");
  body.replaceChildren();
  circuit.components.forEach((component, index) => {
    const row = document.createElement("tr");
    row.dataset.index = index;
    for (const key of ["id", "type", "a", "b", "value"]) {
      const cell = document.createElement("td");
      const input = document.createElement(key === "type" ? "select" : "input");
      if (key === "type") {
        for (const [value, label] of Object.entries(TYPE_NAMES)) {
          const option = document.createElement("option"); option.value = value; option.textContent = label; input.append(option);
        }
      } else if (key === "value") {
        input.type = "number"; input.step = "any"; input.inputMode = "decimal";
      } else {
        input.type = "text"; input.maxLength = 24; input.spellcheck = false;
      }
      input.value = component[key]; input.dataset.field = key;
      input.setAttribute("aria-label", `${component.id || index + 1} ${ {id:"名称",type:"元件类型",a:"从节点",b:"到节点",value:"数值"}[key] }`);
      cell.append(input); row.append(cell);
    }
    const cell = document.createElement("td");
    const remove = document.createElement("button"); remove.type = "button"; remove.className = "remove"; remove.textContent = "×";
    remove.setAttribute("aria-label", `删除 ${component.id}`); remove.dataset.remove = index; cell.append(remove); row.append(cell); body.append(row);
  });
  $("component-count").textContent = `${circuit.components.length} 个元件`;
  $("duration").value = circuit.duration_ms; $("step").value = circuit.step_us;
  refreshProbeOptions(); drawSchematic(); refreshButtons();
}

function invalidate(message = "已修改电路，请重新运行以获得当前参数的结果。") {
  result = null; resultCircuit = null;
  $("waveform").replaceChildren(); $("empty-result").hidden = false;
  $("waveform").setAttribute("aria-label", "尚无当前仿真电压波形，请运行仿真");
  for (const id of ["last-voltage", "voltage-range", "sample-count", "last-time", "sample-time"]) $(id).textContent = "—";
  $("sample-slider").disabled = true; $("sample-slider").max = "0"; $("sample-slider").value = "0";
  $("result-version").textContent = "尚无当前结果"; $("run-state").textContent = "等待运行";
  $("warnings").hidden = true; $("warnings").replaceChildren();
  $("voltage-readout").replaceChildren(); $("current-readout").replaceChildren();
  $("wave-title").textContent = "节点电压";
  $("result-note").textContent = "修改任何电路参数后需重新运行。图形是连接关系与计算结果，不是硬件测量。";
  tell(message, "neutral"); refreshButtons();
}

function refreshButtons() {
  document.querySelectorAll("button").forEach((button) => button.disabled = busy);
  $("editor-fields").disabled = busy;
  $("export-csv-btn").disabled = busy || !result;
  $("add-btn").disabled = busy || circuit.components.length >= 24;
}

function setBusy(value) {
  busy = value; refreshButtons();
  $("run-btn").firstChild.textContent = value ? "正在求解… " : "运行仿真 ";
}

async function api(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  let response;
  try { response = await fetch(new URL(`api/${path}`, document.baseURI), {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? { Accept: "application/json" } : { Accept: "application/json", "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin", cache: "no-store", redirect: "error", signal: controller.signal
  }); } catch (error) {
    throw new Error(error.name === "AbortError" ? "本机服务响应超时，请检查服务状态。没有自动重试。" : "无法连接本机服务，请检查服务是否仍在运行。没有自动重试。");
  } finally { clearTimeout(timeout); }
  const data = await response.json().catch(() => { throw new Error("本机服务返回了无法读取的响应，请检查服务是否仍在运行。"); });
  if (!response.ok || data.ok === false) throw new Error(data.error?.message || data.message || "本机服务拒绝了此次操作。");
  return data;
}

function validateClient(value) {
  if (!value || Array.isArray(value) || typeof value !== "object") throw new Error("电路文件必须是一个 JSON 对象。");
  const allowed = ["components", "duration_ms", "step_us", "probe"];
  if (Object.keys(value).some((key) => !allowed.includes(key))) throw new Error("电路包含不支持的字段；本版仅接受元件、仿真时长、步长和观察节点。");
  if (!Array.isArray(value.components) || !value.components.length || value.components.length > 24) throw new Error("电路需要 1–24 个受支持元件。");
  for (const item of value.components) {
    if (!item || Array.isArray(item) || typeof item !== "object" || Object.keys(item).some((key) => !["id", "type", "a", "b", "value"].includes(key))) throw new Error("元件结构或字段不受支持。");
    if (!Object.hasOwn(TYPE_NAMES, item.type)) throw new Error("本版只支持 R、L、C、V 元件。");
    if (!["id", "a", "b"].every((key) => typeof item[key] === "string" && item[key].length > 0 && item[key].length <= 24)) throw new Error("元件名称和节点必须为 1–24 个字符的文本。");
    if (typeof item.value !== "number" || !Number.isFinite(item.value)) throw new Error("请为每个元件填写有限的数值。");
  }
  if (typeof value.probe !== "string" || !value.probe || value.probe.length > 24) throw new Error("观察节点必须是有效的节点名称。");
  if (![value.duration_ms, value.step_us].every((number) => typeof number === "number" && Number.isFinite(number) && number > 0)) throw new Error("仿真时长和时间步长必须是正数。");
  if (nodesOf(value).length > 16) throw new Error("最多支持 16 个节点（包含接地 0）。");
  const steps = value.duration_ms * 1000 / value.step_us;
  if (steps < 1 || steps > 5000 || Math.abs(steps - Math.round(steps)) > 1e-9 * Math.max(1, steps)) throw new Error("仿真时长必须是时间步长的整数倍，且共 1–5000 步。");
  return copy(value);
}

function showReadout(index) {
  if (!result) return;
  const sample = result.samples[Math.max(0, Math.min(index, result.samples.length - 1))];
  $("sample-time").textContent = `${pretty(sample.t * 1000)} ms`;
  for (const [container, values] of [["voltage-readout", sample.voltages], ["current-readout", sample.currents]]) {
    const target = $(container); target.replaceChildren();
    Object.entries(values || {}).forEach(([name, value]) => {
      const dt = document.createElement("dt"); dt.textContent = container === "voltage-readout" ? `节点 ${name}` : name;
      const dd = document.createElement("dd"); dd.textContent = pretty(value, 6); target.append(dt, dd);
    });
  }
  drawWaveform(index);
}

function drawWaveform(index = 0) {
  const svg = $("waveform"); svg.replaceChildren();
  if (!result) return;
  const samples = result.samples, probe = resultCircuit.probe;
  const numbers = samples.map((sample) => sample.voltages[probe]);
  let low = Math.min(0, ...numbers), high = Math.max(0, ...numbers);
  const padding = Math.max((high - low) * 0.1, 0.05);
  low -= padding; high += padding;
  const end = Math.max(samples[samples.length - 1].t, 1e-12);
  const plot = { x: 61, y: 25, width: 512, height: 228 };
  const x = (time) => plot.x + time / end * plot.width;
  const y = (value) => plot.y + (high - value) / (high - low) * plot.height;
  for (let i = 0; i <= 4; i++) {
    const value = low + (high - low) * i / 4, time = end * i / 4;
    svg.append(svgElement("line", { x1: plot.x, y1: y(value), x2: plot.x + plot.width, y2: y(value), stroke: "#e0e5d7", "stroke-width": 1 }));
    svg.append(svgElement("text", { x: plot.x - 10, y: y(value) + 4, fill: "#74816b", "font-size": 11, "text-anchor": "end", "font-family": "monospace" }, pretty(value, 3)));
    svg.append(svgElement("line", { x1: x(time), y1: plot.y, x2: x(time), y2: plot.y + plot.height, stroke: "#e0e5d7", "stroke-width": 1 }));
    svg.append(svgElement("text", { x: x(time), y: plot.y + plot.height + 22, fill: "#74816b", "font-size": 11, "text-anchor": "middle", "font-family": "monospace" }, pretty(time * 1000, 3)));
  }
  const path = samples.map((sample, i) => `${i ? "L" : "M"}${x(sample.t).toFixed(2)},${y(sample.voltages[probe]).toFixed(2)}`).join(" ");
  svg.append(svgElement("path", { d: path, fill: "none", stroke: "#246647", "stroke-width": 2.4, "stroke-linejoin": "round" }));
  const sample = samples[Math.max(0, Math.min(index, samples.length - 1))];
  svg.append(svgElement("line", { x1: x(sample.t), y1: plot.y, x2: x(sample.t), y2: plot.y + plot.height, stroke: "#b39456", "stroke-dasharray": "4 4" }));
  svg.append(svgElement("circle", { cx: x(sample.t), cy: y(sample.voltages[probe]), r: 4.5, fill: "#246647", stroke: "#fffef8", "stroke-width": 2 }));
  svg.setAttribute("aria-label", `节点 ${probe} 电压波形，共 ${samples.length} 个真实采样点，结束时间 ${pretty(end * 1000)} 毫秒`);
}

function acceptResult(data, usedCircuit) {
  if (!Array.isArray(data.samples) || !data.samples.length || data.samples.some((sample) => !Number.isFinite(sample.t) || !sample.voltages || !Number.isFinite(sample.voltages[usedCircuit.probe]))) throw new Error("求解响应缺少有效采样数据，未绘制波形。");
  result = data; resultCircuit = usedCircuit;
  const samples = result.samples, last = samples[samples.length - 1];
  const values = samples.map((sample) => sample.voltages[usedCircuit.probe]);
  $("empty-result").hidden = true;
  $("wave-title").textContent = `节点 ${usedCircuit.probe} 电压`;
  $("last-voltage").textContent = `${pretty(last.voltages[usedCircuit.probe])} V`;
  $("voltage-range").textContent = `${pretty(Math.min(...values), 4)} – ${pretty(Math.max(...values), 4)}`;
  $("sample-count").textContent = String(samples.length);
  $("last-time").textContent = `${pretty(last.t * 1000)} ms`;
  $("result-version").textContent = data.version ? `v${data.version}` : "未返回版本";
  $("sample-slider").disabled = false; $("sample-slider").max = String(samples.length - 1); $("sample-slider").value = String(samples.length - 1);
  $("warnings").replaceChildren();
  const warnings = Array.isArray(data.warnings) ? data.warnings : [];
  warnings.forEach((warning) => { const p = document.createElement("div"); p.textContent = String(warning); $("warnings").append(p); });
  $("warnings").hidden = warnings.length === 0;
  $("run-state").textContent = "本次求解完成";
  $("result-note").textContent = "读数来自本次实际求解。电流的正方向为元件的“从节点 → 到节点”；负值表示方向相反。修改参数会清除旧结果。";
  showReadout(samples.length - 1); refreshButtons();
}

async function run() {
  if (busy) return;
  invalidate("正在求解当前电路……"); setBusy(true);
  try {
    const usedCircuit = validateClient(circuit);
    const data = await api("simulate", { circuit: usedCircuit });
    acceptResult(data, usedCircuit);
    tell(`求解成功：${data.samples.length} 个采样点。拖动采样滑块查看逐点电压与电流；修改参数后重新运行进行对比。`);
  } catch (error) {
    tell(error.message || "求解失败，请检查电路参数。", "error"); $("run-state").textContent = "求解未完成";
  } finally { setBusy(false); }
}

async function load(initial = false) {
  if (busy) return;
  if (!initial && !await confirmChange("读取已保存电路会替换当前编辑内容，是否继续？")) return;
  setBusy(true);
  try {
    const data = await api("load");
    if (data.circuit) {
      circuit = validateClient(data.circuit); renderEditor(); invalidate("已从本机工作区读取电路。请运行仿真以获得新的数值结果。");
    } else tell("尚未保存电路。已准备 RC 充电示例；可编辑参数后运行。", "neutral");
  } catch (error) { tell(error.message || "读取失败。", "error"); }
  finally { setBusy(false); }
}

async function save() {
  if (busy) return;
  if (!await confirmChange("保存会更新本次工作区中已保存的电路状态，不修改导入原文件。是否继续？")) return;
  setBusy(true);
  try {
    await api("save", { circuit: validateClient(circuit) });
    tell("电路已保存到本机工作区。刷新页面或点击“读取已保存”可恢复；数值结果需重新运行。");
  } catch (error) { tell(error.message || "保存失败。", "error"); }
  finally { setBusy(false); }
}

function download(filename, content, mime) {
  const url = URL.createObjectURL(new Blob([content], { type: mime }));
  const link = document.createElement("a"); link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

function csvCell(value) { return '"' + String(value).replaceAll('"', '""') + '"'; }

$("component-rows").addEventListener("input", (event) => {
  const input = event.target;
  const row = input.closest("tr[data-index]");
  if (!row || !input.dataset.field || busy) return;
  const component = circuit.components[Number(row.dataset.index)];
  component[input.dataset.field] = input.dataset.field === "value" ? input.value === "" ? NaN : Number(input.value) : input.value;
  refreshProbeOptions(); drawSchematic(); invalidate();
});
$("component-rows").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-remove]"); if (!button || busy) return;
  circuit.components.splice(Number(button.dataset.remove), 1); renderEditor(); invalidate();
});
$("add-btn").addEventListener("click", () => {
  if (busy || circuit.components.length >= 24) return;
  const type = $("new-type").value; let index = 1;
  while (circuit.components.some((component) => component.id === type + index)) index++;
  circuit.components.push({ id: type + index, type, a: "1", b: "0", value: DEFAULT_VALUES[type] }); renderEditor(); invalidate();
});
for (const [id, key] of [["probe", "probe"], ["duration", "duration_ms"], ["step", "step_us"]]) {
  $(id).addEventListener("input", () => { circuit[key] = id === "probe" ? $(id).value : $(id).value === "" ? NaN : Number($(id).value); invalidate(); });
}
document.querySelectorAll("[data-preset]").forEach((button) => button.addEventListener("click", async () => {
  if (busy || !await confirmChange("载入示例会替换当前编辑内容，是否继续？")) return;
  circuit = copy(PRESETS[button.dataset.preset]); renderEditor(); invalidate("已载入示例。点击“运行仿真”查看真实数值结果。");
}));
$("run-btn").addEventListener("click", run);
$("load-btn").addEventListener("click", () => load(false));
$("save-btn").addEventListener("click", save);
$("sample-slider").addEventListener("input", () => showReadout(Number($("sample-slider").value)));
$("export-json-btn").addEventListener("click", () => {
  try { download("离线电路实验室-电路.json", JSON.stringify(validateClient(circuit), null, 2) + "\n", "application/json;charset=utf-8"); tell("电路 JSON 已交给浏览器下载；请检查浏览器实际保存位置。"); }
  catch (error) { tell(error.message, "error"); }
});
$("export-csv-btn").addEventListener("click", () => {
  if (!result) return;
  const nodes = Object.keys(result.samples[0].voltages), components = Object.keys(result.samples[0].currents);
  const header = ["时间(s)", ...nodes.map((node) => `节点${node}电压(V)`), ...components.map((id) => `${id}电流(A)`)].map(csvCell).join(",");
  const rows = result.samples.map((sample) => [sample.t, ...nodes.map((node) => sample.voltages[node]), ...components.map((id) => sample.currents[id])].join(","));
  download("离线电路实验室-数值采样.csv", "\ufeff" + [header, ...rows].join("\r\n") + "\r\n", "text/csv;charset=utf-8");
  tell("本次全部采样值已交给浏览器下载。CSV 是数值求解结果，不是硬件测量。");
});
$("import-btn").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", async () => {
  const file = $("file-input").files[0]; $("file-input").value = "";
  if (!file || busy) return;
  try {
    if (file.size > 256 * 1024) throw new Error("电路 JSON 文件不能超过 256 KiB。");
    let text;
    try { text = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer()); }
    catch { throw new Error("电路文件必须是有效的 UTF-8 文本。"); }
    let parsed;
    try { parsed = JSON.parse(text); } catch { throw new Error("文件不是有效的 UTF-8 JSON 电路。"); }
    const next = validateClient(parsed);
    if (!await confirmChange("导入将替换当前编辑内容，不会修改原文件。是否继续？")) return;
    circuit = next; renderEditor(); invalidate("已导入电路结构；尚未通过求解校验，请点击“运行仿真”。");
  } catch (error) { tell(error.message || "导入失败。", "error"); }
});

renderEditor();
load(true);
