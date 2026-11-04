import fs from 'node:fs/promises';
import path from 'node:path';
import { buildIndexFromFileMap, rippleFrom } from '../vendor/deps.js';
import { classifyFileRisk, heuristicDisplayName } from '../vendor/heuristics.js';
import { repository, resolve, changed, snapshot, safePath, git, limits } from './git.mjs';
import { cacheRoot, directory, newID, saveNew, digest, update } from './store.mjs';

export const boundary = '静态引用和路径规则生成的人工回归候选，可能误报或漏报；未执行项目代码，不代表功能已通过。状态为用户在面板录入的结果，不是自动测试证明。';
export async function analyze(args) {
  const root = await repository(args.root);
  const depth = args.depth ?? 2;
  if (!Number.isInteger(depth) || depth < 0 || depth > limits.depth) throw new Error('依赖扩散深度必须是 0 到 3 的整数。');
  const modules = args.modules ?? [];
  if (!Array.isArray(modules) || modules.length > 30 || modules.some(row => !row || !safePath(row.prefix) ||
    typeof row.name !== 'string' || !row.name.trim() || row.name.length > 60 || /[\x00-\x1f]/.test(row.name))) throw new Error('模块映射最多 30 项；每项需要安全的相对路径前缀和简短中文名称。');
  const base = await resolve(root, args.base);
  const head = await resolve(root, args.head);
  const allChanges = await changed(root, base, head);
  const changes = allChanges.filter(row => safePath(row.path));
  const before = await snapshot(root, base);
  const after = base === head ? before : await snapshot(root, head);
  const diffPaths = changes.map(row => row.path).filter(file => before.files.has(file) || after.files.has(file));
  const diffText = diffPaths.length ? (await git(root, ['diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--unified=3', base, head, '--', ...diffPaths], 1048576)).toString('utf8') : '';
  const diffExcerpt = diffText.slice(0, 40000);
  const indexBefore = buildIndexFromFileMap(before.files);
  const indexAfter = buildIndexFromFileMap(after.files);
  const seeds = changes.map(row => row.path);
  const edges = new Map();
  for (const index of [indexBefore, indexAfter]) for (const [file, parents] of index.reverseDeps) {
    if (!edges.has(file)) edges.set(file, new Set());
    for (const parent of parents) edges.get(file).add(parent);
  }
  const ripples = [...rippleFrom(seeds, edges, depth)].sort(([a], [b]) => a.localeCompare(b));
  const warnings = [];
  if (diffText.length > diffExcerpt.length) warnings.push('提交差异片段仅返回前 40000 个字符，后续改动未展示；不要据此编造未展示逻辑。');
  const protectedCount = allChanges.length - changes.length;
  if (protectedCount) warnings.push(`${protectedCount} 个受保护路径的变更未展示或分析。`);
  for (const [label, snap] of [['基线', before], ['目标', after]]) {
    const omitted = Object.values(snap.counts.omissions).reduce((a, b) => a + b, 0);
    if (omitted) warnings.push(`${label}快照跳过 ${omitted} 个不适用或受限路径，详见扫描统计。`);
  }
  if (ripples.length + changes.length > limits.items) warnings.push(`清单最多 ${limits.items} 项，后续间接候选未纳入；请缩小比较范围后复核。`);
  const make = (file, kind, detail, changeStatus = null, meta = null) => {
    const mapping = modules.find(row => file === row.prefix || file.startsWith(row.prefix + '/'));
    const heuristic = heuristicDisplayName(file);
    const label = mapping?.name || (/相关$/.test(heuristic) ? heuristic : `代码模块（${path.posix.basename(file)}）`);
    return { id: digest(kind + ':' + file).slice(0, 20), path: file, display_name: label, kind,
      risk: classifyFileRisk(file), change_status: changeStatus, evidence: detail, dependency: meta,
      suggested_steps: kind === 'direct' ? [
        `核对 ${file} 在两个提交中的实际改动与预期。`,
        `在适当的测试环境覆盖「${label}」主路径及异常输入；记录实际观察。`,
        changeStatus === 'D' ? '确认删除后的入口、调用方和错误处理符合预期。' : '检查与调用方的输入、输出及边界行为是否兼容。',
      ] : [`确认 ${file} 经由 ${meta.via} 的静态引用关系仍适用。`,
        `人工回归「${label}」依赖该变更的路径，并记录实际观察。`, '检查空数据、错误和边界场景；不适用时填写跳过原因。'],
      status: 'pending', note: '', screenshots: [], result_source: null, result_at: null };
  };
  const items = changes.map(row => make(row.path, 'direct', `Git 端点差异 ${row.status}：${base.slice(0, 12)} → ${head.slice(0, 12)}`, row.status));
  for (const [file, meta] of ripples.slice(0, limits.items - items.length)) items.push(make(file, 'ripple',
    `两个快照的静态反向依赖候选，第 ${meta.depth} 层，经由 ${meta.via}；不证明运行时会受影响。`, null, meta));
  const rank = { high: 3, medium: 2, low: 1 };
  items.sort((a, b) => rank[b.risk] - rank[a.risk] || a.path.localeCompare(b.path));
  const created = new Date().toISOString();
  let demo = false;
  if (root.startsWith(path.join(cacheRoot, 'demos') + path.sep)) {
    try { const marker = JSON.parse(await fs.readFile(path.join(root, 'demo-info.json'), 'utf8')); demo = marker.base === base && marker.head === head; } catch {}
  }
  return saveNew({ id: newID(), version: '1.0.0', display_name: '变更影响与回归检查台', root, base, head, depth,
    demo, created_at: created, updated_at: created, revision: 0, boundary,
    comparison: '两个提交端点，非合并基线；重命名按删除与新增分别列出。', changes, protected_change_count: protectedCount,
    scan: { base: before.counts, head: after.counts, ripple_candidates: ripples.length },
    diff_excerpt: diffExcerpt, diff_excerpt_truncated: diffText.length > diffExcerpt.length, warnings, items });
}
export async function demo() {
  const parent = await directory(path.join(cacheRoot, 'demos'));
  const root = await fs.mkdtemp(path.join(parent, 'sample-'));
  await fs.chmod(root, 0o700);
  const files = {
    'README.md': '# 演示订单项目\n\n虚构代码，仅用于验证影响分析，不是真实产品或测试证明。\n',
    'src/auth.ts': 'export function canCheckout(token: string) { return token.length > 0; }\n',
    'src/checkout.ts': "import { canCheckout } from './auth';\nexport function checkout(token: string) { return canCheckout(token); }\n",
    'src/CheckoutPage.tsx': "import { checkout } from './checkout';\nexport const CheckoutPage = () => checkout('演示');\n",
    'src/unrelated.ts': 'export const greeting = "不相关模块";\n',
    'src/legacy.ts': 'export const legacy = true;\n',
    'src/LegacyPage.tsx': "import { legacy } from './legacy';\nexport const LegacyPage = () => legacy;\n",
    '.env': 'SYNTHETIC_DEMO_ONLY=not-a-real-secret\n',
  };
  for (const [file, text] of Object.entries(files)) {
    await fs.mkdir(path.dirname(path.join(root, file)), { recursive: true });
    await fs.writeFile(path.join(root, file), text);
  }
  await git(root, ['init', '--quiet']);
  await git(root, ['add', '--', '.']);
  const commit = async message => git(root, ['-c', 'user.name=演示材料', '-c', 'user.email=demo@example.invalid',
    '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', message]);
  await commit('演示基线');
  const base = await resolve(root, 'HEAD');
  await fs.writeFile(path.join(root, 'src/auth.ts'), 'export function canCheckout(token: string) { return token.trim().length >= 8; }\n');
  await fs.rm(path.join(root, 'src/legacy.ts'));
  await git(root, ['add', '--all']);
  await commit('演示登录规则修改及旧接口删除');
  const head = await resolve(root, 'HEAD');
  const result = { root, base, head, data_kind: '虚构演示仓库；不会执行这些代码。', modules: [
    { prefix: 'src/auth.ts', name: '登录与结算权限' }, { prefix: 'src/checkout.ts', name: '结算服务' },
    { prefix: 'src/CheckoutPage.tsx', name: '结算页面' }, { prefix: 'src/legacy.ts', name: '旧接口删除' },
    { prefix: 'src/LegacyPage.tsx', name: '旧页面兼容性' },
  ] };
  await fs.writeFile(path.join(root, 'demo-info.json'), JSON.stringify(result), { mode: 0o600 });
  return result;
}
export async function plan(args) {
  if (!Array.isArray(args.steps) || !args.steps.length || args.steps.length > 8 ||
    args.steps.some(step => typeof step !== 'string' || !step.trim() || step.length > 300 || /[\x00-\x08]/.test(step))) throw new Error('建议验证步骤应为 1 至 8 条简短中文文字。');
  return update(args.report_id, args.revision, report => {
    const item = report.items.find(row => row.id === args.item_id);
    if (!item) throw new Error('清单项不存在。');
    if (item.status !== 'pending' || item.result_at) throw new Error('已有测试结果的清单不能悄悄改写步骤，请另建分析报告。');
    item.suggested_steps = args.steps.map(step => step.trim());
    item.plan_source = '会话模型建议，未执行验证';
  });
}
export function image(input) {
  if (!input || typeof input.name !== 'string' || input.name.length > 100 || /[\x00-\x1f\\/]/.test(input.name)) throw new Error('截图名称无效。');
  if (typeof input.data_url !== 'string' || input.data_url.length > 1400000) throw new Error('截图过大；每张最多 1 MiB。');
  const match = input.data_url.match(/^data:image\/(png|jpeg);base64,([A-Za-z0-9+/]+={0,2})$/);
  if (!match) throw new Error('仅接受 PNG 或 JPEG 截图，不接受 SVG 或外部图片地址。');
  const buffer = Buffer.from(match[2], 'base64');
  if (!buffer.length || buffer.length > 1048576 || buffer.toString('base64') !== match[2]) throw new Error('截图编码或大小无效。');
  if (match[1] === 'png') {
    if (buffer.length < 33 || buffer.subarray(0, 8).toString('hex') !== '89504e470d0a1a0a' || buffer.subarray(12, 16).toString() !== 'IHDR') throw new Error('PNG 文件头无效。');
    const width = buffer.readUInt32BE(16), height = buffer.readUInt32BE(20);
    if (!width || !height || width > 8192 || height > 8192 || width * height > 16777216) throw new Error('PNG 图片尺寸超限。');
  } else if (buffer.subarray(0, 3).toString('hex') !== 'ffd8ff' || buffer.subarray(-2).toString('hex') !== 'ffd9') throw new Error('JPEG 文件头或结尾无效。');
  return { name: input.name, mime: 'image/' + match[1], bytes: buffer.length, sha256: digest(buffer), data_url: input.data_url };
}
export async function result(args) {
  if (!['pending', 'pass', 'fail', 'skip'].includes(args.status) || typeof args.note !== 'string' || args.note.length > 1500) throw new Error('测试状态或备注无效。');
  if (['fail', 'skip'].includes(args.status) && !args.note.trim()) throw new Error('失败或跳过必须填写实际观察或原因。');
  if (!Array.isArray(args.screenshots) || args.screenshots.length > 3) throw new Error('每项最多保存 3 张截图。');
  const screenshots = args.screenshots.map(image);
  return update(args.report_id, args.revision, report => {
    const item = report.items.find(row => row.id === args.item_id);
    if (!item) throw new Error('清单项不存在。');
    item.status = args.status;
    item.note = args.note.trim();
    item.screenshots = screenshots;
    item.result_source = '浏览器面板人工录入，未独立核验';
    item.result_at = new Date().toISOString();
  });
}
