'use strict';

const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {readFileSync} = require('node:fs');
const {createInterface} = require('node:readline');
const {test} = require('node:test');
const {perform, TOOLS} = require('../src/trello-mcp.cjs');

const apiKey = 'test-api-key';
const apiToken = 'test-api-token';
const boardId = '50f8a79520ce617820000001';
const listId = '50f8a79520ce617820000002';
const cardId = '50f8a79520ce617820000003';
const otherBoard = '50f8a79520ce617820000009';
const basic = {id: cardId, name: '测试卡片 ＱＡ', idBoard: boardId, idList: listId,
  shortUrl: 'https://trello.com/c/fixture', closed: false, desc: '虚构内容'};
const abort = new AbortController().signal;

function run(name, args, handler, credentials = [apiKey, apiToken]) {
  return perform(name, args, ...credentials, abort, async (url, options) => {
    assert.equal(url.origin, 'https://api.trello.com');
    assert.equal(options.redirect, 'error');
    assert.equal(options.signal, abort);
    assert.equal(options.headers.Authorization, 'OAuth oauth_consumer_key="test-api-key", oauth_token="test-api-token"');
    assert.ok(!url.href.includes(apiToken) && !url.href.includes(apiKey));
    return handler(url, options);
  });
}

test('credential probe reads only the current member ID and returns a status', async () => {
  const result = await run('trello_status', {}, (url, opt) => {
    assert.equal(opt.method, 'GET');
    assert.equal(url.pathname, '/1/members/me');
    assert.equal(url.searchParams.get('fields'), 'id');
    return Response.json({id: 'fixture-user', email: 'fixture@example.test'});
  });
  assert.deepEqual(result, {connected: true});
});

test('filters current-user open boards by normalized name and keeps the next offset', async () => {
  const res = await run('trello_list_boards', {query: 'QA', limit: 1}, url => {
    assert.equal(url.pathname, '/1/members/me/boards');
    assert.equal(url.searchParams.get('filter'), 'open');
    return Response.json([
      {id: boardId, name: '看板ＱＡ', shortUrl: 'https://trello.com/b/fixture?token=untrusted', closed: false},
      {id: otherBoard, name: 'QA Next', closed: false},
      {id: 'archived', name: 'QA 归档', closed: true},
    ]);
  });
  assert.equal(res.next_offset, 1);
  assert.equal(res.matched, 2);
  assert.deepEqual(res.items[0], {id: boardId, name: '看板ＱＡ', url: 'https://trello.com/b/fixture'});
});

test('lists open lists and locally filtered card names without descriptions', async () => {
  const lists = await run('trello_list_lists', {board_id: boardId}, url => {
    assert.equal(url.pathname, '/1/boards/' + boardId + '/lists');
    return Response.json([{id: listId, name: '待办', closed: false}, {id: 'archived', name: '旧列表', closed: true}]);
  });
  assert.deepEqual(lists.items, [{id: listId, name: '待办'}]);
  const cards = await run('trello_list_cards', {list_id: listId, query: '测试卡片 QA'}, url => {
    assert.equal(url.pathname, '/1/lists/' + listId + '/cards');
    return Response.json([basic, {...basic, name: '无关'}]);
  });
  assert.equal(cards.matched, 1);
  assert.equal(cards.items[0].id, cardId);
  assert.ok(!Object.hasOwn(cards.items[0], 'description'));
});

test('reads a card by ID with only the requested detail fields', async () => {
  const result = await run('trello_get_card', {card_id: cardId}, url => {
    assert.equal(url.pathname, '/1/cards/' + cardId);
    assert.equal(url.searchParams.get('fields'), 'id,name,desc,idBoard,idList,closed,shortUrl');
    return Response.json({...basic, attachments: [{url: 'https://example.test'}]});
  });
  assert.equal(result.list_id, listId);
  assert.equal(result.description, basic.desc);
  assert.equal(result.url, basic.shortUrl);
  assert.ok(!Object.hasOwn(result, 'attachments'));
});

