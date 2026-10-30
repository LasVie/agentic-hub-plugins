"use strict";

(() => {
  const $ = id => document.getElementById(id);
  const ui = {
    form: $("molecule-form"), smiles: $("smiles"), smarts: $("smarts"), analyze: $("analyze"),
    analyzeText: $("analyze-text"), cancel: $("cancel"), feedback: $("feedback"),
    engineState: $("engine-state"), results: $("results"), badge: $("result-badge"),
    empty: $("empty-state"), image: $("structure-image"), staleOverlay: $("stale-overlay"),
    properties: $("properties-panel"), summary: $("structure-summary"), match: $("match-panel"),
    exportSvg: $("export-svg"), exportJson: $("export-json")
  };
  const presets = {
    aspirin: {smiles: "CC(=O)Oc1ccccc1C(=O)O", smarts: "c1ccccc1"},
    ethanol: {smiles: "CCO", smarts: "c1ccccc1"},
    benzene: {smiles: "c1ccccc1", smarts: "c1ccccc1"}
  };
  const descriptorOrder = ["amw", "exactmw", "CrippenClogP", "tpsa", "NumHBA", "NumHBD", "NumRotatableBonds", "NumRings"];
  const descriptorPrecision = {amw: 3, exactmw: 6, CrippenClogP: 3, tpsa: 2};
  let worker = null;
  let ready = false;
  let initializing = false;
  let busy = false;
  let timer = null;
  let revision = 0;
  let requestId = 0;
  let requestRevision = null;
  let acceptedRevision = null;
  let result = null;
  let resultTime = null;
  let imageUrl = null;
  let analyzeAfterReady = false;
  let inputLimits = {smiles: 1024, smarts: 512};

  function feedback(message, tone = "") {
    ui.feedback.textContent = message;
    ui.feedback.className = "feedback" + (tone ? " " + tone : "");
  }

  function badge(message, tone = "neutral") {
    ui.badge.textContent = message;
    ui.badge.className = "result-badge " + tone;
  }

  function setControls() {
    ui.analyze.disabled = initializing || busy;
    ui.analyzeText.textContent = initializing ? "引擎加载中…" : busy ? "正在分析…" : ready ? "运行分析" : "重新加载并分析";
    ui.cancel.hidden = !busy;
    ui.results.setAttribute("aria-busy", String(busy));
    const canExport = !!result && acceptedRevision === revision && !busy && !initializing;
    ui.exportSvg.disabled = !canExport;
    ui.exportJson.disabled = !canExport;
  }

  function stopWorker() {
    clearTimeout(timer);
    timer = null;
    if (worker) worker.terminate();
    worker = null;
    ready = false;
    initializing = false;
    busy = false;
    analyzeAfterReady = false;
    requestId += 1;
    ui.engineState.textContent = "RDKit 引擎已释放";
  }

  function resetResult() {
    result = null;
    acceptedRevision = null;
    resultTime = null;
    if (imageUrl) URL.revokeObjectURL(imageUrl);
    imageUrl = null;
    ui.image.removeAttribute("src");
    ui.image.hidden = true;
    ui.empty.hidden = false;
    ui.properties.hidden = true;
    ui.summary.hidden = true;
    ui.match.hidden = true;
    ui.staleOverlay.hidden = true;
    ui.results.classList.remove("stale");
  }

  function fail(message, code = "", inputError = false) {
    busy = false;
    clearTimeout(timer);
    timer = null;
    resetResult();
    badge("分析未完成", "error");
    $("empty-title").textContent = "未生成有效结果";
    $("empty-description").textContent = "调整输入或重新加载引擎后再次运行。";
    feedback(message + (code ? "（" + code + "）" : ""), "error");
    if (inputError) {
      const target = code.includes("smarts") || code.includes("query") ? ui.smarts : ui.smiles;
      target.setAttribute("aria-invalid", "true");
    }
    setControls();
  }

  function startWorker(runWhenReady = false) {
    stopWorker();
    initializing = true;
    analyzeAfterReady = runWhenReady;
    ui.engineState.textContent = "正在加载本地 RDKit 引擎…";
    ui.engineState.classList.remove("error");
    setControls();
    try {
      const currentWorker = new Worker("worker.js");
      worker = currentWorker;
      timer = setTimeout(() => {
        if (worker !== currentWorker) return;
        stopWorker();
        ui.engineState.classList.add("error");
        fail("引擎加载超过 12 秒，计算线程已释放。请确认本地服务可用后重试。", "engine_timeout");
      }, 12000);
      currentWorker.onmessage = event => {
        if (worker !== currentWorker) return;
        const message = event.data;
        if (message.type === "ready") {
          clearTimeout(timer);
          timer = null;
          ready = true;
          initializing = false;
          $("plugin-version").textContent = message.version;
          ui.engineState.textContent = "RDKit " + message.rdkit_version + " · 本地引擎就绪";
          if (message.limits) {
            inputLimits = message.limits;
            $("limits-note").textContent = "单次限制：SMILES " + message.limits.smiles + " 字符、SMARTS " + message.limits.smarts + " 字符、分子 " + message.limits.atoms + " 个原子 / " + message.limits.bonds + " 条键。查询最多 " + message.limits.query_atoms + " 个原子 / " + message.limits.query_bonds + " 条键。";
          }
          setControls();
          if (analyzeAfterReady) {
            analyzeAfterReady = false;
            analyze();
          } else {
            feedback("本地引擎已就绪。点击“运行分析”查看当前输入的结果。");
          }
        } else if (message.type === "initialization_error") {
          console.error("[molecule-workbench] Local engine initialization failed " + JSON.stringify(message.diagnostic));
          stopWorker();
          ui.engineState.classList.add("error");
          fail(message.message, "engine_unavailable");
        } else if (message.type === "result" && message.requestId === requestId) {
          clearTimeout(timer);
          timer = null;
          busy = false;
          if (requestRevision !== revision) {
            setControls();
            return;
          }
          if (!message.result || !message.result.ok) {
            const error = message.result && message.result.error;
            fail(error ? error.message : "未收到有效的计算结果。", error ? error.code : "invalid_result", true);
          } else {
            renderResult(message.result);
          }
        }
      };
      currentWorker.onerror = event => {
        event.preventDefault();
        if (worker !== currentWorker) return;
        stopWorker();
        ui.engineState.classList.add("error");
        fail("本地计算线程发生错误并已释放。请检查输入或重新加载后重试。", "worker_failed");
      };
      currentWorker.postMessage({type: "init"});
    } catch (_) {
      stopWorker();
      ui.engineState.classList.add("error");
      fail("此浏览器无法启动本地计算线程。请从插件提供的本地网址打开工作台。", "worker_unavailable");
    }
  }

  function markEdited() {
    revision += 1;
    acceptedRevision = null;
    ui.smiles.removeAttribute("aria-invalid");
    ui.smarts.removeAttribute("aria-invalid");
    if (busy) stopWorker();
    for (const button of document.querySelectorAll("[data-preset]")) {
      const preset = presets[button.dataset.preset];
      const selected = ui.smiles.value === preset.smiles && ui.smarts.value === preset.smarts;
      button.classList.toggle("selected", selected);
      button.setAttribute("aria-pressed", String(selected));
    }
    if (result) {
      ui.results.classList.add("stale");
      ui.staleOverlay.hidden = false;
      badge("结果待更新", "warning");
      feedback("输入已修改；下方仍为上次结果。请重新分析后再导出。", "warning");
    } else {
      badge("等待分析");
      $("empty-title").textContent = "等待分析当前输入";
      $("empty-description").textContent = "点击“运行分析”，生成当前输入的二维结构与结果。";
      feedback("输入已修改，请运行分析。");
    }
    setControls();
  }

  function analyze() {
    if (busy || initializing) return;
    acceptedRevision = null;
    ui.smiles.removeAttribute("aria-invalid");
    ui.smarts.removeAttribute("aria-invalid");
    if (!ui.smiles.value.trim()) {
      fail("请先输入分子 SMILES。", "smiles_required", true);
      ui.smiles.focus();
      return;
    }
    if (ui.smiles.value.length > inputLimits.smiles || ui.smarts.value.length > inputLimits.smarts) {
      fail("输入超过限制：SMILES 最多 " + inputLimits.smiles + " 字符，SMARTS 最多 " + inputLimits.smarts + " 字符。原输入已保留，没有截断后继续计算。", "input_too_large");
      const target = ui.smiles.value.length > inputLimits.smiles ? ui.smiles : ui.smarts;
      target.setAttribute("aria-invalid", "true");
      target.focus();
      return;
    }
    if (!ready) {
      feedback("正在重新加载本地引擎，随后分析当前输入。", "busy");
      startWorker(true);
      return;
    }
    busy = true;
    requestId += 1;
    requestRevision = revision;
    const currentRequest = requestId;
    if (result) {
      ui.results.classList.add("stale");
      ui.staleOverlay.hidden = false;
    }
    badge("正在分析", "busy");
    feedback("正在本地解析结构、计算描述符并执行子结构查询…", "busy");
    setControls();
    timer = setTimeout(() => {
      if (currentRequest !== requestId) return;
      stopWorker();
      fail("计算超过 12 秒，已中止并释放线程。请缩短 SMILES 或简化 SMARTS 后重试。", "analysis_timeout");
    }, 12000);
    worker.postMessage({type: "analyze", requestId: currentRequest, smiles: ui.smiles.value, smarts: ui.smarts.value});
  }

  function renderResult(value) {
    resetResult();
    result = value;
    acceptedRevision = revision;
    resultTime = new Date().toISOString();
    imageUrl = URL.createObjectURL(new Blob([value.svg], {type: "image/svg+xml"}));
    ui.image.src = imageUrl;
    ui.image.alt = value.match.matched ? "当前分子的二维结构，已高亮 SMARTS 首个匹配的原子与键" : "当前分子的二维结构";
    ui.image.hidden = false;
    ui.empty.hidden = true;
    ui.summary.hidden = false;
    $("atom-count").textContent = value.atom_count;
    $("bond-count").textContent = value.bond_count;
    ui.match.hidden = false;
    ui.match.className = "match-panel";
    if (!value.match.query_supplied) {
      ui.match.classList.add("no-query");
      $("match-title").textContent = "未设置子结构查询";
    } else if (value.match.matched) {
      $("match-title").textContent = "找到首个匹配 · 已高亮";
    } else {
      ui.match.classList.add("no-match");
      $("match-title").textContent = "未匹配到子结构";
    }
    $("match-description").textContent = value.match.message;
    $("match-indices").hidden = !value.match.matched;
    $("match-atoms").textContent = "[" + value.match.atoms.join(", ") + "]";
    $("match-bonds").textContent = "[" + value.match.bonds.join(", ") + "]";
    $("canonical-smiles").textContent = value.canonical_smiles;
    const descriptors = $("descriptors");
    descriptors.replaceChildren();
    for (const key of descriptorOrder) {
      const container = document.createElement("div");
      container.className = "descriptor";
      const title = document.createElement("dt");
      title.textContent = value.descriptor_labels[key];
      const number = document.createElement("dd");
      const precision = descriptorPrecision[key] === undefined ? 0 : descriptorPrecision[key];
      number.textContent = Number(value.descriptors[key]).toLocaleString("zh-CN", {maximumFractionDigits: precision, useGrouping: false});
      const keyLabel = document.createElement("span");
      keyLabel.className = "descriptor-code";
      keyLabel.textContent = key;
      number.append(keyLabel);
      container.append(title, number);
      descriptors.append(container);
    }
    ui.properties.hidden = false;
    badge("分析完成", "success");
    feedback(value.match.query_supplied && !value.match.matched ? "结构与描述符已计算。当前 SMARTS 未匹配到子结构；这不是解析错误。" : "分析完成。结果对应当前输入，可导出 SVG 或 JSON。", "success");
    setControls();
  }

  function exportMetadata() {
    const {svg, ...data} = result;
    return {
      export_schema_version: 1,
      plugin_name: "离线分子结构工作台",
      analyzed_at: resultTime,
      ...data,
      export_notice: "仅对应所列输入的本地计算。SMARTS 为首个匹配；未枚举全部匹配，不构成药效、毒性或临床结论。"
    };
  }

  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  ui.form.addEventListener("submit", event => {event.preventDefault(); analyze();});
  for (const input of [ui.smiles, ui.smarts]) {
    input.addEventListener("input", markEdited);
    input.addEventListener("keydown", event => {
      if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {event.preventDefault(); analyze();}
    });
  }
  for (const button of document.querySelectorAll("[data-preset]")) {
    button.addEventListener("click", () => {
      const preset = presets[button.dataset.preset];
      ui.smiles.value = preset.smiles;
      ui.smarts.value = preset.smarts;
      markEdited();
    });
  }
  ui.cancel.addEventListener("click", () => {
    stopWorker();
    acceptedRevision = null;
    if (result) {ui.results.classList.add("stale"); ui.staleOverlay.hidden = false;}
    badge("已取消", "warning");
    feedback("此次计算已取消，线程已释放。下次运行将重新加载本地引擎。", "warning");
    setControls();
  });
  ui.exportJson.addEventListener("click", () => {
    if (ui.exportJson.disabled || !result || acceptedRevision !== revision) return;
    download(new Blob([JSON.stringify(exportMetadata(), null, 2) + "\n"], {type: "application/json;charset=utf-8"}), "分子分析-" + result.version + ".json");
    feedback("已向浏览器请求下载 JSON。请在浏览器下载列表中确认文件保存结果。", "success");
  });
  ui.exportSvg.addEventListener("click", () => {
    if (ui.exportSvg.disabled || !result || acceptedRevision !== revision) return;
    const svgDocument = new DOMParser().parseFromString(result.svg, "image/svg+xml");
    if (svgDocument.querySelector("parsererror") || svgDocument.documentElement.localName !== "svg") {
      feedback("结构图无法导出为有效 SVG，请重新分析。", "error");
      return;
    }
    const metadata = svgDocument.createElementNS("http://www.w3.org/2000/svg", "metadata");
    metadata.textContent = JSON.stringify(exportMetadata());
    svgDocument.documentElement.insertBefore(metadata, svgDocument.documentElement.firstChild);
    const svg = '<?xml version="1.0" encoding="UTF-8"?>\n' +
      new XMLSerializer().serializeToString(svgDocument.documentElement) + "\n";
    download(new Blob([svg], {type: "image/svg+xml;charset=utf-8"}), "分子结构-" + result.version + ".svg");
    feedback("已向浏览器请求下载 SVG。图中包含本次版本与输入元数据，请在下载列表中确认。", "success");
  });
  window.addEventListener("pagehide", () => {stopWorker(); if (imageUrl) URL.revokeObjectURL(imageUrl);});
  window.addEventListener("pageshow", event => {
    if (event.persisted) {
      resetResult();
      badge("等待分析");
      startWorker();
    }
  });
  startWorker();
})();
