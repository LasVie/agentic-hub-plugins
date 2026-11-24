'use strict';

const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { readFileSync } = require('node:fs');
const { createInterface } = require('node:readline');
const { test } = require('node:test');
const { perform, TOOLS } = require('../src/fathom-mcp.cjs');

const key = 'unit-test-key';
const signal = new AbortController().signal;
const data = {
  items: [
    {recording_id: 17, title: '会议验收 ＱＡ', url: 'https://fathom.video/test', calendar_invitees: [{email: 'fixture@example.net'}]},
    {recording_id: 18, title: '无关会议'},
  ],
  next_cursor: 'e2==',
};

function fake(handler) {
  return async (url, options) => {
    assert.equal(url.origin, 'https://api.fathom.ai');
    assert.equal(options.method, 'GET');
    assert.equal(options.redirect, 'error');
    assert.equal(options.headers['X-Api-Key'], key);
    assert.equal(options.signal, signal);
    return handler(url);
  };
}

test('checks the authenticated meeting list without returning data', async () => {
  assert.deepEqual(await perform('fathom_status', {}, key, signal, fake(url => {
    assert.equal(url.pathname, '/external/v1/meetings');
    return Response.json(data);
  })), {connected: true});
});

test('filters the current title page, normalizes dates and preserves the provider cursor', async () => {
  const result = await perform('fathom_search_meetings', {
    query: '验收 qa', created_after: '2026-11-23T18:00:00+08:00', created_before: '2026-11-25', cursor: 'e1+=',
  }, key, signal, fake(url => {
    assert.equal(url.pathname, '/external/v1/meetings');
    assert.deepEqual(Object.fromEntries(url.searchParams), {
      created_after: '2026-11-23T10:00:00.000Z', created_before: '2026-11-25T00:00:00.000Z', cursor: 'e1+=',
    });
    return Response.json(data);
  }));
  assert.deepEqual(result.meetings.map(m => m.recording_id), ['17']);
  assert.equal(result.next_cursor, 'e2==');
  assert.ok(!JSON.stringify(result).includes('fixture@example.net'));
});

test('preserves a usable next page when current page has no match', async () => {
  const result = await perform('fathom_search_meetings', {query: '无此记录'}, key, signal, fake(() => Response.json(data)));
  assert.deepEqual(result, {meetings: [], scanned: 2, next_cursor: 'e2=='});
  const absent = await perform('fathom_search_meetings', {query: '无此记录', cursor: 'e2=='}, key, signal,
    fake(() => Response.json({items: [], next_cursor: null})));
  assert.deepEqual(absent, {meetings: [], scanned: 0, next_cursor: null});
});

test('fetches an existing summary by ID without callback parameters', async () => {
  const result = await perform('fathom_read_summary', {recording_id: '17'}, key, signal, fake(url => {
    assert.equal(url.pathname, '/external/v1/recordings/17/summary');
    assert.equal(url.search, '');
    return Response.json({summary: {template_name: null, markdown_formatted: '# 决策\n选用蓝色笔记本。'}});
  }));
  assert.deepEqual(result, {recording_id: '17', available: true, summary: '# 决策\n选用蓝色笔记本。'});
});

test('retains summary text while removing generated recording share URLs', async () => {
  const summary = '- [**决定：** 蓝色笔记本。](https://fathom.video/share/demo-key?timestamp=90.0)\n' +
    '- <https://fathom.video/share/demo-key>\n- [Fathom 文档](https://developers.fathom.ai)';
  const result = await perform('fathom_read_summary', {recording_id: '17'}, key, signal,
    fake(() => Response.json({summary: {markdown_formatted: summary}})));
  assert.match(result.summary, /\*\*决定：\*\* 蓝色笔记本。/u);
  assert.match(result.summary, /\[Fathom 文档\]\(https:\/\/developers\.fathom\.ai\)/u);
  assert.doesNotMatch(result.summary, /demo-key/u);
});

