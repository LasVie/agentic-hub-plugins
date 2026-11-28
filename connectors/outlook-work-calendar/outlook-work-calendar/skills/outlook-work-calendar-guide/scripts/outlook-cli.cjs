'use strict';

const fs = require('node:fs');
const http = require('node:http');
const crypto = require('node:crypto');
const store = require('./storage.cjs');
const outlook = require('./graph.cjs');

const {error} = store;
const VERSION = '1.0.0';
const SESSION = 'session.json';
const ERRORS = new Set([
  'BAD_ARGUMENTS', 'BAD_CURSOR', 'INVALID_CLIENT', 'UNSAFE_STORAGE', 'INVALID_CREDENTIALS',
  'SESSION_CHANGED', 'AUTH_REQUIRED', 'AUTH_FAILED', 'AUTH_TIMEOUT', 'ACCESS_DENIED',
  'MAILBOX_UNAVAILABLE', 'NOT_FOUND', 'RATE_LIMIT', 'SERVICE_ERROR', 'NETWORK_ERROR',
  'INVALID_RESPONSE', 'RESPONSE_LIMIT',
]);

function currentSession() {
  return store.read(store.location(SESSION), true);
}

function changeSession(change) {
  const lock = store.location('session-write.lock');
  try {
    fs.mkdirSync(lock, {mode: 0o700});
  } catch (cause) {
    if (cause.code === 'EEXIST') {
      throw error('SESSION_CHANGED', '连接状态正在更新，请稍后重试。');
    }
    throw cause;
  }
  try {
    return change();
  } finally {
    fs.rmdirSync(lock);
  }
}

function saveSession(config, token) {
  changeSession(() => store.write(SESSION, {
    ...config, ...token, connection: crypto.randomUUID(), revision: crypto.randomUUID(),
  }));
}

async function accessToken(session, refresh = false, request = fetch) {
  if (!session?.refresh_token || typeof session.connection !== 'string') {
    throw error('AUTH_REQUIRED', '请先在 WorkSwarm 的 Outlook 工作日历卡片完成 Microsoft 授权。');
  }
  if (!refresh && typeof session.access_token === 'string' && session.expires_at - Date.now() > 60_000) {
    return session.access_token;
  }
  const fresh = await outlook.exchange(session, {
    grant_type: 'refresh_token', refresh_token: session.refresh_token,
  }, request);
  return changeSession(() => {
    const current = currentSession();
    if (current?.connection !== session.connection) {
      throw error('SESSION_CHANGED', '授权在请求期间发生变化，请重新查询。');
    }
    if (current.revision !== session.revision) return current.access_token;
    store.write(SESSION, {...session, ...fresh, revision: crypto.randomUUID()});
    return fresh.access_token;
  });
}

async function authorized(operation) {
  const session = currentSession();
  const token = await accessToken(session);
  try {
    return await operation(token);
  } catch (cause) {
    if (cause.code !== 'AUTH_REQUIRED') throw cause;
    const latest = currentSession();
    if (latest?.connection !== session?.connection) {
      throw error('SESSION_CHANGED', '授权在请求期间发生变化，请重新查询。');
    }
    return operation(await accessToken(latest, latest.revision === session.revision));
  }
}

function html(title, body) {
  return '<!doctype html><html lang="zh-CN"><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1"><title>' +
    title + '</title><h1>' + title + '</h1>' + body + '</html>';
}

function form(base, configured, invalid = false) {
  const message = invalid ? '<p>请核对两个 ID，格式应为 UUID。</p>' : '';
  const fields = '<form method="post" action="' + base + '/configure">' +
    '<p><label>目录（租户）ID <input name="tenant" required maxlength="36"></label></p>' +
    '<p><label>应用程序（客户端）ID <input name="client" required maxlength="36"></label></p>' +
    '<button>保存应用配置</button></form>';
  const signIn = '<p><a href="' + base + '/authorize">前往 Microsoft 授权</a></p>';
  return html('连接 Outlook 工作日历', '<p>使用工作或学校账号授权读取主日历基本信息。</p>' +
    '<p>请使用组织租户的桌面应用注册，回调为 http://localhost。</p>' + message +
    (configured ? signIn + '<details><summary>更换应用配置</summary>' + fields + '</details>' : fields));
}

function reply(res, status, body, extra = {}) {
  res.writeHead(status, {
    'Content-Type': 'text/html; charset=UTF-8',
    'Cache-Control': 'no-store',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': "default-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    ...extra,
  });
  res.end(body);
}

async function formData(req) {
  if (!/^application\/x-www-form-urlencoded(?:;|$)/iu.test(req.headers['content-type'] ?? '')) {
    throw error('INVALID_CLIENT', '请使用本机连接表单。');
  }
  let text = '';
  for await (const chunk of req) {
    text += chunk.toString('utf8');
    if (Buffer.byteLength(text) > 2048) throw error('INVALID_CLIENT', '应用配置过大。');
  }
  const params = new URLSearchParams(text);
  if (params.size !== 2) throw error('INVALID_CLIENT', '应用配置无效。');
  return outlook.clientConfig(params.get('tenant'), params.get('client'));
}

function safeFailure(cause) {
  if (ERRORS.has(cause?.code)) return {code: cause.code, message: cause.message};
  return {code: 'OPERATION_FAILED', message: 'Outlook 工作日历操作未完成，请检查本机配置或网络。'};
}

