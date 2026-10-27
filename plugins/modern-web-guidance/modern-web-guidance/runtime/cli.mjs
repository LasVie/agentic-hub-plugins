// 现代网页技术指南：只读取包内静态指南，不联网、不写文件、不执行指南示例。
import { readFileSync } from 'node:fs';
import { buildBm25Index, rankBm25, tokenize } from './bm25.mjs';

let data;
try {
  data = JSON.parse(readFileSync(new URL('../data/catalog.json', import.meta.url), 'utf8'));
  if (!Array.isArray(data.guides) || data.guides.length !== 12 ||
      data.guides.some(g => !/^[a-z][a-z0-9-]*$/.test(g.id))) throw new Error();
} catch {
  process.stdout.write(JSON.stringify({ok: false, message: '指南目录损坏或缺失，请重新安装完整插件。'}) + '\n');
  process.exit(2);
}
const byId = new Map(data.guides.map(g => [g.id, g]));
const index = buildBm25Index(data.guides.map(g => ({
  id: g.id, text: `${g.id} ${g.title} ${g.keywords} ${g.description}`,
})));
const metadata = {version: '1.0.0', upstream_version: data.upstream_version,
  snapshot_date: data.snapshot_date, guide_count: data.guides.length,
  scope: '12 篇中文精选改编指南；固定快照，非实时兼容性数据库。'};
const fail = message => ({ok: false, message, ...metadata});
const summary = g => ({id: g.id, title: g.title, description: g.description,
  category: g.category, source: g.source});

export function run(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) return fail('输入必须是对象。');
  if (Object.keys(input).some(k => !['action', 'query', 'ids', 'limit'].includes(k))) return fail('包含不支持的参数。');
  const {action} = input;
  if (action === 'help') return {ok: true, ...metadata,
    message: '先 search 搜索主题，再 retrieve 读取命中的指南；未命中可 list 查看范围。',
    actions: {search: 'query：1–300 字查询；limit：1–12，默认 5。支持中文与 API 名称。',
      retrieve: 'ids：1–3 个列表或搜索返回的真实指南 ID。', list: '列出全部 12 篇指南。',
      help: '显示使用说明、版本和覆盖范围。'},
    example: {action: 'search', query: '中文输入法回车误提交'}};
  if (action === 'list') return {ok: true, ...metadata, guides: data.guides.map(summary)};
  if (action === 'search') {
    if (typeof input.query !== 'string' || !input.query.trim() || input.query.length > 300) return fail('查询须为 1–300 字的非空文本。');
    const limit = input.limit ?? 5;
    if (!Number.isInteger(limit) || limit < 1 || limit > 12) return fail('limit 须为 1–12 的整数。');
    const terms = [...new Set(tokenize(input.query))];
    const results = rankBm25(index, input.query).filter(r => {
      const guide = byId.get(r.id);
      const tokens = new Set(tokenize(`${guide.id} ${guide.title} ${guide.keywords} ${guide.description}`));
      const hits = terms.filter(t => tokens.has(t));
      // 长查询只命中一个普通汉语双字词时，不足以建立相关性。
      // 精确 API/英文关键词和单主题短查询仍可直接命中。
      const names = new Set(tokenize(`${guide.id} ${guide.keywords}`));
      return hits.length >= Math.min(2, terms.length) ||
        hits.some(t => /^[a-z0-9]/.test(t) && names.has(t));
    }).slice(0, limit).map(r => ({...summary(byId.get(r.id)), score: r.score}));
    return {ok: true, ...metadata, results,
      message: results.length ? '请按描述确认相关性，再读取指南。分数仅用于本次排序，不代表兼容性或置信度。'
        : '未命中本版精选指南。可用 list 查看范围；不要编造指南或循环重试。'};
  }
  if (action === 'retrieve') {
    if (!Array.isArray(input.ids) || input.ids.length < 1 || input.ids.length > 3 ||
        input.ids.some(id => typeof id !== 'string' || !byId.has(id))) return fail('ids 须包含 1–3 个真实指南 ID，请先 search 或 list。');
    // 路径仅取自受信任的包内目录清单，不使用调用者提供的路径。
    return {ok: true, ...metadata, guides: [...new Set(input.ids)].map(id => {
      const g = byId.get(id);
      return {...summary(g), content: readFileSync(new URL(`../data/guides/${g.id}.md`, import.meta.url), 'utf8')};
    })};
  }
  return fail('未知操作，请使用 help、search、list 或 retrieve。');
}

let chunks = [], size = 0;
try {
  for await (const chunk of process.stdin) {
    size += chunk.length;
    if (size > 16384) throw new Error('输入过大，请缩短查询。');
    chunks.push(chunk);
  }
  let parsed;
  try { parsed = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw new Error('请输入有效的 JSON 对象。'); }
  const result = run(parsed);
  process.stdout.write(JSON.stringify(result) + '\n');
  if (!result.ok) process.exitCode = 2;
} catch (error) {
  process.stdout.write(JSON.stringify(fail(error.message === '输入过大，请缩短查询。' ||
    error.message === '请输入有效的 JSON 对象。' ? error.message : '包内指南无法读取，请重新安装完整插件。')) + '\n');
  process.exitCode = 2;
}