test('creates once in the verified matching open list and reads the new card independently', async () => {
  const args = {board_id: boardId, list_id: listId, name: basic.name, description: basic.desc};
  const calls = [];
  const handler = (url, options) => {
    calls.push([options.method, url.pathname]);
    if (url.pathname === '/1/lists/' + listId) return Response.json({id: listId, closed: false, idBoard: boardId});
    if (options.method === 'POST') {
      assert.deepEqual(JSON.parse(options.body), {idList: listId, name: basic.name, desc: basic.desc});
      return Response.json(basic);
    }
    return Response.json(basic);
  };
  const created = await run('trello_create_card', args, handler);
  assert.deepEqual(await run('trello_get_card', {card_id: created.id}, handler), created);
  assert.deepEqual(calls, [['GET', '/1/lists/' + listId], ['POST', '/1/cards'], ['GET', '/1/cards/' + cardId]]);
});

test('never attempts a write to a mismatching or closed list', async () => {
  for (const [parent, closed, pattern] of [[otherBoard, false, /其他看板/], [boardId, true, /归档/]]) {
    let writes = 0;
    await assert.rejects(run('trello_create_card', {board_id: boardId, list_id: listId, name: basic.name}, (url, opt) => {
      if (opt.method === 'POST') writes++;
      return Response.json({id: listId, idBoard: parent, closed});
    }), pattern);
    assert.equal(writes, 0);
  }
});

test('refuses invalid IDs, unsupported writes and missing credentials before HTTP', async () => {
  const never = () => assert.fail('Unexpected request');
  await assert.rejects(run('trello_get_card', {card_id: '../members/me'}, never), /格式无效/);
  await assert.rejects(run('trello_create_card', {board_id: boardId, list_id: listId, name: 'QA', due: '2027'}, never), /不受支持/);
  await assert.rejects(run('trello_status', {}, never, [undefined, undefined]), /卡片填写/);
  await assert.rejects(run('trello_status', {}, never, [apiKey, 'line\nbreak']), /格式无效/);
});

test('handles auth errors, limits, and indeterminate create without exposing provider text or retrying', async () => {
  for (const [status, expected] of [[401, /重新连接/], [403, /没有访问/], [404, /无法找到/], [429, /频繁/]]) {
    await assert.rejects(run('trello_status', {}, () => new Response(apiToken, {status})),
      e => expected.test(e.message) && !e.message.includes(apiToken));
  }
  let posts = 0;
  await assert.rejects(run('trello_create_card', {board_id: boardId, list_id: listId, name: basic.name}, (url, opt) => {
    if (opt.method === 'GET') return Response.json({id: listId, idBoard: boardId, closed: false});
    posts++;
    throw new Error(apiToken);
  }), e => /先在目标列表查同名/.test(e.message) && !e.message.includes(apiToken));
  assert.equal(posts, 1);
});

test('matches packaged entry code and exposes exactly six tools over stdio', {timeout: 5000}, async t => {
  const config = require('../trello/mcp.json').mcpServers.trello;
  assert.equal(config.args[1], readFileSync(require.resolve('../src/trello-mcp.cjs'), 'utf8'));
  assert.equal(config.env.TRELLO_API_KEY, '$' + '{TRELLO_API_KEY}');
  assert.equal(config.env.TRELLO_API_TOKEN, '$' + '{TRELLO_API_TOKEN}');
  const env = {...process.env};
  delete env.TRELLO_API_KEY;
  delete env.TRELLO_API_TOKEN;
  const child = spawn(process.execPath, config.args, {env, stdio: ['pipe', 'pipe', 'inherit']});
  t.after(() => child.kill());
  const lines = createInterface({input: child.stdout})[Symbol.asyncIterator]();
  async function rpc(id, method, params) {
    child.stdin.write(JSON.stringify({jsonrpc: '2.0', id, method, params}) + '\n');
    const response = JSON.parse((await lines.next()).value);
    assert.equal(response.id, id);
    return response.result;
  }
  assert.deepEqual((await rpc(1, 'initialize', {protocolVersion: '2024-11-05'})).serverInfo,
    {name: 'trello', version: '1.0.0'});
  assert.deepEqual((await rpc(2, 'tools/list')).tools, TOOLS);
  const result = await rpc(3, 'tools/call', {name: 'trello_status'});
  assert.equal(result.isError, true);
  assert.match(result.content[0].text, /卡片填写/);
  child.stdin.end();
});
