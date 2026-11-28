'use strict';

const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {test} = require('node:test');
const root = '../outlook-work-calendar/skills/outlook-work-calendar-guide/scripts/';
const graph = require(root + 'graph.cjs');
const {login, accessToken} = require(root + 'outlook-cli.cjs');
const store = require(root + 'storage.cjs');

const config = {
  tenant: 'dad710cd-4b5b-4810-9526-7d5587f7cbf1',
  client: '80e9456b-cccf-4044-a045-83c7ac66d3f3',
};
const range = {from: '2026-11-24T09:00:00+08:00', to: '2026-11-26T09:00:00+08:00'};
const token = {
  access_token: 'qa-access', refresh_token: 'qa-refresh', expires_in: 3600,
  scope: 'Calendars.ReadBasic',
};
const event = {
  id: 'AAMkQA==', subject: '周会 ＱＡ', isAllDay: false, isCancelled: false,
  start: {dateTime: '2026-11-24T02:00:00.0000000', timeZone: 'UTC'},
  end: {dateTime: '2026-11-24T02:30:00.0000000', timeZone: 'UTC'},
  location: {displayName: '虚构会议室'},
  body: {content: 'exclude me'}, attendees: [{emailAddress: {address: 'fixture@example.test'}}],
};

function fixtureDirectory(t) {
  const dir = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'outlook-work-qa-'));
  const before = process.env.JIUWENSWARM_DATA_DIR;
  process.env.JIUWENSWARM_DATA_DIR = dir;
  t.after(() => {
    if (before === undefined) delete process.env.JIUWENSWARM_DATA_DIR;
    else process.env.JIUWENSWARM_DATA_DIR = before;
    fs.rmSync(dir, {force: true, recursive: true});
  });
}

test('uses the documented Microsoft tenant endpoint, PKCE and only the selected scopes', () => {
  const url = graph.authorizationUrl(config, {
    redirect: 'http://localhost:48771/', state: 'fixture-state', challenge: 'fixture-challenge',
  });
  assert.equal(url.origin, 'https://login.microsoftonline.com');
  assert.equal(url.pathname, '/' + config.tenant + '/oauth2/v2.0/authorize');
  assert.equal(url.searchParams.get('response_type'), 'code');
  assert.equal(url.searchParams.get('scope'), 'offline_access https://graph.microsoft.com/Calendars.ReadBasic');
  assert.equal(url.searchParams.get('code_challenge_method'), 'S256');
  assert.throws(() => graph.clientConfig('consumers', config.client), {code: 'INVALID_CLIENT'});
});

test('calendar view preserves date bounds, limits fields and filters only the current page', async () => {
  const req = graph.listRequest({...range, query: 'qa', limit: 11});
  assert.equal(req.url.pathname, '/v1.0/me/calendar/calendarView');
  assert.equal(req.url.searchParams.get('startDateTime'), '2026-11-24T01:00:00.000Z');
  assert.equal(req.url.searchParams.get('$top'), '11');
  assert.doesNotMatch(req.url.searchParams.get('$select'), /body|attendees/u);
  const res = await graph.list(req, token.access_token, async (url, opts) => {
    assert.equal(url.origin, 'https://graph.microsoft.com');
    assert.equal(opts.method, 'GET');
    assert.equal(opts.redirect, 'error');
    assert.equal(opts.headers.Authorization, 'Bearer qa-access');
    return Response.json({value: [event, {...event, subject: '另一个日程'}]});
  });
  assert.equal(res.events[0].title, '周会 ＱＡ');
  assert.equal(res.events[0].location, '虚构会议室');
  assert.equal(res.scanned, 2);
  assert.equal(res.events.length, 1);
  assert.doesNotMatch(JSON.stringify(res), /fixture@example|exclude me/u);
});

test('follows the returned cursor only for the same time window and calendar route', async () => {
  const req = graph.listRequest(range);
  const cursor = new URL(req.url);
  cursor.searchParams.set('$skip', '25');
  const first = await graph.list(req, token.access_token, async () => Response.json({value: [], '@odata.nextLink': cursor.href}));
  assert.equal(first.next_cursor, cursor.href);
  assert.equal(graph.listRequest({...range, cursor: first.next_cursor}).url.href, cursor.href);
  for (const value of [cursor.href.replace('graph.microsoft.com', 'example.test'),
       cursor.href.replace('/me/calendar/calendarView', '/me/messages'),
       cursor.href.replace('2026-11-24', '2026-11-23'),
       cursor.href + '&%24expand=attachments']) {
    assert.throws(() => graph.listRequest({...range, cursor: value}), {code: 'BAD_CURSOR'});
  }
});

test('checks dates and reads the event ID in the default calendar only', async () => {
  assert.throws(() => graph.listRequest({from: '2026-02-30T00:00:00Z', to: range.to}), {code: 'BAD_ARGUMENTS'});
  assert.throws(() => graph.listRequest({...range, to: range.from}), {code: 'BAD_ARGUMENTS'});
  assert.throws(() => graph.listRequest({from: '2026-01-01T00:00:00Z', to: range.to}), {code: 'BAD_ARGUMENTS'});
  assert.throws(() => graph.detailRequest({event_id: '../../me/messages'}), {code: 'BAD_ARGUMENTS'});
  const url = graph.detailRequest({event_id: event.id});
  assert.equal(url.pathname, '/v1.0/me/calendar/events/AAMkQA%3D%3D');
  const detail = await graph.graph(url, token.access_token, async () => Response.json(event));
  assert.equal(graph.record(detail).from.time_zone, 'UTC');
});

