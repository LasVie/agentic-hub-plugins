import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const repository = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const sourcePayload = process.env.ANNOTATE_PAYLOAD_DIR || path.join(repository, 'plugins/annotate/annotate');
const installation = fs.mkdtempSync(path.join(os.tmpdir(), 'annotate-installed-'));
const payload = path.join(installation, 'annotate');
const cache = path.join(installation, 'cache');
const version = JSON.parse(fs.readFileSync(path.join(sourcePayload, 'manifest.json'), 'utf8')).version;
const evidence = path.join(repository, '.research/annotate', version);
fs.mkdirSync(evidence, { recursive: true });
fs.cpSync(sourcePayload, payload, { recursive: true });
const environment = { ...process.env, ANNOTATE_DATA_DIR: cache, npm_config_cache: process.env.ANNOTATE_NPM_CACHE || '/tmp/huaweisg-npm-cache' };
delete environment.ANNOTATE_NODE;
const npmCacheInitiallyEmpty = !fs.existsSync(environment.npm_config_cache) || fs.readdirSync(environment.npm_config_cache).length === 0;
const runtime = path.join(payload, 'runtime');
assert.ok(!fs.existsSync(path.join(runtime, 'node_modules')), 'Cold start must not inherit installed dependencies');
assert.ok(!fs.existsSync(path.join(cache, 'runtime.json')), 'Cold start must not inherit Node configuration');
const sdk = process.env.ANNOTATE_TEST_SDK || path.join(repository, '../upstream/claude-annotate/node_modules/@modelcontextprotocol/sdk/dist/esm');
const { Client } = await import(pathToFileURL(path.join(sdk, 'client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(path.join(sdk, 'client/stdio.js')));
const configuration = JSON.parse(fs.readFileSync(path.join(payload, 'mcps/annotate/mcp.json'), 'utf8')).mcpServers.annotate;
const mcpDirectory = path.join(payload, 'mcps/annotate');
assert.equal(configuration.command, 'python3');
assert.equal(path.resolve(mcpDirectory, configuration.args[0]), path.join(payload, 'scripts/launch.py'));
const python = process.env.ANNOTATE_PYTHON || path.join(path.dirname(process.execPath), 'python3');
assert.ok(fs.existsSync(python), 'Test Python executable is required');
const transport = new StdioClientTransport({
  command: python,
  args: configuration.args,
  cwd: mcpDirectory,
  env: { ...environment, PATH: '/usr/bin:/bin', ANNOTATE_HEADLESS: '1', ANNOTATE_DEBUG: '1' },
  stderr: 'pipe'
});
const client = new Client({ name: 'annotate-integration', version: '1.0.0' }, { capabilities: {} });
let serverErrors = '';
transport.stderr.on('data', chunk => { serverErrors += chunk.toString(); });
const fixture = fs.readFileSync(path.join(payload, 'demo/index.html'));
const server = http.createServer((request, response) => {
  response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  response.end(fixture);
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const pageUrl = `http://127.0.0.1:${server.address().port}/`;
const checks = [];
const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
async function waitFor(predicate, message, timeout = 15000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await predicate()) return;
    await delay(100);
  }
  throw new Error(message);
}
async function call(name, argumentsObject = {}) {
  const result = await client.callTool({ name, arguments: argumentsObject });
  assert.ok(!result.isError, `${name}: ${JSON.stringify(result.content)}`);
  return result;
}
async function evaluate(expression) {
  const result = await call('annotate_debug', { eval: expression });
  const text = result.content[0].text;
  try { return JSON.parse(text); } catch { return text; }
}
async function capture(filename) {
  const result = await call('annotate_screenshot', { chrome: true });
  const image = result.content.find(item => item.type === 'image');
  assert.ok(image);
  fs.writeFileSync(path.join(evidence, filename), Buffer.from(image.data, 'base64'));
}
try {
  const failedTransport = new StdioClientTransport({ command: python, args: configuration.args, cwd: mcpDirectory, env: { ...environment, PATH: '/usr/bin:/bin', npm_config_cache: path.join(installation, 'empty-npm-cache'), npm_config_offline: 'true' }, stderr: 'pipe' });
  const failedClient = new Client({ name: 'annotate-offline-start', version: '1.0.0' }, { capabilities: {} });
  let failedErrors = '';
  failedTransport.stderr.on('data', chunk => { failedErrors += chunk.toString(); });
  try {
    await assert.rejects(failedClient.connect(failedTransport, { timeout: 240000 }));
    assert.match(failedErrors, /自动安装依赖失败/);
    assert.ok(!fs.existsSync(path.join(runtime, 'node_modules/.annotate-ready.json')));
    fs.writeFileSync(path.join(evidence, 'failed-initialization-stderr.log'), failedErrors);
  } finally {
    await failedClient.close().catch(() => {});
  }
  checks.push('offline cold installation fails clearly without a readiness stamp; following startup retries');
  const peerTransport = new StdioClientTransport({ command: python, args: configuration.args, cwd: mcpDirectory, env: { ...environment, PATH: '/usr/bin:/bin' }, stderr: 'pipe' });
  const peerClient = new Client({ name: 'annotate-parallel-start', version: '1.0.0' }, { capabilities: {} });
  let peerErrors = '';
  peerTransport.stderr.on('data', chunk => { peerErrors += chunk.toString(); });
  try {
    await Promise.all([client.connect(transport, { timeout: 240000 }), peerClient.connect(peerTransport, { timeout: 240000 })]);
    assert.equal((`${serverErrors}\n${peerErrors}`.match(/首次使用正在初始化/g) || []).length, 1);
    assert.ok((await peerClient.listTools()).tools.some(tool => tool.name === 'annotate_open'));
  } finally {
    await peerClient.close().catch(() => {});
  }
  checks.push('two simultaneous real MCP startups share one dependency installation');
  assert.ok(fs.existsSync(path.join(runtime, 'node_modules/.annotate-ready.json')));
  const discoveredNode = JSON.parse(fs.readFileSync(path.join(cache, 'runtime.json'), 'utf8')).node;
  assert.ok(discoveredNode.includes('.app/Contents/Resources/node-runtime/bin/node'));
  checks.push('cold MCP startup discovers bundled WorkSwarm Node and installs dependencies without setup, Conda PATH or cached runtime.json; installation logs do not corrupt protocol');
  assert.ok(!client.getServerCapabilities().experimental?.['claude/channel']);
  const tools = (await client.listTools()).tools;
  assert.ok(tools.some(tool => tool.name === 'annotate_pull'));
  assert.ok(tools.some(tool => tool.name === 'annotate_wait'));
  assert.equal(client.getServerVersion().version, version);
  assert.match(client.getInstructions(), /默认使用简体中文/);
  assert.ok(tools.every(tool => /[\u4e00-\u9fff]/.test(tool.description)));
  checks.push('Chinese default MCP instructions and tool descriptions; protocol identifiers and version preserved');
  checks.push('native package launcher works without Node on host PATH; standard MCP handshake');
  assert.equal(JSON.parse((await call('annotate_pull')).content[0].text).status, 'empty');
  await assert.rejects(client.callTool({ name: 'annotate_open', arguments: { url: 'https://example.com/' } }), /仅支持本地开发主机/);
  await assert.rejects(client.callTool({ name: 'annotate_open', arguments: { url: 'file:///tmp/test.html' } }), /http/);
  checks.push('empty retrieval and rejection of public/non-HTTP URLs');
  const opened = JSON.parse((await call('annotate_open', { url: pageUrl })).content[0].text);
  assert.equal(opened.delivery, 'poll');
  await waitFor(() => evaluate('Boolean(window.__claudeAnnotate?.ready)'), 'Annotation overlay did not become ready');
  assert.equal(await evaluate('document.querySelector("claude-annotate").shadowRoot.querySelector(".send .label").textContent'), '发送给智能体');
  assert.equal(await evaluate('document.querySelector("claude-annotate").shadowRoot.querySelector("[data-tool=rect]").getAttribute("aria-label")'), '矩形');
  assert.equal(JSON.parse((await call('annotate_wait', { timeout_s: 1 })).content[0].text).status, 'timeout');
  checks.push('real Chrome launch, overlay injection and bounded polling timeout');
  const rootExpression = 'document.querySelector("claude-annotate").shadowRoot';
  const button = await evaluate('(() => { const bounds = document.querySelector("#demo-button").getBoundingClientRect(); return {x:bounds.x,y:bounds.y,width:bounds.width,height:bounds.height}; })()');
  await evaluate(`${rootExpression}.querySelector('[data-tool="rect"]').click()`);
  await call('annotate_debug', { mouse: [
    ['move', button.x - 15, button.y - 15], ['down', button.x - 15, button.y - 15],
    ['move', button.x + button.width + 15, button.y + button.height + 15], ['up', button.x + button.width + 15, button.y + button.height + 15]
  ] });
  await evaluate(`${rootExpression}.querySelector('[data-tool="note"]').click()`);
  await call('annotate_debug', { mouse: [['click', button.x + button.width / 2, button.y + button.height / 2]] });
  await evaluate(`(() => { const root = ${rootExpression}; const input = root.querySelector('textarea'); input.value = '请描述这个蓝色按钮，暂时不要修改代码。'; input.dispatchEvent(new Event('input', {bubbles:true})); root.querySelector('.pop .ok').click(); return true; })()`);
  await delay(400);
  await capture('automated-before-send.png');
  await evaluate(`${rootExpression}.querySelector('[data-act="send"]').click()`);
  await waitFor(() => evaluate(`Boolean(${rootExpression}.querySelector('.pin.pending'))`), 'Sent note did not become pending');
  const batch = await call('annotate_pull');
  const batchText = batch.content.find(item => item.type === 'text').text;
  assert.match(batchText, /网页批注 · 批次/);
  assert.match(batchText, /对应元素：/);
  assert.equal(await evaluate(`${rootExpression}.querySelector('.send .label').textContent`), '智能体处理中');
  assert.match(batchText, /请描述这个蓝色按钮/);
  assert.match(batchText, /demo-button/);
  assert.match(batchText, /矩形框选中/);
  const images = batch.content.filter(item => item.type === 'image');
  assert.ok(images.length >= 2, 'Inline crop and overview must be returned');
  assert.equal(Buffer.from(images[0].data, 'base64').subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
  fs.writeFileSync(path.join(evidence, 'automated-received-crop.png'), Buffer.from(images[0].data, 'base64'));
  checks.push('draw rectangle and note through browser controls; send and retrieve exact text/DOM context and inline PNGs');
  await assert.rejects(client.callTool({ name: 'annotate_done', arguments: { summary: 'premature' } }), /明确标记为 done 或 skipped/);
  await assert.rejects(client.callTool({ name: 'annotate_progress', arguments: { note: 9999, status: 'done' } }), /未找到指定的批注/);
  checks.push('premature completion and nonexistent note are rejected');
  await call('annotate_progress', { note: 1, status: 'working', message: '正在审阅按钮' });
  await call('annotate_progress', { note: 1, status: 'done', message: '已确认蓝色按钮：提交测试；未修改代码。' });
  await waitFor(() => evaluate(`Boolean(${rootExpression}.querySelector('.pin.done'))`), 'Completion status did not reach browser');
  await call('annotate_done', { summary: '已描述按钮，未修改源码。', batch: 1 });
  await waitFor(() => evaluate(`${rootExpression}.querySelector('.send .label').textContent === '全部完成'`), 'Chinese completion label did not appear');
  await capture('automated-after-completion.png');
  checks.push('Chinese toolbar labels, batch text, validation errors and completion feedback verified in real Chrome');
  assert.equal(JSON.parse((await call('annotate_pull')).content[0].text).status, 'empty');
  const screenshotDirectories = fs.readdirSync(path.join(cache, 'screenshots')).flatMap(directory => fs.readdirSync(path.join(cache, 'screenshots', directory)).filter(name => name.startsWith('batch-')));
  assert.deepEqual(screenshotDirectories, []);
  checks.push('per-note feedback round trip, explicit completion and deletion of batch screenshots');
  await call('annotate_clear');
  await waitFor(() => evaluate(`${rootExpression}.querySelectorAll('.pin').length === 0`), 'Clear did not remove pins');
  await call('annotate_close');
  assert.equal(JSON.parse((await call('annotate_wait', { timeout_s: 1 })).content[0].text).status, 'closed');
  assert.deepEqual(fs.readFileSync(path.join(payload, 'demo/index.html')), fixture);
  checks.push('clear, browser close, closed-state response and unchanged fixture source');
  await client.close();
  const statePath = path.join(runtime, 'node_modules/.annotate-ready.json');
  const stamp = fs.statSync(statePath).mtimeMs;
  const warmTransport = new StdioClientTransport({ command: python, args: configuration.args, cwd: mcpDirectory, env: { ...environment, PATH: '/usr/bin:/bin' }, stderr: 'pipe' });
  let warmErrors = '';
  warmTransport.stderr.on('data', chunk => { warmErrors += chunk.toString(); });
  const warmClient = new Client({ name: 'annotate-warm-start', version: '1.0.0' }, { capabilities: {} });
  try {
    await warmClient.connect(warmTransport, { timeout: 30000 });
    assert.ok((await warmClient.listTools()).tools.some(tool => tool.name === 'annotate_open'));
    assert.equal(fs.statSync(statePath).mtimeMs, stamp);
    assert.ok(!warmErrors.includes('首次使用正在初始化'));
  } finally {
    await warmClient.close();
  }
  checks.push('second MCP startup reuses verified installation without npm reinstall');
  const report = { status: 'PASS', date: new Date().toISOString(), sourcePayload, installedPayload: payload, npmCache: environment.npm_config_cache, npmCacheInitiallyEmpty, discoveredNode, checks, evidenceDirectory: evidence, limitation: 'Automated development evidence only. Actual WorkSwarm UI/model invocation and explicit user test completion remain pending.' };
  fs.writeFileSync(path.join(evidence, 'integration-report.json'), JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 2));
} finally {
  await client.close().catch(() => {});
  await new Promise(resolve => server.close(resolve));
  fs.writeFileSync(path.join(evidence, 'runtime-stderr.log'), serverErrors);
}