async function login({request = fetch, announce = console.log, timeout = 180_000} = {}) {
  const nonce = '/' + crypto.randomBytes(24).toString('hex');
  let config = currentSession();
  if (config) config = outlook.clientConfig(config.tenant, config.client);
  let port;
  let flow;
  let expired = false;
  let finish;
  let fail;
  const completed = new Promise((resolve, reject) => { finish = resolve; fail = reject; });
  const server = http.createServer(async (req, res) => {
    const host = req.headers.host;
    const localHost = '127.0.0.1:' + port;
    const callbackHost = 'localhost:' + port;
    let url;
    try {
      url = new URL(req.url, 'http://' + localHost);
    } catch {
      return reply(res, 400, '无效请求。');
    }
    if (host === localHost && req.method === 'GET' && url.pathname === nonce) {
      return reply(res, 200, form(nonce, config));
    }
    if (host === localHost && req.method === 'POST' && url.pathname === nonce + '/configure') {
      try {
        if (req.headers.origin && req.headers.origin !== 'http://' + localHost) {
          return reply(res, 403, '请从本机连接页提交。');
        }
        config = await formData(req);
        flow = null;
        return reply(res, 303, '', {Location: nonce});
      } catch {
        return reply(res, 400, form(nonce, config, true));
      }
    }
    if (host === localHost && req.method === 'GET' && url.pathname === nonce + '/authorize' && config) {
      const verifier = crypto.randomBytes(48).toString('base64url');
      const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
      const state = crypto.randomBytes(32).toString('base64url');
      const redirect = 'http://' + callbackHost + '/';
      flow = {state, verifier, redirect, config};
      const target = outlook.authorizationUrl(config, {state, challenge, redirect});
      return reply(res, 302, '', {Location: target.href});
    }
    if (host !== callbackHost || req.method !== 'GET' || url.pathname !== '/') {
      return reply(res, 404, '需要从 WorkSwarm 卡片打开授权入口。');
    }
    const state = url.searchParams.get('state');
    if (!flow || !state || state !== flow.state) {
      return reply(res, 400, '授权链接不匹配，请返回原来的 WorkSwarm 卡片。');
    }
    const pending = flow;
    flow = null;
    try {
      const code = url.searchParams.get('code');
      if (!code || code.length > 8192 || url.searchParams.has('error')) {
        throw error('AUTH_FAILED', 'Microsoft 没有完成授权，请核对账号和组织管理员同意。');
      }
      const credentials = await outlook.exchange(pending.config, {
        grant_type: 'authorization_code', code, code_verifier: pending.verifier, redirect_uri: pending.redirect,
      }, request);
      await outlook.probe(credentials.access_token, request);
      if (expired) throw error('AUTH_TIMEOUT', 'Microsoft 授权已超时，请从卡片重试。');
      saveSession(pending.config, credentials);
      reply(res, 200, html('Outlook 工作日历授权已完成', '<p>已确认主日历可以读取。请返回 WorkSwarm。</p>'));
      finish();
    } catch (cause) {
      const safe = safeFailure(cause);
      reply(res, 400, html('Outlook 工作日历连接失败', '<p>' + safe.message + '</p>'));
      fail(cause);
    }
  });
  server.requestTimeout = 20_000;
  server.headersTimeout = 10_000;
  server.keepAliveTimeout = 1000;
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  port = server.address().port;
  const timer = setTimeout(() => {
    expired = true;
    fail(error('AUTH_TIMEOUT', 'Microsoft 授权已超时，请从卡片重试。'));
  }, timeout);
  try {
    announce('http://127.0.0.1:' + port + nonce);
    await completed;
  } finally {
    clearTimeout(timer);
    server.close();
  }
}

function readInput(args) {
  if (args.length !== 3 || args[1] !== '--input') throw error('BAD_ARGUMENTS', '请通过 --input 指定 JSON 参数文件。');
  try {
    const stat = fs.statSync(args[2]);
    if (!stat.isFile() || stat.size > 16_384) throw new Error();
    return JSON.parse(fs.readFileSync(args[2], 'utf8'));
  } catch {
    throw error('BAD_ARGUMENTS', '参数文件须是小于 16 KiB 的有效 JSON。');
  }
}

async function main(args = process.argv.slice(2)) {
  const [mode] = args;
  try {
    let output;
    switch (mode) {
      case 'prepare':
        store.directory();
        output = {ready: true};
        break;
      case 'version':
        console.log(VERSION);
        return;
      case 'login':
        await login();
        return;
      case 'status':
        await authorized(token => outlook.probe(token));
        output = {connected: true};
        break;
      case 'logout':
        changeSession(() => fs.rmSync(store.location(SESSION), {force: true}));
        output = {connected: false};
        break;
      case 'list': {
        const req = outlook.listRequest(readInput(args));
        output = await authorized(token => outlook.list(req, token));
        break;
      }
      case 'get': {
        const url = outlook.detailRequest(readInput(args));
        output = await authorized(async token => outlook.record(await outlook.graph(url, token)));
        break;
      }
      default:
        throw error('BAD_ARGUMENTS', '可用命令为 prepare、version、login、status、logout、list 和 get。');
    }
    console.log(JSON.stringify(output));
  } catch (cause) {
    console.log(JSON.stringify({...safeFailure(cause), ...(mode === 'status' ? {connected: false} : {})}));
    if (mode !== 'status') process.exitCode = 1;
  }
}

module.exports = {main, login, accessToken};
if (require.main === module) main();
