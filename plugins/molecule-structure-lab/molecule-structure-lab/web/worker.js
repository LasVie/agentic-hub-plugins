"use strict";

let engine = null;
let initialization = null;
let initializationStage = "start";
const vendorBase = new URL("../vendor/rdkit/", self.location.href);

async function initialize() {
  initializationStage = "import_vendor";
  importScripts(new URL("RDKit_minimal.js", vendorBase).href);
  initializationStage = "import_core";
  importScripts(new URL("../engine/core.js", self.location.href).href);
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 10000);
  try {
    initializationStage = "fetch_wasm";
    const response = await fetch(new URL("RDKit_minimal.wasm", vendorBase), {
      signal: abort.signal,
      credentials: "same-origin",
      cache: "no-cache"
    });
    if (!response.ok) throw new Error("wasm_unavailable");
    initializationStage = "read_wasm";
    const wasmBinary = await response.arrayBuffer();
    initializationStage = "instantiate_wasm";
    engine = await initRDKitModule({
      wasmBinary,
      locateFile: path => new URL(path, vendorBase).href,
      print: () => {},
      printErr: () => {}
    });
    initializationStage = "engine_ready";
    self.postMessage({
      type: "ready",
      version: MoleculeCore.VERSION,
      rdkit_version: engine.version(),
      limits: MoleculeCore.LIMITS
    });
  } finally {
    clearTimeout(timeout);
  }
}

self.onmessage = async event => {
  const message = event.data;
  if (!message || typeof message !== "object") return;
  if (message.type === "init") {
    if (initialization) return;
    initialization = initialize();
    try {
      await initialization;
    } catch (error) {
      const diagnostic = {
        stage: initializationStage,
        name: String(error && error.name || "Error").slice(0, 80),
        message: String(error && error.message || "unknown")
          .replace(/https?:\/\/[^\s'\"]+/g, "[local-resource]")
          .slice(0, 240)
      };
      self.postMessage({type: "initialization_error", diagnostic, message: "本地计算引擎加载失败。请确认本地服务仍在运行，并使用支持 WebAssembly 的浏览器后重试。"});
    }
    return;
  }
  if (message.type !== "analyze" || !engine || !Number.isSafeInteger(message.requestId)) return;
  try {
    const result = MoleculeCore.analyze(engine, {smiles: message.smiles, smarts: message.smarts});
    self.postMessage({type: "result", requestId: message.requestId, result});
  } catch (_) {
    self.postMessage({type: "result", requestId: message.requestId, result: {
      ok: false,
      version: MoleculeCore.VERSION,
      error: {code: "engine_failed", message: "计算引擎未能完成此次分析；请检查或缩短输入后重试。"}
    }});
  }
};
