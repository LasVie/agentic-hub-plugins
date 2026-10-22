#!/usr/bin/env node
// 修改说明（Agentic Hub 团队，2026-10-22）：将位置、帮助与错误文本翻译为简体中文；保留原算法、协议值及 MIT 署名。

import { createHash, randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";

const DEFAULT_DECK_PATH = fileURLToPath(new URL("../assets/deck.json", import.meta.url));
const SCHEMA_VERSION = "1.0";

export const SPREADS = Object.freeze({
  daily: ["反思主题"],
  "three-card": ["过去或背景", "当前动态", "未来倾向"],
  decision: ["当前情况", "选项 A", "选项 B", "需要考虑的因素", "务实的下一步"],
  relationship: ["你自己", "对方或你感受到的互动", "彼此的联结", "优势", "挑战", "建设性的下一步"],
  "celtic-cross": [
    "当前情况",
    "挑战或交叉影响",
    "基础",
    "最近的过去",
    "有意识的目标或可能性",
    "近期方向",
    "你的立场",
    "环境或外部影响",
    "希望与恐惧",
    "结果倾向",
  ],
  "yes-no": ["象征倾向"],
});

function normalize(value) {
  return String(value)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function comparableNames(value) {
  const normalized = normalize(value);
  return new Set([normalized, normalized.replace(/^the\s+/, "")]);
}

export function loadDeck(path = DEFAULT_DECK_PATH) {
  const raw = readFileSync(path, "utf8");
  const parsed = JSON.parse(raw);
  return { ...parsed, _path: path, _sha256: createHash("sha256").update(raw).digest("hex") };
}

export function validateDeck(deck) {
  const errors = [];
  if (!Array.isArray(deck.cards)) errors.push("cards 必须是数组");
  if (deck.count !== deck.cards?.length) errors.push("count 必须等于 cards.length");
  if (deck.cards?.length !== 78) errors.push("牌组必须恰好包含 78 张牌");

  const required = [
    "card_number",
    "card_name",
    "arcana",
    "element",
    "upright_meaning",
    "reversed_meaning",
    "love_meaning",
    "career_meaning",
    "yes_or_no",
    "guide_url",
  ];
  const names = new Set();
  const urls = new Set();

  for (const [index, card] of (deck.cards ?? []).entries()) {
    for (const field of required) {
      if (typeof card[field] !== "string" || !card[field].trim()) {
        errors.push(`cards[${index}].${field} 必须是非空字符串`);
      }
    }
    for (const optionalField of ["suit", "zodiac_sign"]) {
      if (typeof card[optionalField] !== "string") {
        errors.push(`cards[${index}].${optionalField} 必须是字符串`);
      }
    }
    const nameKey = normalize(card.card_name);
    if (names.has(nameKey)) errors.push(`重复的 card_name： ${card.card_name}`);
    names.add(nameKey);

    if (urls.has(card.guide_url)) errors.push(`重复的 guide_url： ${card.guide_url}`);
    urls.add(card.guide_url);
    try {
      const url = new URL(card.guide_url);
      if (url.protocol !== "https:" || !/(^|\.)deckaura\.com$/i.test(url.hostname)) {
        errors.push(`无效的 Deckaura guide_url： ${card.guide_url}`);
      }
    } catch {
      errors.push(`guide_url 格式错误： ${card.guide_url}`);
    }
  }

  return { ok: errors.length === 0, errors };
}

export function lookupCard(query, deck = loadDeck()) {
  const wanted = comparableNames(query);
  const exact = deck.cards.find((card) => {
    const names = comparableNames(card.card_name);
    return [...wanted].some((value) => names.has(value));
  });
  if (exact) return { card: exact, suggestions: [] };

  const needle = normalize(query);
  const suggestions = deck.cards
    .filter((card) => normalize(card.card_name).includes(needle))
    .slice(0, 10)
    .map((card) => card.card_name);
  return { card: null, suggestions };
}

function seedToUint32(seed) {
  return createHash("sha256").update(String(seed)).digest().readUInt32LE(0);
}

function mulberry32(initial) {
  let state = initial >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let value = state;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function publicCard(card, orientation, position) {
  return {
    position,
    card_number: card.card_number,
    card_name: card.card_name,
    orientation,
    meaning: orientation === "reversed" ? card.reversed_meaning : card.upright_meaning,
    arcana: card.arcana,
    suit: card.suit,
    element: card.element,
    love_meaning: card.love_meaning,
    career_meaning: card.career_meaning,
    yes_or_no: card.yes_or_no,
    zodiac_sign: card.zodiac_sign,
    guide_url: card.guide_url,
  };
}

export function drawCards({ count = 1, seed, reversals = true, positions = [], deck = loadDeck() } = {}) {
  if (!Number.isInteger(count) || count < 1 || count > deck.cards.length) {
    throw new RangeError(`count 必须是 1 至 ${deck.cards.length} 的整数`);
  }
  const effectiveSeed = seed ?? randomBytes(16).toString("hex");
  const rng = mulberry32(seedToUint32(effectiveSeed));
  const pool = [...deck.cards];

  for (let index = pool.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(rng() * (index + 1));
    [pool[index], pool[swapIndex]] = [pool[swapIndex], pool[index]];
  }

  const cards = pool.slice(0, count).map((card, index) => {
    const orientation = reversals && rng() < 0.33 ? "reversed" : "upright";
    return publicCard(card, orientation, positions[index] ?? `第 ${index + 1} 张牌`);
  });

  return {
    schema_version: SCHEMA_VERSION,
    source: deck.source,
    seed: effectiveSeed,
    reversals,
    cards,
  };
}

export function createSpread(name, options = {}) {
  const positions = SPREADS[name];
  if (!positions) {
    throw new Error(`未知牌阵：${name}。请选择： ${Object.keys(SPREADS).join(", ")}`);
  }
  return { spread: name, ...drawCards({ ...options, count: positions.length, positions }) };
}

function parseOptions(args) {
  const positional = [];
  const options = {};
  for (let index = 0; index < args.length; index += 1) {
    const token = args[index];
    if (!token.startsWith("--")) {
      positional.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = args[index + 1];
    if (next === undefined || next.startsWith("--")) {
      options[key] = true;
    } else {
      options[key] = next;
      index += 1;
    }
  }
  return { positional, options };
}

function parseBoolean(value, fallback) {
  if (value === undefined) return fallback;
  if (value === true || value === "true") return true;
  if (value === false || value === "false") return false;
  throw new Error("布尔选项必须是 true 或 false");
}

function print(value) {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`);
}

function usage() {
  return {
    usage: [
      '查询卡牌：node scripts/tarot.mjs lookup "The Star"',
      "抽牌：node scripts/tarot.mjs draw --count 1 --reversals true [--seed 非敏感标签]",
      `创建牌阵：node scripts/tarot.mjs spread <${Object.keys(SPREADS).join("|")}> [--reversals true] [--seed 非敏感标签]`,
      "检查数据：node scripts/tarot.mjs validate",
    ],
  };
}

export function runCli(argv = process.argv.slice(2)) {
  const [command, ...rest] = argv;
  const { positional, options } = parseOptions(rest);
  const deck = loadDeck();

  if (command === "lookup") {
    const query = positional.join(" ").trim();
    if (!query) throw new Error("lookup 需要卡牌名称（使用数据集中的英文 card_name）");
    const result = lookupCard(query, deck);
    if (!result.card) {
      const error = new Error(`未找到卡牌： ${query}`);
      error.suggestions = result.suggestions;
      throw error;
    }
    const orientation = options.orientation === "reversed" ? "reversed" : "upright";
    print({ schema_version: SCHEMA_VERSION, source: deck.source, card: publicCard(result.card, orientation, "查询") });
    return;
  }

  if (command === "draw") {
    const count = options.count === undefined ? 1 : Number(options.count);
    print(drawCards({ count, seed: options.seed, reversals: parseBoolean(options.reversals, true), deck }));
    return;
  }

  if (command === "spread") {
    const name = positional[0];
    if (!name) throw new Error("spread 需要牌阵名称");
    print(createSpread(name, { seed: options.seed, reversals: parseBoolean(options.reversals, true), deck }));
    return;
  }

  if (command === "validate") {
    const validation = validateDeck(deck);
    print({ ...validation, count: deck.cards.length, sha256: deck._sha256, source: deck.source });
    if (!validation.ok) process.exitCode = 1;
    return;
  }

  print(usage());
  if (command) process.exitCode = 1;
}

const isMain = process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url;
if (isMain) {
  try {
    runCli();
  } catch (error) {
    process.stderr.write(`${JSON.stringify({ error: error.message, suggestions: error.suggestions ?? [] })}\n`);
    process.exitCode = 1;
  }
}
