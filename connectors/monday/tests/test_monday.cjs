'use strict';

const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {test} = require('node:test');
const {perform, TOOLS} = require('../src/monday-mcp.cjs');
const config = require('../monday/mcp.json').mcpServers.monday;

const token = 'fixture-token-stays-in-header';
const board = '5032516681';
const entry = {id: '2910613877', name: '验收条目', board: {id: board}, url: 'https://qa.monday.com/boards/5032516681/pulses/2910613877?tracking=hidden'};
const respond = value => new Response(JSON.stringify(value), {headers: {'Content-Type': 'application/json'}});
const call = (name, args, request, secret = token) => perform(name, args, secret, AbortSignal.timeout(3000), request);

test('uses the fixed HTTPS endpoint and API version, and keeps the token out of output', async () => {
  const result = await call('monday_status', {}, async (url, init) => {
    assert.equal(url, 'https://api.monday.com/v2');
    assert.equal(init.method, 'POST');
    assert.equal(init.redirect, 'error');
    assert.deepEqual(init.headers, {Authorization: token, 'Content-Type': 'application/json', 'API-Version': '2026-10'});
    assert.doesNotMatch(init.body, new RegExp(token));
    return respond({data: {me: {id: '9'}}});
  });
  assert.deepEqual(result, {connected: true, api_version: '2026-10'});
});

test('lists a specified board and returns its opaque next-page cursor', async () => {
  const result = await call('monday_list_board_items', {board_id: board, limit: 1}, async (_, init) => {
    const sent = JSON.parse(init.body);
    assert.match(sent.query, /items_page\(limit:/u);
    assert.doesNotMatch(sent.query, /subitem_columns/u);
    assert.deepEqual(sent.variables, {board, limit: 1});
    return respond({data: {boards: [{id: board, name: '验收看板', items_page: {cursor: 'next', items: [entry]}}]}});
  });
  assert.equal(result.board_name, '验收看板');
  assert.equal(result.next_cursor, 'next');
  assert.equal(result.items[0].title, '验收条目');
  assert.equal(result.items[0].url, entry.url.split('?')[0]);
});

test('validates cursor result board and rejects a cross-board page', async () => {
  const args = {board_id: board, cursor: 'encoded="cursor"', limit: 5};
  const sendPage = async (_, init) => {
    const {query, variables} = JSON.parse(init.body);
    assert.match(query, /next_items_page/u);
    assert.deepEqual(variables, {cursor: args.cursor, limit: 5});
    return respond({data: {next_items_page: {cursor: null, items: [entry]}}});
  };
  assert.equal((await call('monday_list_board_items', args, sendPage)).items[0].board_id, board);
  await assert.rejects(call('monday_list_board_items', {...args, board_id: '123'}, sendPage), /看板不一致/u);
});

test('reads a specific item and checks the supplied board', async () => {
  const request = async (_, init) => {
    assert.deepEqual(JSON.parse(init.body).variables, {item: entry.id});
    return respond({data: {items: [{...entry, url: 'https://monday.com.example.org/test', column_values: [{id: 'status', text: '已完成'}, {id: 'formula', text: null}]}]}});
  };
  const found = await call('monday_read_item', {item_id: entry.id, board_id: board}, request);
  assert.deepEqual(found.columns, [{id: 'status', text: '已完成'}, {id: 'formula', text: null}]);
  assert.equal(found.url, null);
  await assert.rejects(call('monday_read_item', {item_id: entry.id, board_id: '2'}, request), /无法访问/u);
});

test('creates once, sending the title as a variable, and independently reads it back', async () => {
  const title = '新建“带引号”的条目';
  const requested = [];
  const send = async (_, init) => {
    const operation = JSON.parse(init.body);
    requested.push(operation);
    const created = {...entry, name: title};
    return respond({data: requested.length === 1 ? {create_item: created} : {items: [created]}});
  };
  const created = await call('monday_create_item', {board_id: board, title}, send);
  assert.equal(created.title, title);
  const read = await call('monday_read_item', {item_id: created.id, board_id: board}, send);
  assert.equal(read.id, created.id);
  assert.match(requested[0].query, /^mutation CreateItem/u);
  assert.deepEqual(requested[0].variables, {board, title});
  assert.deepEqual(requested[1].variables, {item: created.id});
  assert.equal(requested.length, 2);
});

test('returns a write uncertainty error after a timeout or a partial creation response', async () => {
  for (const request of [
    async () => { throw new Error('PRIVATE response'); },
    async () => respond({data: {create_item: entry}, errors: [{message: 'PRIVATE response'}]}),
    async () => respond({data: {create_item: {...entry, board: {id: '2'}}}}),
  ]) {
    let attempts = 0;
    await assert.rejects(call('monday_create_item', {board_id: board, title: entry.name}, (...args) => {
      attempts++;
      return request(...args);
    }), error => /创建结果未确认/u.test(error.message) && !error.message.includes('PRIVATE'));
    assert.equal(attempts, 1);
  }
});

test('distinguishes missing or denied access from provider payloads', async () => {
  await assert.rejects(call('monday_status', {}, async () => new Response('PRIVATE', {status: 401})), /无法验证访问令牌/u);
  await assert.rejects(call('monday_list_board_items', {board_id: board}, async () => respond({
    data: {boards: []},
    errors: [{message: token, extensions: {code: 'UserUnauthorizedException', status_code: 403}}],
  })), error => /拒绝访问/u.test(error.message) && !error.message.includes(token));
  await assert.rejects(call('monday_list_board_items', {board_id: board}, async () => respond({data: {boards: []}})), /找不到目标/u);
});

test('rejects unapproved operations, invalid input and missing credentials before using the network', async () => {
  const unexpected = () => assert.fail('invalid input should not call GraphQL');
  await assert.rejects(call('monday_delete_item', {}, unexpected), /仅提供/u);
  await assert.rejects(call('monday_create_item', {board_id: board, title: '  '}, unexpected), /格式或范围无效/u);
  await assert.rejects(call('monday_list_board_items', {board_id: 100}, unexpected), /格式或范围无效/u);
  await assert.rejects(call('monday_status', {}, unexpected, ''), /卡片填写/u);
  await assert.rejects(call('monday_status', {}, unexpected, 'copied@example.com'), /令牌格式无效/u);
});

test('the exact mcp.json argv starts stdio and declares only the four expected tools', () => {
  const messages = [
    {id: 1, method: 'initialize', params: {protocolVersion: '2024-11-05'}},
    {method: 'notifications/initialized'},
    {id: 2, method: 'tools/list'},
    {id: 3, method: 'tools/call', params: {name: 'monday_status', arguments: {}}},
  ];
  const run = spawnSync(process.execPath, config.args, {
    input: messages.map(message => JSON.stringify({jsonrpc: '2.0', ...message})).join('\n') + '\n',
    env: {...process.env, MONDAY_PERSONAL_TOKEN: ''},
    encoding: 'utf8', timeout: 5000,
  });
  assert.equal(run.status, 0);
  assert.equal(run.stderr, '');
  const [hello, tools, status] = run.stdout.trim().split('\n').map(line => JSON.parse(line));
  assert.deepEqual(hello.result.serverInfo, {name: 'monday', version: '1.1.0'});
  assert.deepEqual(tools.result.tools, TOOLS);
  assert.equal(status.result.isError, true);
  assert.match(status.result.content[0].text, /卡片填写/u);
});
