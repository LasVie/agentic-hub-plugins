'use strict';

const assert = require('node:assert/strict');
const {test} = require('node:test');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const src = '../intercom/skills/intercom-guide/scripts/';
const {readArguments} = require(src + 'intercom-cli.cjs');
const {login, logout, useSession} = require(src + 'intercom-auth.cjs');
const {readResponse, checkTools, readTool} = require(src + 'intercom-mcp.cjs');

test('accepts Chinese conversation search and contact lookup', () => {
  for (const query of ['object_type:conversations source_body:contains:"核对标记" limit:5', 'object_type:contacts email_domain:"example.com"']) {
    assert.deepEqual(readArguments('search', {query}), {query});
  }
  assert.deepEqual(readArguments('fetch', {id: 'contact_2ac9f5'}), {id: 'contact_2ac9f5'});
});

test('rejects unrelated objects, URLs and extra arguments before network', async () => {
  for (const bad of [{query: 'object_type:articles'}, {query: 'object_type:contacts', email: 'x'}]) {
    assert.throws(() => readArguments('search', bad), {code: 'BAD_ARGUMENTS'});
  }
  assert.throws(() => readArguments('fetch', {id: 'https://example.org/123'}), {code: 'BAD_ARGUMENTS'});
  await assert.rejects(() => readTool(() => assert.fail(), 'create_article', {}), {code: 'BAD_ARGUMENTS'});
});

test('accepts matching JSON-RPC SSE result and ignores other message IDs', async () => {
  const stream = new Response('data: {"jsonrpc":"2.0","id":9,"result":{}}\r\n\r\n' +
    'event: message\r\ndata: {"jsonrpc":"2.0","id":1,"result":{"content":"中文"}}\r\n\r\n',
    {headers: {'content-type': 'text/event-stream'}});
  assert.deepEqual((await readResponse(stream, 1)).result, {content: '中文'});
});

test('supports paginated discovery using only official search and fetch', async () => {
  const cursors = [];
  await checkTools(async (op, params) => {
    assert.equal(op, 'tools/list');
    cursors.push(params.cursor);
    return params.cursor ? {tools: [{name: 'fetch'}]} : {tools: [{name: 'search'}, {name: 'write'}], nextCursor: 'page-2'};
  });
  assert.deepEqual(cursors, [undefined, 'page-2']);
});

test('loopback auth links PKCE to callback, verifies tools and refreshes before read', async t => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'intercom-auth-test-'));
  t.after(() => fs.rmSync(dir, {recursive: true, force: true}));
  const realFetch = globalThis.fetch;
  const requests = [];
  let authorize, registered;
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    if (String(url).startsWith('http://127.0.0.1:')) return realFetch(url, options);
    const remote = new URL(url);
    assert.equal(remote.origin, 'https://mcp.eu.intercom.com');
    if (remote.pathname === '/register') {
      registered = JSON.parse(options.body);
      assert.equal(registered.token_endpoint_auth_method, 'none');
      return Response.json({...registered, client_id: 'fixture-client'}, {status: 201});
    }
    if (remote.pathname === '/token') {
      if (options.body.get('grant_type') === 'authorization_code') {
        assert.equal(options.body.get('code'), 'fixture-code');
        assert.equal(options.body.get('redirect_uri'), registered.redirect_uris[0]);
        const hash = crypto.createHash('sha256').update(options.body.get('code_verifier')).digest('base64url');
        assert.equal(authorize.searchParams.get('code_challenge'), hash);
        return Response.json({access_token: 'test-first', token_type: 'Bearer', refresh_token: 'test-refresh', expires_in: 1});
      }
      assert.equal(options.body.get('refresh_token'), 'test-refresh');
      return Response.json({access_token: 'test-next', token_type: 'Bearer', expires_in: 500});
    }
    assert.equal(remote.pathname, '/mcp');
    if (options.method === 'DELETE') return new Response(null, {status: 204});
    const body = JSON.parse(options.body);
    requests.push(body);
    if (body.method === 'initialize') {
      return Response.json({jsonrpc:'2.0', id:body.id, result:{capabilities:{tools:{}}, protocolVersion:'2025-06-18'}},
        {headers:{'Mcp-Session-Id':'test-session'}});
    }
    assert.equal(options.headers['Mcp-Session-Id'], 'test-session');
    assert.equal(options.headers['MCP-Protocol-Version'], '2025-06-18');
    if (body.method === 'notifications/initialized') return new Response(null, {status: 202});
    if (body.method === 'tools/list') return Response.json({jsonrpc:'2.0', id:body.id, result:{tools:[{name:'search'}, {name:'fetch'}]}});
    assert.equal(body.params.name, 'fetch');
    assert.equal(options.headers.Authorization, 'Bearer test-next');
    return Response.json({jsonrpc:'2.0', id:body.id, result:{structuredContent:{title:'虚构测试会话'}}});
  });

  let showUrl;
  const entry = new Promise(r => { showUrl = r; });
  const auth = login(dir, showUrl);
  const url = await entry;
  const page = await fetch(url).then(r => r.text());
  assert.match(page, /连接欧区/);
  assert.equal((await fetch(url + '/eu', {headers:{'Sec-Fetch-Site':'cross-site'}, redirect:'manual'})).status, 403);
  const redirect = await fetch(url + '/eu', {redirect:'manual'});
  assert.equal(redirect.status, 303);
  authorize = new URL(redirect.headers.get('location'));
  assert.equal(authorize.pathname, '/authorize');
  const callback = new URL(authorize.searchParams.get('redirect_uri'));
  callback.search = new URLSearchParams({state:'wrong', code:'fixture-code'});
  assert.equal((await fetch(callback)).status, 404);
  callback.searchParams.set('state', authorize.searchParams.get('state'));
  assert.match(await fetch(callback).then(r => r.text()), /授权已完成/);
  assert.equal(await auth, 'eu');
  assert.deepEqual(await useSession(dir, rpc => readTool(rpc, 'fetch', {id:'conversation_123'})), {title:'虚构测试会话'});
  assert.deepEqual(requests.map(r => r.method), ['initialize', 'notifications/initialized', 'tools/list', 'initialize', 'notifications/initialized', 'tools/call']);
  await logout(dir);
  assert.equal(fs.readFileSync(path.join(dir, 'session.json'), 'utf8').includes('test-refresh'), false);
  await assert.rejects(() => useSession(dir, checkTools), {code:'AUTH_REQUIRED'});
});