test('keeps original transcript text and time data while paging without invitee email', async () => {
  const transcript = [0, 1, 2].map(i => ({
    text: '测试 ' + i,
    timestamp: '00:00:0' + i,
    speaker: {display_name: '测试人', matched_calendar_invitee_email: 'fixture@example.net'},
  }));
  const call = fake(url => {
    assert.equal(url.pathname, '/external/v1/recordings/17/transcript');
    assert.equal(url.search, '');
    return Response.json({transcript});
  });
  const first = await perform('fathom_read_transcript', {recording_id: '17', limit: 2}, key, signal, call);
  const last = await perform('fathom_read_transcript', {recording_id: '17', offset: first.next_offset}, key, signal, call);
  assert.deepEqual(first.segments[0], {speaker: '测试人', text: '测试 0', timestamp: '00:00:00'});
  assert.equal(first.total, 3);
  assert.equal(first.next_offset, 2);
  assert.equal(last.segments[0].text, '测试 2');
  assert.equal(last.next_offset, null);
  assert.ok(!JSON.stringify(first).includes('fixture@example.net'));
});

test('rejects arbitrary paths, unsupported parameters and invalid date or pagination before HTTP', async () => {
  const never = () => assert.fail('Unexpected HTTP request');
  await assert.rejects(perform('fathom_read_summary', {recording_id: '../99'}, key, signal, never), /格式无效/);
  await assert.rejects(perform('fathom_read_summary', {recording_id: '99', destination_url: 'https://example.net'}, key, signal, never), /不支持/);
  await assert.rejects(perform('fathom_read_transcript', {recording_id: '99', offset: -1}, key, signal, never), /超出/);
  await assert.rejects(perform('fathom_search_meetings', {created_before: '2026-02-30'}, key, signal, never), /日期无效/);
  await assert.rejects(perform('fathom_search_meetings', {created_after: '2026-02-28', created_before: '2026-02-28'}, key, signal, never), /晚于/);
  await assert.rejects(perform('fathom_status', {}, '', signal, never), /填写 API Key/);
});

test('handles unauthorized, forbidden, rate limits and transport failures without echoing raw responses', async () => {
  for (const [status, pattern] of [[401, /无效/], [403, /拒绝访问/], [404, /无法读取/], [429, /频繁/], [503, /暂时/]]) {
    await assert.rejects(
      perform('fathom_status', {}, key, signal, fake(() => new Response(key, {status}))),
      err => pattern.test(err.message) && !err.message.includes(key)
    );
  }
  await assert.rejects(perform('fathom_status', {}, key, signal, () => { throw new Error(key); }),
    err => err.message.includes('网络') && !err.message.includes(key));
});

test('distinguishes unprocessed recordings and unexpected data shapes', async () => {
  assert.deepEqual(await perform('fathom_read_summary', {recording_id: '17'}, key, signal,
    fake(() => Response.json({summary: null}))), {recording_id: '17', available: false});
  assert.deepEqual(await perform('fathom_read_transcript', {recording_id: '17'}, key, signal,
    fake(() => Response.json({transcript: []}))),
  {recording_id: '17', available: false, total: 0, offset: 0, segments: [], next_offset: null});
  await assert.rejects(perform('fathom_status', {}, key, signal, fake(() => Response.json({}))), /缺少会议列表/);
  await assert.rejects(perform('fathom_status', {}, key, signal, fake(() => new Response('not json'))), /无法读取/);
});

test('runs the exact packaged Node entry point and discovers tools over stdio', {timeout: 5000}, async t => {
  const config = require('../fathom/mcp.json').mcpServers.fathom;
  assert.equal(config.args[1], readFileSync(require.resolve('../src/fathom-mcp.cjs'), 'utf8'));
  assert.equal(config.env.FATHOM_API_KEY, '$' + '{FATHOM_API_KEY}');
  const env = {...process.env};
  delete env.FATHOM_API_KEY;
  const child = spawn(process.execPath, config.args, {env, stdio: ['pipe', 'pipe', 'inherit']});
  t.after(() => child.kill());
  const lines = createInterface({input: child.stdout})[Symbol.asyncIterator]();
  async function rpc(id, method, params) {
    child.stdin.write(JSON.stringify({jsonrpc: '2.0', id, method, params}) + '\n');
    const line = await lines.next();
    const output = JSON.parse(line.value);
    assert.equal(output.id, id);
    return output.result;
  }
  const init = await rpc(1, 'initialize', {protocolVersion: '2024-11-05'});
  const {version} = require('../fathom/manifest.json');
  assert.deepEqual(init.serverInfo, {name: 'fathom', version});
  assert.deepEqual((await rpc(2, 'tools/list')).tools, TOOLS);
  const status = await rpc(3, 'tools/call', {name: 'fathom_status'});
  assert.equal(status.isError, true);
  assert.match(status.content[0].text, /卡片填写 API Key/);
  child.stdin.end();
});
