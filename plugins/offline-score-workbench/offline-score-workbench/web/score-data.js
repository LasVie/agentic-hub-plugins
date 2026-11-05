const MEI = "http://www.music-encoding.org/ns/mei";
const SVG = "http://www.w3.org/2000/svg";
const XLINK = "http://www.w3.org/1999/xlink";
const XML = "http://www.w3.org/XML/1998/namespace";
export const MAX_BYTES = 192 * 1024;

const musicElements = new Set(("score-partwise work work-title movement-title identification creator rights part-list score-part part-name part-abbreviation score-instrument instrument-name midi-instrument midi-channel midi-program part measure attributes divisions key fifths mode time beats beat-type clef sign line staves transpose chromatic octave-change direction direction-type words metronome beat-unit per-minute sound note pitch step alter octave duration type rest chord voice staff accidental tie notations tied slur dot backup forward barline bar-style beam stem print").split(" "));
const meiElements = new Set(("mei meiHead fileDesc titleStmt title respStmt persName pubStmt music body mdiv score scoreDef staffGrp staffDef section measure staff layer note rest mRest chord beam clef keySig meterSig accid dot tie slur dir tempo label labelAbbr pb sb").split(" "));
const allowedAttributes = new Set(("id version number type placement tempo dynamics font-size font-family font-weight font-style print-object width height new-page new-system implicit line end-line color location default-x default-y relative-x relative-y print-spacing print-dot print-lyric measure justify halign valign parentheses meiversion n lines meter.count meter.unit clef.shape clef.line key.sig pname oct dur dots accid accid.ges stem.dir startid endid tstamp tstamp2 midi.bpm form shape sig count unit label layer staff metcon").split(" "));
const noteIdentity = /^[A-Za-z_][A-Za-z0-9_.-]{0,99}$/;

export function validateScore(text) {
  if (!text.trim()) throw new Error("请先输入乐谱。");
  if (new TextEncoder().encode(text).length > MAX_BYTES) throw new Error("乐谱超过 192 KiB。");
  if (/<!\s*(DOCTYPE|ENTITY)\b/i.test(text) || /<\?(?!xml\s)/i.test(text)) {
    throw new Error("不支持文档类型声明、实体声明或外部处理指令。");
  }
  const doc = new DOMParser().parseFromString(text, "application/xml");
  if (doc.getElementsByTagNameNS("*", "parsererror").length) throw new Error("XML 格式无效。");
  const root = doc.documentElement;
  const mei = root.localName === "mei" && root.namespaceURI === MEI;
  const music = root.localName === "score-partwise" && root.namespaceURI === null;
  if ((!music && !mei) || root.prefix) throw new Error("仅支持 MusicXML score-partwise 或带 MEI 命名空间的乐谱。");
  const names = mei ? meiElements : musicElements;
  const elements = doc.getElementsByTagName("*");
  if (elements.length > 3500) throw new Error("乐谱元素过多。");
  const ids = new Set();
  let notes = 0;
  let measures = 0;
  for (const element of elements) {
    if (element.namespaceURI !== root.namespaceURI || element.prefix || !names.has(element.localName)) {
      throw new Error("含有不支持的乐谱元素：" + element.localName);
    }
    if (element.localName === "note") notes++;
    if (element.localName === "measure") measures++;
    let depth = 0;
    for (let parent = element.parentElement; parent; parent = parent.parentElement) depth++;
    if (depth > 32) throw new Error("乐谱嵌套过深。");
    for (const attr of element.attributes) {
      const xml = attr.namespaceURI === XML && (attr.localName === "id" || attr.localName === "lang");
      const xmlns = mei && element === root && attr.name === "xmlns" && attr.value === MEI;
      if (!xmlns && !xml && (attr.namespaceURI || !allowedAttributes.has(attr.name))) {
        throw new Error("含有不支持的属性：" + attr.name);
      }
      if (attr.value.length > 160) throw new Error("乐谱属性过长。");
      if ((xml && attr.localName === "id") || (element.localName === "note" && attr.name === "id")) {
        if (!noteIdentity.test(attr.value) || ids.has(attr.value)) throw new Error("音符或元素标识无效或重复。");
        ids.add(attr.value);
      }
      if (["startid", "endid"].includes(attr.name) && !/^#[A-Za-z_][A-Za-z0-9_.-]{0,99}$/.test(attr.value)) {
        throw new Error("连接记号仅支持本乐谱内的元素标识。");
      }
    }
  }
  if (notes < 1 || notes > 512 || measures < 1 || measures > 128) throw new Error("乐谱须包含 1 至 512 个音符和 1 至 128 个小节。");
}

