import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';
import http from 'node:http';

const sdkRoot = process.env.CHANGE_TEST_MCP_SDK;
const playwrightRoot = process.env.CHANGE_TEST_PLAYWRIGHT;
assert(sdkRoot && playwrightRoot, '请指定已有的独立 MCP SDK 与 Playwright 开发依赖路径；本脚本不安装依赖。');
const { Client } = await import(pathToFileURL(path.join(sdkRoot, 'client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(path.join(sdkRoot, 'client/stdio.js')));
const { chromium } = createRequire(import.meta.url)(playwrightRoot);
const payload = path.resolve(process.argv[2]);
const state = await fs.mkdtemp('/private/tmp/change-verification-mcp-');
const output = path.resolve(process.argv[3] || '/private/tmp/change-verification-ui-evidence');
await fs.mkdir(output, { recursive: true });
const connections = [];
const notes = [];
let browser;
let assertions = 0;
function check(condition, label) { assert(condition, label); assertions++; }
async function connect() {
  const config = JSON.parse(await fs.readFile(path.join(payload, 'mcps/change-verification/mcp.json'), 'utf8')).mcpServers['change-verification'];
  const transport = new StdioClientTransport({ command: config.command, args: config.args,
    cwd: path.join(payload, 'mcps/change-verification'), stderr: 'pipe', env: { ...process.env, CHANGE_VERIFICATION_STATE_DIR: state,
      PATH: '/usr/bin:/bin', PYTHONDONTWRITEBYTECODE: '1' } });
  const client = new Client({ name: 'independent-change-verification-test', version: '1.0.0' });
  await client.connect(transport);
  transport.stderr?.on('data', data => notes.push(data.toString()));
  connections.push(client);
  check((await client.listTools()).tools.length === 6, '六个工具实际通过 SDK 握手列出');
  return client;
}
async function call(client, name, args = {}) {
  const response = await client.callTool({ name, arguments: args }, undefined, { timeout: 120000 });
  return { value: JSON.parse(response.content[0].text), error: Boolean(response.isError) };
}
try {
  const client = await connect();
  check((await call(client, 'verification_status')).value.reports.length === 0, '冷启动空历史，无依赖安装');
  const sample = (await call(client, 'verification_demo')).value;
  check(sample.ok && sample.base !== sample.head, '工具创建实际演示提交');
  const result = await call(client, 'verification_analyze', { root: sample.root, base: sample.base, head: sample.head, modules: sample.modules });
  check(!result.error && result.value.report.items.length === 5, '实际 MCP 分析返回五项');
  const report = result.value.report;
  const reportID = report.id;
  check(report.counts.pending === 5 && report.counts.pass === 0, '所有项目初始未验证');
  check(report.items.some(row => row.path === 'src/LegacyPage.tsx' && row.kind === 'ripple'), '删除项旧引用链保留');
  check(!JSON.stringify(report).includes('SYNTHETIC_DEMO_ONLY'), '隐藏内容没有泄露');
  check((await call(client, 'verification_analyze', { root: sample.root, base: '--help', head: sample.head })).error, '无效引用真实拒绝');
  check((await call(client, 'verification_status', { report_id: reportID, status: 'pass' })).error, '不能通过额外参数代填结果');
  check((await call(client, 'verification_open', { report_id: '../invalid' })).error, '错误报告标识拒绝，不启动浏览器');
  const url = new URL(result.value.panel_url);
  const origin = url.origin;
  const headers = { Authorization: 'Bearer ' + url.hash.slice(1) };
  check((await fetch(origin + '/api/report?id=' + reportID)).status === 403, '未认证读取拒绝');
  check((await fetch(origin + '/api/report?id=' + reportID, { headers: { ...headers, Origin: 'https://example.invalid' } })).status === 403, '跨站读取拒绝');
  const wrongHost = await new Promise((resolve, reject) => {
    const request = http.get(origin + '/api/report?id=' + reportID, { headers: { ...headers, Host: 'localhost:' + url.port } }, response => { response.resume(); resolve(response.statusCode); });
    request.on('error', reject);
  });
  check(wrongHost === 403, '不匹配 Host 拒绝');
  check((await fetch(origin + '/api/result', { method: 'GET', headers })).status === 404, 'GET 不能写测试结果');
  check((await fetch(origin + '/api/result', { method: 'POST', headers: { ...headers, 'Content-Type': 'text/plain' }, body: '{}' })).status === 400, '写入类型校验');
  check((await fetch(origin + '/api/report?id=../outside', { headers })).status === 400, '报告读取路径穿越拒绝');
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', error => pageErrors.push(error.message));
  await page.goto(url.href);
  await page.getByRole('heading', { name: '把代码变更，变成回归清单。' }).waitFor();
  await page.waitForFunction(() => document.querySelectorAll('article.item').length === 5);
  check(await page.locator('html').getAttribute('lang') === 'zh-CN', '中文页面实际加载');
  check(await page.locator('.count.pending b').innerText() === '5', '实际渲染未验证数量');
  check(await page.locator('.count.pass b').innerText() === '0', '没有自动通过');
  const shot = await page.screenshot({ path: path.join(output, 'developer-initial-panel.png'), fullPage: false });
  const first = page.locator('article.item').filter({ hasText: 'src/auth.ts' }).first();
  const firstID = await first.getAttribute('data-id');
  await first.getByLabel('实际状态').selectOption('fail');
  await first.getByRole('button', { name: '保存本项结果' }).click();
  await page.getByRole('status').filter({ hasText: '失败或跳过必须填写' }).waitFor();
  check((await call(client, 'verification_status', { report_id: reportID })).value.report.revision === 0, '失败无备注未落盘');
  await first.getByLabel('实际观察', { exact: true }).fill('开发者自动化演示：检查记录与截图保存。<img src=x onerror=window.injected=1>');
  await first.getByLabel('添加截图').setInputFiles({ name: '开发者测试截图.png', mimeType: 'image/png', buffer: shot });
  await page.getByRole('status').filter({ hasText: '截图已暂存' }).waitFor();
  await first.getByRole('button', { name: '保存本项结果' }).click();
  await page.getByRole('status').filter({ hasText: '本项实际结果已保存' }).waitFor();
  const saved = (await call(client, 'verification_status', { report_id: reportID })).value.report;
  check(saved.counts.fail === 1 && saved.counts.pending === 4 && saved.counts.pass === 0, '浏览器结果通过 MCP 原样读回');
  check(saved.items.find(row => row.id === firstID).screenshots[0].sha256 === createHash('sha256').update(shot).digest('hex'), '截图原始字节哈希一致');
  check(await page.evaluate(() => window.injected) === undefined, '用户备注作为文字，不执行 HTML');
  await page.reload();
  await page.waitForFunction(() => document.querySelector('.count.fail b')?.textContent === '1');
  check(await page.locator('.shot img').evaluate(element => element.complete && element.naturalWidth > 0), '保存截图在浏览器可解码渲染');
  await page.locator('#filter').selectOption('fail');
  check(await page.locator('article.item').count() === 1, '失败筛选实际生效');
  await page.locator('#filter').selectOption('all');
  const second = page.locator('article.item').filter({ hasText: 'src/legacy.ts' }).filter({ has: page.locator('.status') }).first();
  await second.getByLabel('实际状态').selectOption('skip');
  await second.getByLabel('实际观察', { exact: true }).fill('开发者演示：本轮没有验证旧接口行为。');
  await second.getByRole('button', { name: '保存本项结果' }).click();
  await page.getByRole('status').filter({ hasText: '本项实际结果已保存' }).waitFor();
  const current = (await call(client, 'verification_status', { report_id: reportID })).value.report;
  check(current.counts.fail === 1 && current.counts.skip === 1 && current.counts.pending === 3, '保留失败、跳过及其余未验证');
  const staleResponse = await fetch(origin + '/api/result', { method: 'POST', headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({ report_id: reportID, revision: 0, item_id: firstID, status: 'pass', note: '旧面板', screenshots: [] }) });
  check(staleResponse.status === 400 && (await staleResponse.json()).message.includes('版本已变化'), '旧面板不能覆盖结果');
  const downloadWait = page.waitForEvent('download');
  await page.getByRole('button', { name: '下载完整 HTML 报告' }).click();
  const download = await downloadWait;
  await download.saveAs(path.join(output, 'developer-export.html'));
  const html = await fs.readFile(path.join(output, 'developer-export.html'), 'utf8');
  check(html.includes('data:image/png;base64,') && html.includes('失败（用户录入）') && html.includes('跳过（用户录入）'), '下载报告内嵌真实输入证据并保留状态');
  const exportedPage = await context.newPage();
  await exportedPage.goto(pathToFileURL(path.join(output, 'developer-export.html')).href);
  check(await exportedPage.locator('img').evaluate(element => element.complete && element.naturalWidth > 0), '导出 HTML 离线截图可见');
  check(await exportedPage.evaluate(() => window.injected) === undefined, '导出备注安全转义');
  await page.screenshot({ path: path.join(output, 'developer-saved-panel.png'), fullPage: true });
  const exported = (await call(client, 'verification_export', { report_id: reportID })).value;
  check(exported.files.length === 4 && exported.counts.pending === 3, 'MCP 导出四份真实文件，未伪报全部通过');
  for (const file of exported.files) check(createHash('sha256').update(await fs.readFile(file.path)).digest('hex') === file.sha256, '导出文件哈希一致');
  await client.close();
  const reopened = await connect();
  const history = (await call(reopened, 'verification_status')).value;
  check(history.reports.length === 1 && history.reports[0].id === reportID, '全新 MCP 进程读取原报告');
  const resumed = (await call(reopened, 'verification_status', { report_id: reportID })).value.report;
  check(resumed.revision === 2 && resumed.counts.fail === 1 && resumed.items.some(item => item.screenshots.length === 1), '跨进程修订、备注和证据持久保存');
  check(pageErrors.length === 0, '浏览器没有运行错误');
  const evidence = { assertions, payload, launcher: 'declared python3 ../../runtime/launch.py, PATH=/usr/bin:/bin',
    mcp: 'independent SDK stdio', browser: await browser.version(), developer_automation_only: true,
    report_id: reportID, expected_counts: resumed.counts, page_errors: pageErrors, stderr: notes,
    statement: '独立客户端与受控浏览器开发者检查，不是 WorkSwarm 用户验收。' };
  await fs.writeFile(path.join(output, 'result.json'), JSON.stringify(evidence, null, 2) + '\n');
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  for (const client of connections) await client.close().catch(() => {});
  if (browser) await browser.close();
  await fs.rm(state, { recursive: true, force: true });
}
