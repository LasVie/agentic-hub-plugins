"use strict";
importScripts("./vendor/verovio-toolkit-wasm.js");

let toolkit;
let midiAvailable = false;
const ready = new Promise(resolve => {
  if (verovio.module.calledRun) resolve();
  else verovio.module.onRuntimeInitialized = resolve;
});

self.addEventListener("message", async ({data}) => {
  try {
    await ready;
    if (data.action === "inspect") {
      const values = midiAvailable ? toolkit.getMIDIValuesForElement(data.id) : {};
      self.postMessage({type: "note", id: data.id, values});
      return;
    }
    toolkit = new verovio.toolkit();
    toolkit.setOptions({
      svgViewBox: true, adjustPageHeight: true, pageWidth: 1600, pageHeight: 1600,
      footer: "none", fontTextLiberation: false, smuflTextFont: "none",
    });
    if (!toolkit.loadData(data.xml)) throw new Error("引擎无法导入此乐谱。请检查结构和受支持的记号。");
    const count = toolkit.getPageCount();
    if (count < 1 || count > 16) throw new Error("排版结果须包含 1 至 16 页。");
    const pages = [];
    let total = 0;
    for (let page = 1; page <= count; page++) {
      const svg = toolkit.renderToSVG(page);
      total += svg.length;
      if (total > 5 * 1024 * 1024) throw new Error("谱面输出过大。");
      pages.push(svg);
    }
    const midi = toolkit.renderToMIDI();
    midiAvailable = midi.startsWith("TVRoZA") && midi.length <= 512 * 1024;
    if (!midiAvailable) throw new Error("MIDI 导出失败或超出大小限制。");
    self.postMessage({type: "score", pages, midi});
  } catch (error) {
    self.postMessage({type: "error", message: error instanceof Error && /[\u3400-\u9fff]/.test(error.message)
      ? error.message : "排版引擎未能完成本次操作。请检查输入后重试。"});
  }
});
