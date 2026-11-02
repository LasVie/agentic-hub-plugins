import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';

const state = await fs.mkdtemp(path.join(await fs.realpath(tmpdir()), 'change-verification-unit-'));
process.env.CHANGE_VERIFICATION_STATE_DIR = state;
const payload = path.resolve(process.env.CHANGE_VERIFICATION_PAYLOAD || new URL('../change-verification', import.meta.url).pathname);
const moduleAt = relative => import(pathToFileURL(path.join(payload, relative)));
const engine = await moduleAt('runtime/engine.mjs');
const store = await moduleAt('runtime/store.mjs');
const exports = await moduleAt('runtime/export.mjs');
const git = await moduleAt('runtime/git.mjs');
const { buildIndexFromFileMap, rippleFrom, isIndexedSource } = await moduleAt('vendor/deps.js');
const sample = await engine.demo();
const png = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aO9sAAAAASUVORK5CYII=';
const fresh = () => engine.analyze(sample);
after(async () => { await fs.rm(state, { recursive: true, force: true }); });

test('演示仓库有两个真实提交，分析保持用户仓库和 Git 配置不变', async () => {
  assert.notEqual(sample.base, sample.head);
  assert.equal((await git.git(sample.root, ['rev-list', '--count', 'HEAD'])).toString().trim(), '2');
  const config = await fs.readFile(path.join(sample.root, '.git/config'));
  const status = await git.git(sample.root, ['status', '--porcelain']);
  const report = await fresh();
  assert.equal(report.demo, true);
  assert.deepEqual(await fs.readFile(path.join(sample.root, '.git/config')), config);
  assert.deepEqual(await git.git(sample.root, ['status', '--porcelain']), status);
  assert.deepEqual(report.changes.map(row => row.status).sort(), ['D', 'M']);
  assert.equal(report.items.length, 5);
  assert(report.items.every(row => row.status === 'pending' && row.result_source === null));
  assert(report.diff_excerpt.includes('-export function canCheckout(token: string) { return token.length > 0; }'));
  assert(report.diff_excerpt.includes('+export function canCheckout(token: string) { return token.trim().length >= 8; }'));
  assert.deepEqual(store.counts(report), { pending: 5, pass: 0, fail: 0, skip: 0 });
});
test('实际依赖链识别两层调用方及被删除接口的旧调用方', async () => {
  const report = await fresh();
  const checkout = report.items.find(row => row.path === 'src/checkout.ts');
  const page = report.items.find(row => row.path === 'src/CheckoutPage.tsx');
  const oldPage = report.items.find(row => row.path === 'src/LegacyPage.tsx');
  assert.deepEqual(checkout.dependency, { depth: 1, via: 'src/auth.ts' });
  assert.deepEqual(page.dependency, { depth: 2, via: 'src/checkout.ts' });
  assert.equal(oldPage.dependency.via, 'src/legacy.ts');
  assert(!report.items.some(row => row.path === 'src/unrelated.ts'));
});
test('未提交工作区内容不会替代已选提交快照或依赖链', async () => {
  const actual = await engine.demo();
  await fs.writeFile(path.join(actual.root, 'src/auth.ts'), 'export const unsafeWorktree = "不能代替提交";\n');
  await fs.writeFile(path.join(actual.root, 'src/checkout.ts'), 'export const unrelated = true;\n');
  const report = await engine.analyze(actual);
  assert(report.diff_excerpt.includes('token.trim().length >= 8'));
  assert(!report.diff_excerpt.includes('unsafeWorktree'));
  assert(report.items.some(row => row.path === 'src/checkout.ts' && row.kind === 'ripple'));
});
test('Git 路径按字面值处理，不解释路径匹配表达式', async () => {
  const actual = await engine.demo();
  const file = path.join(actual.root, ':(glob)*.ts');
  const commit = async message => git.git(actual.root, ['-c', 'user.name=测试', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', message]);
  await fs.writeFile(file, 'export const literal = 1;\n');
  await git.git(actual.root, ['add', '--all']); await commit('路径基线');
  const base = await git.resolve(actual.root, 'HEAD');
  await fs.writeFile(file, 'export const literal = 2;\n');
  await git.git(actual.root, ['add', '--all']); await commit('路径目标');
  const report = await engine.analyze({ root: actual.root, base, head: 'HEAD' });
  assert.equal(report.changes[0].path, ':(glob)*.ts');
  assert(report.diff_excerpt.includes('+export const literal = 2;'));
  assert(!report.diff_excerpt.includes('canCheckout'));
});
test('深度零只保留直接项；相同端点为空且不能说功能通过', async () => {
  const report = await engine.analyze({ ...sample, depth: 0 });
  assert.equal(report.items.length, 2);
  const empty = await engine.analyze({ ...sample, head: sample.base });
  assert.equal(empty.items.length, 0);
  assert.match(exports.markdown(empty), /不表示所有功能通过/);
});
test('拒绝未授权范围扩大、远程地址、无效提交与参数', async () => {
  await assert.rejects(() => engine.analyze({ ...sample, root: path.join(sample.root, 'src') }), /顶层/);
  await assert.rejects(() => engine.analyze({ ...sample, root: 'https://example.invalid/repo' }), /绝对路径/);
  await assert.rejects(() => engine.analyze({ ...sample, base: '--help' }), /引用格式/);
  await assert.rejects(() => engine.analyze({ ...sample, head: 'unknown-ref' }), /Git 读取失败/);
  await assert.rejects(() => engine.analyze({ ...sample, depth: 4 }), /深度/);
  await assert.rejects(() => engine.analyze({ ...sample, modules: [{ prefix: '../bad', name: '无效' }] }), /映射/);
});
test('隐藏、敏感、依赖目录和路径穿越不能进入索引', async () => {
  for (const value of ['../file.ts', '.env', 'src/.hidden.ts', 'node_modules/a.ts', 'secrets/file.ts', '/tmp/a.ts', 'src/a\n.ts']) assert.equal(git.safePath(value), false);
  for (const value of ['src/main.ts', 'src/支付.tsx', 'src/a b.ts']) assert.equal(git.safePath(value), true);
  assert.equal(isIndexedSource('dist/bundle.js'), false);
  const report = await fresh();
  assert(report.scan.head.omissions['保护路径或不支持的类型'] >= 2);
  assert(!JSON.stringify(report).includes('SYNTHETIC_DEMO_ONLY'));
});
test('纯算法保留 TS 别名、Java、Vue 样式和循环依赖边界', () => {
  const files = new Map([
    ['src/utils/format.ts', 'export const f = 1'],
    ['src/view.tsx', "import { f } from '@/utils/format'"],
    ['app/OrderRepo.java', 'class OrderRepo {}'],
    ['app/PayActivity.java', 'import app.OrderRepo; class PayActivity {}'],
    ['src/styles.scss', '.checkout { color: blue; }'],
    ['src/page.vue', '<template><div class="checkout"></div></template>'],
    ['src/a.ts', "import './b'"], ['src/b.ts', "import './a'"],
  ]);
  const index = buildIndexFromFileMap(files);
  assert(index.reverseDeps.get('src/utils/format.ts').has('src/view.tsx'));
  assert(index.reverseDeps.get('app/OrderRepo.java').has('app/PayActivity.java'));
  assert(index.reverseDeps.get('src/styles.scss').has('src/page.vue'));
  assert.deepEqual([...rippleFrom(['src/a.ts'], index.reverseDeps, 3).keys()], ['src/b.ts']);
});
test('跳过二进制、超限、符号链接，扫描统计不假装完整', async () => {
  const root = (await engine.demo()).root;
  await fs.writeFile(path.join(root, 'src/binary.ts'), Buffer.from([1, 0, 2]));
  await fs.writeFile(path.join(root, 'src/large.ts'), 'x'.repeat(262145));
  await fs.symlink('/etc/passwd', path.join(root, 'src/link.ts'));
  await git.git(root, ['add', '--all']);
  await git.git(root, ['-c', 'user.name=测试', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', '边界样本']);
  const snap = await git.snapshot(root, await git.resolve(root, 'HEAD'));
  assert.equal(snap.counts.omissions['二进制内容'], 1);
  assert.equal(snap.counts.omissions['单文件超限'], 1);
  assert.equal(snap.counts.omissions['符号链接或子模块'], 1);
  assert(!snap.files.has('src/link.ts'));
});
test('过多变更明确拒绝，不生成虚假的完整清单', async () => {
  const demo = await engine.demo();
  for (let n = 0; n < 101; n++) await fs.writeFile(path.join(demo.root, `src/file${n}.ts`), `export const value${n}=1;`);
  await git.git(demo.root, ['add', '--all']);
  await git.git(demo.root, ['-c', 'user.name=测试', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', 'commit', '--quiet', '-m', '大变更']);
  await assert.rejects(() => engine.analyze({ ...demo, head: 'HEAD' }), /超过 100/);
});
test('缺失源码对象明确拒绝，不联网补齐或读取工作区冒充', async () => {
  const actual = await engine.demo();
  const oid = (await git.git(actual.root, ['rev-parse', 'HEAD:src/auth.ts'])).toString().trim();
  await fs.rm(path.join(actual.root, '.git/objects', oid.slice(0, 2), oid.slice(2)));
  await assert.rejects(() => engine.analyze(actual), /本地缺失的源码对象/);
});
test('失败、跳过要求备注，拒绝无效截图与状态', async () => {
  const report = await fresh();
  const args = { report_id: report.id, revision: 0, item_id: report.items[0].id, note: '', screenshots: [] };
  await assert.rejects(() => engine.result({ ...args, status: 'fail' }), /必须填写/);
  await assert.rejects(() => engine.result({ ...args, status: 'skip' }), /必须填写/);
  await assert.rejects(() => engine.result({ ...args, status: 'everything-passed' }), /状态/);
  assert.throws(() => engine.image({ name: 'x.svg', data_url: 'data:image/svg+xml;base64,PHN2Zz4=' }), /PNG/);
  assert.throws(() => engine.image({ name: 'bad.png', data_url: 'data:image/png;base64,YmFk' }), /PNG/);
  assert.throws(() => engine.image({ name: '../bad.png', data_url: png }), /名称/);
  assert.equal((await store.load(report.id)).revision, 0);
});
test('实际结果、原始证据哈希和其余未验证状态持久保存', async () => {
  const report = await fresh();
  const saved = await engine.result({ report_id: report.id, revision: 0, item_id: report.items[0].id, status: 'fail',
    note: '演示记录：只测试结果保存，不是真实业务失败。', screenshots: [{ name: '演示.png', data_url: png }] });
  const loaded = await store.load(saved.id);
  assert.equal(loaded.revision, 1);
  assert.deepEqual(store.counts(loaded), { pending: 4, pass: 0, fail: 1, skip: 0 });
  assert.equal(loaded.items[0].screenshots[0].sha256, store.digest(Buffer.from(png.split(',')[1], 'base64')));
  assert(!JSON.stringify(store.publicReport(loaded)).includes(png));
  assert.match(loaded.items[0].result_source, /人工录入/);
});
test('旧修订与并发写入不能覆盖新结果', async () => {
  const report = await fresh();
  const args = { report_id: report.id, revision: 0, item_id: report.items[0].id, status: 'skip', note: '本轮未验证', screenshots: [] };
  const outcomes = await Promise.allSettled([engine.result(args), engine.result({ ...args, status: 'fail' })]);
  assert.equal(outcomes.filter(row => row.status === 'fulfilled').length, 1);
  assert.equal((await store.load(report.id)).revision, 1);
  await assert.rejects(() => engine.result(args), /版本已变化/);
});
test('模型只可完善待验证项的步骤，不能改测试结果', async () => {
  const report = await fresh();
  const item = report.items[0];
  const planned = await engine.plan({ report_id: report.id, revision: 0, item_id: item.id, steps: ['检查空令牌被拒绝。'] });
  assert.equal(planned.items[0].status, 'pending');
  assert.deepEqual(planned.items[0].suggested_steps, ['检查空令牌被拒绝。']);
  await engine.result({ report_id: report.id, revision: 1, item_id: item.id, status: 'pass', note: '演示录入', screenshots: [] });
  await assert.rejects(() => engine.plan({ report_id: report.id, revision: 2, item_id: item.id, steps: ['悄悄更改'] }), /已有测试结果/);
});
test('中文导出保留失败、跳过与未验证，HTML 转义脚本，CSV 防公式', async () => {
  let report = await fresh();
  report = await engine.result({ report_id: report.id, revision: 0, item_id: report.items[0].id, status: 'fail', note: '<script>恶意()</script>', screenshots: [{ name: '证据.png', data_url: png }] });
  report = await engine.result({ report_id: report.id, revision: 1, item_id: report.items[1].id, status: 'skip', note: '=HYPERLINK("https://example.invalid")', screenshots: [] });
  const result = await exports.exportFiles(report);
  assert.equal(result.files.length, 4);
  assert.match(result.markdown, /失败（用户录入）/);
  assert.match(result.markdown, /跳过（用户录入）/);
  const html = await fs.readFile(result.files.find(row => row.path.endsWith('.html')).path, 'utf8');
  assert(html.includes(png));
  assert(!html.includes('<script>恶意()'));
  assert(html.includes('&lt;script&gt;'));
  const csv = exports.csv(report);
  assert(csv.includes("'=HYPERLINK"));
  assert.deepEqual((await exports.exportFiles(report)).files, result.files);
});
test('报告路径穿越、缓存符号链接与身份不符被拒绝', async () => {
  await assert.rejects(() => store.load('../outside'), /标识无效/);
  const fake = 'f'.repeat(32);
  await fs.symlink('/etc/passwd', path.join(state, 'reports', fake + '.json'));
  await assert.rejects(() => store.load(fake), /不可安全读取/);
  const report = await fresh();
  const target = await store.reportPath(report.id);
  report.version = '0.0.0';
  await fs.writeFile(target, JSON.stringify(report));
  await assert.rejects(() => store.load(report.id), /版本不匹配/);
});
