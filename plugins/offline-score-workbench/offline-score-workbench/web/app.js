import {MAX_BYTES, safeScoreSvg, validateScore} from "./score-data.js";

const elements = Object.fromEntries(["file", "example", "restore", "source", "run", "cancel",
  "status", "previous", "next", "page-number", "svg", "midi", "score", "empty", "note"]
  .map(id => [id, document.getElementById(id)]));
const noteHint = "选择谱面上的音符，查看 MIDI 音高、起始时间和时长。";
let original = null;
let result = null;
let worker = null;
let deadline;
let page = 0;
let selection = null;
let inputRevision = 0;

function status(message, error = false) {
  elements.status.textContent = message;
  elements.status.toggleAttribute("data-error", error);
}

function clearWorker() {
  clearTimeout(deadline);
  worker?.terminate();
  worker = null;
  elements.run.disabled = false;
  elements.cancel.disabled = true;
}

function updatePage() {
  selection = null;
  elements.note.textContent = noteHint;
  elements.score.replaceChildren();
  elements.empty.hidden = Boolean(result);
  elements["page-number"].textContent = result ? (page + 1) + " / " + result.pages.length : "—";
  elements.previous.disabled = !result || page === 0;
  elements.next.disabled = !result || page >= result.pages.length - 1;
  elements.svg.disabled = elements.midi.disabled = !result;
  if (!result) return;
  const svg = result.pages[page].cloneNode(true);
  for (const note of svg.querySelectorAll("g.note[data-note-id]")) {
    note.setAttribute("role", "button");
    note.setAttribute("tabindex", "0");
    note.setAttribute("aria-label", "检查音符");
    note.setAttribute("aria-pressed", "false");
  }
  elements.score.append(svg);
}

function invalidate(message, error = false) {
  clearWorker();
  result = null;
  page = 0;
  updatePage();
  status(message, error);
}

function replaceInput(text, message) {
  original = text;
  elements.source.value = text;
  elements.restore.disabled = false;
  invalidate(message);
}

elements.source.addEventListener("input", () => {
  inputRevision++;
  invalidate("输入已更改。请重新排版后导出。");
});

elements.file.addEventListener("change", async () => {
  const file = elements.file.files[0];
  elements.file.value = "";
  if (!file) return;
  const revision = ++inputRevision;
  invalidate("正在读取本机文件。");
  try {
    if (file.size > MAX_BYTES) throw new Error("文件超过 192 KiB。");
    const text = new TextDecoder("utf-8", {fatal: true}).decode(await file.arrayBuffer());
    if (revision === inputRevision) replaceInput(text, "已读取本机文件。请排版查看。");
  } catch (error) {
    if (revision === inputRevision) status(error instanceof TypeError ? "请选择 UTF-8 编码的 XML 文件。" : error.message, true);
  }
});

elements.example.addEventListener("click", async () => {
  const revision = ++inputRevision;
  invalidate("正在载入内置示例。");
  try {
    const response = await fetch("./example.musicxml");
    if (!response.ok) throw new Error();
    const text = await response.text();
    if (revision === inputRevision) replaceInput(text, "已载入《晨光练习曲》。请排版查看。");
  } catch {
    if (revision === inputRevision) status("无法读取内置示例。", true);
  }
});

elements.restore.addEventListener("click", () => {
  if (original === null) return;
  inputRevision++;
  replaceInput(original, "已恢复导入原文。请重新排版。");
});

function render() {
  inputRevision++;
  invalidate("正在本机排版。");
  try {
    validateScore(elements.source.value);
    const active = new Worker("./worker.js");
    worker = active;
    elements.run.disabled = true;
    elements.cancel.disabled = false;
    deadline = setTimeout(() => invalidate("排版超时。请缩小乐谱范围后重试。", true), 12000);
    active.onerror = () => {
      if (active === worker) invalidate("排版引擎加载失败。请重试。", true);
    };
    active.onmessage = ({data}) => {
      if (active !== worker) return;
      if (data.type === "error") {
        invalidate(data.message, true);
      } else if (data.type === "score") {
        try {
          result = {pages: data.pages.map(safeScoreSvg), midi: data.midi};
          clearTimeout(deadline);
          elements.run.disabled = false;
          elements.cancel.disabled = true;
          updatePage();
          status("排版完成。可检查音符并导出。");
        } catch (error) {
          invalidate(error.message, true);
        }
      } else if (data.type === "note" && data.id === selection?.getAttribute("data-note-id")) {
        clearTimeout(deadline);
        const {pitch, time, duration} = data.values;
        elements.note.textContent = [pitch, time, duration].every(Number.isFinite)
          ? "MIDI 音高 " + pitch + " · 起始 " + time + " 毫秒 · 时长 " + duration + " 毫秒"
          : "此音符没有独立的 MIDI 事件可供检查。";
      }
    };
    active.postMessage({action: "render", xml: elements.source.value});
  } catch (error) {
    invalidate(error.message, true);
  }
}

function selectNote(note) {
  if (!note || !worker || !result) return;
  selection?.setAttribute("aria-pressed", "false");
  selection = note;
  note.setAttribute("aria-pressed", "true");
  elements.note.textContent = "正在检查音符。";
  clearTimeout(deadline);
  deadline = setTimeout(() => invalidate("音符检查超时。请重新排版。", true), 12000);
  worker.postMessage({action: "inspect", id: note.getAttribute("data-note-id")});
}

function movePage(delta) {
  if (!result || page + delta < 0 || page + delta >= result.pages.length) return;
  clearTimeout(deadline);
  page += delta;
  updatePage();
}

function download(body, mime, name) {
  const url = URL.createObjectURL(new Blob([body], {type: mime}));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

elements.run.addEventListener("click", render);
elements.cancel.addEventListener("click", () => invalidate("已取消排版。"));
elements.previous.addEventListener("click", () => movePage(-1));
elements.next.addEventListener("click", () => movePage(1));
elements.score.addEventListener("click", event => selectNote(event.target.closest("g.note[data-note-id]")));
elements.score.addEventListener("keydown", event => {
  if (["Enter", " "].includes(event.key) && event.target.matches("g.note[data-note-id]")) {
    event.preventDefault();
    selectNote(event.target);
  }
});
elements.svg.addEventListener("click", () => {
  if (result) download(new XMLSerializer().serializeToString(result.pages[page]), "image/svg+xml", "乐谱-" + (page + 1) + ".svg");
});
elements.midi.addEventListener("click", () => {
  if (result) download(Uint8Array.from(atob(result.midi), c => c.charCodeAt(0)), "audio/midi", "乐谱.mid");
});