test('handles authorization, missing mailboxes and throttling without provider error details', async () => {
  const req = graph.listRequest(range);
  for (const [status, result] of [[401, 'AUTH_REQUIRED'], [403, 'ACCESS_DENIED'],
       [404, 'MAILBOX_UNAVAILABLE'], [429, 'RATE_LIMIT'], [502, 'SERVICE_ERROR']]) {
    await assert.rejects(graph.graph(req.url, token.access_token, async () =>
      Response.json({error: {message: token.access_token}}, {status})),
    error => error.code === result && !error.message.includes(token.access_token));
  }
  await assert.rejects(graph.exchange(config, {grant_type: 'authorization_code', code: 'fixture'}, async () =>
    Response.json({...token, scope: 'Mail.Read'})), {code: 'ACCESS_DENIED'});
});

async function begin(t, request) {
  fixtureDirectory(t);
  let show;
  const ready = new Promise(resolve => { show = resolve; });
  const result = login({request, announce: show, timeout: 5000});
  result.catch(() => {});
  const entry = await ready;
  const form = await fetch(entry);
  assert.match(await form.text(), /目录（租户）ID/u);
  const invalid = await fetch(entry + '/configure', {
    method: 'POST', body: new URLSearchParams({...config, tenant: 'consumers'}),
  });
  assert.equal(invalid.status, 400);
  const saved = await fetch(entry + '/configure', {
    method: 'POST', body: new URLSearchParams(config), redirect: 'manual',
  });
  assert.equal(saved.status, 303);
  const start = await fetch(entry + '/authorize', {redirect: 'manual'});
  assert.equal(start.status, 302);
  return {result, auth: new URL(start.headers.get('location'))};
}

test('exchanges the real loopback form and validates state, PKCE and Graph before storing', async t => {
  let auth;
  let requests = 0;
  const run = await begin(t, async (url, options) => {
    requests++;
    if (url.origin === 'https://login.microsoftonline.com') {
      assert.equal(options.body.get('grant_type'), 'authorization_code');
      assert.equal(options.body.get('code'), 'fixture-code');
      assert.equal(options.body.has('client_secret'), false);
      const challenge = crypto.createHash('sha256').update(options.body.get('code_verifier')).digest('base64url');
      assert.equal(challenge, auth.searchParams.get('code_challenge'));
      assert.equal(options.body.get('redirect_uri'), auth.searchParams.get('redirect_uri'));
      return Response.json(token);
    }
    assert.equal(url.pathname, '/v1.0/me/calendar/calendarView');
    return Response.json({value: []});
  });
  auth = run.auth;
  const cb = new URL(auth.searchParams.get('redirect_uri'));
  cb.search = new URLSearchParams({state: 'wrong-state', code: 'fixture-code'}).toString();
  assert.equal((await fetch(cb)).status, 400);
  assert.equal(requests, 0);
  cb.searchParams.set('state', auth.searchParams.get('state'));
  assert.match(await (await fetch(cb)).text(), /授权已完成/u);
  await run.result;
  assert.equal(requests, 2);
  const state = store.read(store.location('session.json'));
  assert.equal(state.client, config.client);
  assert.equal(state.refresh_token, token.refresh_token);
  if (process.platform !== 'win32') assert.equal(fs.statSync(store.location('session.json')).mode & 0o777, 0o600);
});

test('does not retain a token when the test mailbox cannot be read', async t => {
  const run = await begin(t, async url => url.origin === 'https://login.microsoftonline.com' ?
    Response.json(token) : Response.json({error: {code: 'MailboxNotEnabledForRESTAPI'}}, {status: 404}));
  const cb = new URL(run.auth.searchParams.get('redirect_uri'));
  cb.search = new URLSearchParams({state: run.auth.searchParams.get('state'), code: 'fixture-code'}).toString();
  assert.match(await (await fetch(cb)).text(), /核对 Exchange Online 邮箱/u);
  await assert.rejects(run.result, {code: 'MAILBOX_UNAVAILABLE'});
  assert.equal(store.read(store.location('session.json'), true), null);
});

test('refreshes inside the same connection and does not replace a signed-out session', async t => {
  fixtureDirectory(t);
  const session = {...config, refresh_token: token.refresh_token, access_token: token.access_token,
    expires_at: 0, connection: 'fixture-connection', revision: 'original-revision'};
  store.write('session.json', session);
  const access = await accessToken(session, false, async (url, options) => {
    assert.equal(options.body.get('grant_type'), 'refresh_token');
    assert.equal(options.body.get('refresh_token'), token.refresh_token);
    return Response.json({...token, access_token: 'second-access'});
  });
  assert.equal(access, 'second-access');
  const updated = store.read(store.location('session.json'));
  assert.notEqual(updated.revision, session.revision);
  await assert.rejects(accessToken(updated, true, async () => {
    fs.rmSync(store.location('session.json'));
    return Response.json(token);
  }), {code: 'SESSION_CHANGED'});
  assert.equal(store.read(store.location('session.json'), true), null);
});
