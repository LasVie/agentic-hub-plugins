import assert from 'node:assert/strict';
import { mkdtemp, readFile, readdir, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const sdkRoot = process.env.RSS_TEST_MCP_SDK;
assert(sdkRoot, '请通过 RSS_TEST_MCP_SDK 指定已有 MCP SDK 的 dist/esm 目录；本脚本不会安装依赖');
const { Client } = await import(pathToFileURL(path.join(sdkRoot, 'client/index.js')));
const { StdioClientTransport } = await import(pathToFileURL(path.join(sdkRoot, 'client/stdio.js')));
const payload = path.resolve(process.argv[2]);
const live = process.argv.includes('--live');
const stateRoot = await mkdtemp(path.join(tmpdir(), 'rss-mcp-smoke-'));
const connections = [];
let assertions = 0;

async function connect() {
  const configuration = JSON.parse(await readFile(path.join(payload, 'mcps/rss-daily/mcp.json'), 'utf8')).mcpServers['rss-daily'];
  const transport = new StdioClientTransport({
    command: configuration.command,
    args: configuration.args,
    cwd: path.join(payload, 'mcps/rss-daily'),
    env: { ...process.env, RSS_DAILY_STATE_DIR: stateRoot, PYTHONDONTWRITEBYTECODE: '1' },
    stderr: 'pipe',
  });
  const client = new Client({ name: 'rss-daily-independent-smoke', version: '1.0.0' });
  await client.connect(transport);
  connections.push(client);
  const tools = (await client.listTools()).tools;
  assert.equal(tools.length, 5);
  assertions += 1;
  return client;
}

async function call(client, name, argumentsValue = {}) {
  const response = await client.callTool({ name, arguments: argumentsValue });
  return { result: JSON.parse(response.content[0].text), isError: Boolean(response.isError) };
}

async function ready(client, mode) {
  for (let attempt = 0; attempt < 150; attempt += 1) {
    const { result } = await call(client, 'rss_status', { mode });
    if (result.phase !== 'RUNNING') return result;
    await new Promise(resolve => setTimeout(resolve, live ? 500 : 50));
  }
  throw new Error('状态等待超时');
}

try {
  const client = await connect();
  const other = await connect();
  assert.equal((await call(client, 'rss_status', { mode: 'demo' })).result.phase, 'IDLE');
  assertions += 1;
  const starts = await Promise.all([client, other].map(connection => call(connection, 'rss_fetch', { mode: 'demo' })));
  assert.equal(starts[0].result.batch_id, starts[1].result.batch_id);
  assertions += 1;
  const draft = await ready(client, 'demo');
  assert.equal(draft.phase, 'DRAFT');
  assert.equal(draft.items.length, 3);
  assert.match(draft.data_kind, /非实时新闻/);
  assertions += 3;
  const early = await call(client, 'rss_confirm', { mode: 'demo', batch_id: draft.batch_id });
  assert.equal(early.isError, true);
  assertions += 1;
  const wrong = await call(client, 'rss_finalize', { mode: 'demo', batch_id: draft.batch_id,
    items: [{ id: 'forged', title: '伪造条目', summary: '必须拒绝无对应素材的摘要' }] });
  assert.equal(wrong.isError, true);
  assertions += 1;
  const finalized = (await call(client, 'rss_finalize', { mode: 'demo', batch_id: draft.batch_id,
    items: draft.items.map(item => ({ id: item.id, title: item.title, summary: item.excerpt })) })).result;
  assert.equal(finalized.phase, 'FINALIZED');
  assert.equal(finalized.history_count, 0);
  for (const item of draft.items) assert(finalized.markdown.includes(item.url));
  assertions += 5;
  const confirmations = await Promise.all([client, other].map(connection => call(connection, 'rss_confirm', { mode: 'demo', batch_id: draft.batch_id })));
  assert.equal(confirmations[0].result.history_count, 3);
  assert.equal(confirmations[1].result.confirmed_at, confirmations[0].result.confirmed_at);
  assertions += 2;
  await client.close();
  const restarted = await connect();
  assert.equal((await call(restarted, 'rss_status', { mode: 'demo' })).result.phase, 'CONFIRMED');
  await call(restarted, 'rss_fetch', { mode: 'demo', force: true });
  const empty = await ready(restarted, 'demo');
  assert.equal(empty.phase, 'EMPTY');
  assert.equal(empty.history_count, 3);
  assert.equal(empty.items.length, 0);
  assert.equal((await call(restarted, 'rss_status', { mode: 'live' })).result.history_count, 0);
  assertions += 5;
  const demoFiles = await readdir(path.join(stateRoot, 'demo'));
  assert.deepEqual(demoFiles.sort(), ['state.json', 'state.lock']);
  assertions += 1;
  if (live) {
    const start = await call(restarted, 'rss_fetch', { mode: 'live', hours: 168 });
    assert.equal(start.result.phase, 'RUNNING');
    const actual = await ready(restarted, 'live');
    console.log(JSON.stringify({ 实网状态: actual.phase, 素材数: actual.items?.length ?? 0, 来源结果: actual.source_results, 错误: actual.error }, null, 2));
    assert.equal(actual.phase, 'DRAFT', '真实公开网络必须实际返回候选素材才能计为通过');
    assert(actual.items.length > 0);
    assert.equal(actual.history_count, 0);
    assertions += 4;
  }
  console.log(JSON.stringify({ 结果: '通过', 版本: '1.0.0', 断言数: assertions, 载荷: payload, 实际宿主界面测试: '等待用户在 WorkSwarm 中执行' }, null, 2));
} finally {
  await Promise.allSettled(connections.map(client => client.close()));
  await rm(stateRoot, { recursive: true, force: true });
}