const svgElements = new Set("svg desc title defs g path use text tspan ellipse circle rect line polygon polyline".split(" "));
const strokedShapes = new Set(["ellipse", "path", "polygon", "polyline", "rect"]);
const geometry = new Set("x y cx cy rx ry r width height x1 x2 y1 y2 viewBox d points transform stroke-width font-size dx dy textLength".split(" "));
const enumerated = {
  "font-weight": /^(normal|bold|[1-9]00)$/,
  "font-style": /^(normal|italic|oblique)$/,
  "text-anchor": /^(start|middle|end)$/,
  "stroke-linecap": /^(butt|round|square)$/,
  "stroke-linejoin": /^(miter|round|bevel)$/,
  overflow: /^(visible|hidden)$/,
};
const paint = /^(none|currentColor|#[\da-fA-F]{3,8}|[a-zA-Z]{1,24})$/;

export function safeScoreSvg(markup) {
  const doc = new DOMParser().parseFromString(markup, "image/svg+xml");
  if (doc.documentElement.localName !== "svg" || doc.documentElement.namespaceURI !== SVG) {
    throw new Error("谱面生成失败。");
  }
  const glyphs = new Set(Array.from(doc.querySelectorAll("defs [id]"), element => element.id));
  // Reconstruct allowed drawing primitives without adding the original SVG to the page.
  function copy(node) {
    if (node.nodeType === Node.TEXT_NODE) return document.createTextNode(node.textContent);
    if (node.namespaceURI !== SVG || !svgElements.has(node.localName) || node.classList.contains("placeholder")) return null;
    const target = document.createElementNS(SVG, node.localName);
    for (const attr of node.attributes) {
      const {name, value, localName, namespaceURI} = attr;
      if (node.localName === "use" && localName === "href" && (namespaceURI === XLINK || !namespaceURI) &&
          value.startsWith("#") && glyphs.has(value.slice(1)) && noteIdentity.test(value.slice(1))) {
        target.setAttribute("href", "#score-" + value.slice(1));
      } else if (!namespaceURI && (
        (geometry.has(name) && /^[A-Za-z0-9 .,+()%\-\t\r\n]+$/.test(value)) ||
        (Object.hasOwn(enumerated, name) && enumerated[name].test(value)) ||
        (["fill", "stroke", "color"].includes(name) && paint.test(value)) ||
        (name === "id" && noteIdentity.test(value)) ||
        (name === "class" && /^[\w -]{1,200}$/.test(value)) ||
        (name === "font-family" && /^[A-Za-z0-9 ,'-]{1,100}$/.test(value))
      )) {
        target.setAttribute(name, name === "id" ? "score-" + value : value);
      }
    }
    if (strokedShapes.has(node.localName) && !target.hasAttribute("stroke")) {
      target.setAttribute("stroke", "currentColor");
    }
    if (node.localName === "g" && target.classList.contains("note") && noteIdentity.test(node.id)) {
      target.setAttribute("data-note-id", node.id);
    }
    for (const child of node.childNodes) {
      const safe = copy(child);
      if (safe) target.append(safe);
    }
    return target;
  }
  const svg = copy(doc.documentElement);
  if (!svg.hasAttribute("viewBox") || !svg.querySelector("g.note")) throw new Error("排版结果缺少可检查的音符。");
  return svg;
}
