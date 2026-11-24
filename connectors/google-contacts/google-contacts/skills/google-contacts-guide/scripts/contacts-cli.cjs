'use strict';

const fs = require('node:fs');
const http = require('node:http');
const crypto = require('node:crypto');
const store = require('./storage.cjs');
const {error} = store;

const VERSION = '1.0.0';
const SCOPE = 'https://www.googleapis.com/auth/contacts.readonly';
const PEOPLE = 'https://people.googleapis.com/v1/';
const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const CONTACT_SOURCE = 'READ_SOURCE_TYPE_CONTACT';
const FIELDS = 'metadata,names,nicknames,emailAddresses,phoneNumbers,organizations';
const random = () => crypto.randomBytes(32).toString('base64url');
const resourceName = /^people\/(?!me$)[A-Za-z0-9_-]{1,128}$/;

async function jsonRequest(url, options = {}) {
  const signal = AbortSignal.timeout(15000);
  let response;
  try {
    response = await fetch(url, {...options, signal: options.signal ? AbortSignal.any([signal, options.signal]) : signal,
      redirect: 'error'});
    const raw = await response.text();
    if (Buffer.byteLength(raw) > 2 * 1024 * 1024) throw error('INVALID_RESPONSE', 'Google 返回内容超出大小限制。');
    return {status: response.status, ok: response.ok, data: raw ? JSON.parse(raw) : {}};
  } catch (cause) {
    if (cause.code === 'INVALID_RESPONSE') throw cause;
    if (cause instanceof SyntaxError) throw error('INVALID_RESPONSE', 'Google 返回了无法解析的内容。');
    throw error('NETWORK_ERROR', '无法访问 Google，请检查网络后重试。');
  }
}

async function requestToken(client, grant, signal) {
  const body = new URLSearchParams({client_id: client.client_id, client_secret: client.client_secret, ...grant});
  const {data, ok, status} = await jsonRequest(TOKEN_URL, {method: 'POST', body, signal});
  if (!ok || typeof data.access_token !== 'string' || !data.access_token || !/^Bearer$/i.test(data.token_type ?? '')) {
    if (data.error === 'invalid_grant') {
      throw error('AUTH_REQUIRED', 'Google 会话已失效，请从卡片重新授权。');
    }
    if (data.error === 'invalid_client' || status === 401) {
      throw error('INVALID_CLIENT', 'Google 拒绝了 Desktop OAuth 客户端，请检查项目配置。');
    }
    throw error('OAUTH_FAILED', 'Google 未返回可用的授权。');
  }
  if (data.scope !== undefined && (typeof data.scope !== 'string' || data.scope.trim() !== SCOPE)) {
    throw error('AUTH_DENIED', '未取得预期的 Google 联系人只读权限，请重新授权。');
  }
  return data;
}

async function people(path, params, token, signal) {
  const url = new URL(PEOPLE + path);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, String(value));
  const result = await jsonRequest(url, {headers: {Authorization: 'Bearer ' + token, Accept: 'application/json'}, signal});
  if (result.status === 401) throw error('AUTH_REQUIRED', 'Google 会话已失效，请从卡片重新连接。');
  if (result.status === 403) {
    if (result.data?.error?.details?.some?.(d => d.reason === 'SERVICE_DISABLED')) {
      throw error('API_DISABLED', '请在 Desktop OAuth 客户端所属 Google Cloud 项目启用 People API。');
    }
    throw error('ACCESS_DENIED', 'Google 拒绝访问，请检查 People API、账号和联系人只读权限。');
  }
  if (result.status === 404) throw error('NOT_FOUND', '未找到这个联系人，请重新搜索。');
  if (!result.ok) throw error('SERVICE_FAILED', 'Google 联系人请求失败（HTTP ' + result.status + '）。');
  return result.data;
}

function probe(token, signal) {
  return people('people/me/connections', {personFields: 'metadata', pageSize: 1, sources: CONTACT_SOURCE, fields: 'totalItems'}, token, signal);
}

function normalize(person) {
  if (!resourceName.test(person?.resourceName ?? '') || !person.metadata?.sources?.some(s => s.type === 'CONTACT')) {
    throw error('NOT_FOUND', 'Google 未返回已保存的联系人。');
  }
  const strings = (values, field) => [...new Set((values ?? []).flatMap(v =>
    typeof v[field] === 'string' && v[field] ? [v[field]] : []))];
  const names = strings(person.names, 'displayName');
  return {resource_name: person.resourceName, display_name: names[0] ?? null,
    nicknames: strings(person.nicknames, 'value'), email_addresses: strings(person.emailAddresses, 'value'),
    phone_numbers: strings(person.phoneNumbers, 'value'), organizations: (person.organizations ?? []).map(org => ({
      name: org.name ?? null, title: org.title ?? null,
    }))};
}

function parameters(mode, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw error('BAD_ARGUMENTS', '参数须为 UTF-8 JSON 对象。');
  }
  if (mode === 'search' && Object.keys(value).every(key => ['query','limit'].includes(key)) &&
      typeof value.query === 'string' && value.query.trim() && value.query.length <= 240 &&
      !/[\u0000-\u001f\u007f]/.test(value.query)) {
    const limit = value.limit === undefined ? 10 : value.limit;
    if (Number.isInteger(limit) && limit >= 1 && limit <= 30) return {query: value.query.trim(), limit};
  }
  if (mode === 'read' && Object.keys(value).length === 1 && typeof value.resource_name === 'string' &&
      resourceName.test(value.resource_name)) return {resource_name: value.resource_name};
  throw error('BAD_ARGUMENTS', '搜索须提供非空 query 和可选的 1 至 30 条 limit；读取须提供搜索返回的 resource_name。');
}

async function search(input, token) {
  const args = {readMask: FIELDS, pageSize: input.limit, sources: CONTACT_SOURCE};
  await people('people:searchContacts', {...args, query: '', pageSize: 1, fields: 'results(person(resourceName))'}, token);
  const result = await people('people:searchContacts', {...args, query: input.query}, token);
  return (result.results ?? []).map(row => normalize(row.person));
}

async function readContact(input, token) {
  const result = await people(input.resource_name, {personFields: FIELDS, sources: CONTACT_SOURCE}, token);
  if (result.resourceName !== input.resource_name) throw error('NOT_FOUND', '返回的联系人与请求不匹配，请重新搜索。');
  return normalize(result);
}

function authorize(client, callback, state, verifier) {
  const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  url.search = new URLSearchParams({client_id: client.client_id, redirect_uri: callback, response_type: 'code',
    scope: SCOPE, access_type: 'offline', prompt: 'select_account consent', include_granted_scopes: 'false',
    state, code_challenge: crypto.createHash('sha256').update(verifier).digest('base64url'), code_challenge_method: 'S256'});
  return url;
}

async function login(onUrl = url => console.log(url)) {
  const attempt = random(), nonce = random(), verifier = random(), entry = '/' + attempt;
  const controller = new AbortController();
  const pageNonce = random();
  const previous = store.read(store.location('client.json'), true);
  let client = previous && store.client(previous).installed;
  let base, used = false, finish, timeout, heartbeat;
  store.write('attempt.json', {id: attempt});
  const result = new Promise(resolve => { finish = resolve; });

  function html(res, status, body) {
    res.writeHead(status, {'Content-Type':'text/html; charset=utf-8', 'Cache-Control':'no-store',
      'Referrer-Policy':'same-origin', 'X-Content-Type-Options':'nosniff',
      'Content-Security-Policy':`default-src 'none'; script-src 'nonce-${pageNonce}'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'`});
    res.end('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>连接 Google 联系人</title>' + body + '</html>');
  }

  async function handle(req, res) {
    if (req.headers.host !== new URL(base).host) return html(res, 403, '<p>请求来源不匹配。</p>');
    const current = new URL(req.url, base);
    if (req.method === 'GET' && current.pathname === entry) {
      return html(res, 200, `<h1>连接 Google 联系人</h1><p>只申请 Google 联系人读取权限。OAuth 配置和会话保存在本机。</p>${client
        ? `<a href="${entry}/authorize">前往 Google 授权</a>`
        : `<p>请选择 Google Cloud 创建的 Desktop app OAuth JSON。</p>
<label for="file">Desktop OAuth JSON</label> <input id="file" type="file" accept=".json">
<button id="save">保存并继续</button><p id="result" role="status"></p>
<script nonce="${pageNonce}">
document.getElementById('save').onclick = async () => {
  const result = document.getElementById('result');
  try {
    const file = document.getElementById('file').files[0];
    if (!file || file.size > 32768) { result.textContent = '请选择有效且不超过 32 KiB 的 JSON 文件。'; return; }
    const response = await fetch(location.pathname + '/configure', {method:'POST', headers:{'Content-Type':'application/json'}, body: await file.text()});
    if (response.ok) location.reload();
    else result.textContent = '配置未保存，请使用 Desktop app OAuth JSON。';
  } catch { result.textContent = '本机入口不可用，请回到 WorkSwarm 重新连接。'; }
};
</script>`}`);
    }
    if (req.method === 'POST' && current.pathname === entry + '/configure' && !client) {
      if (req.headers.origin !== base || !req.headers['content-type']?.startsWith('application/json')) {
        return html(res, 403, '<p>请求来源不匹配。</p>');
      }
      let raw = '';
      for await (const chunk of req) {
        raw += chunk;
        if (Buffer.byteLength(raw) > 32768) return html(res, 413, '<p>配置文件过大。</p>');
      }
      if (client || controller.signal.aborted) return html(res, 409, '<p>配置已存在或入口已关闭。</p>');
      try {
        const value = store.client(JSON.parse(raw));
        store.write('client.json', value);
        client = value.installed;
        return html(res, 200, '<p>配置已保存。</p>');
      } catch {
        return html(res, 400, '<p>请使用 Google Cloud 创建的 Desktop app OAuth JSON。</p>');
      }
    }
    const callback = base + entry + '/callback';
    if (req.method === 'GET' && current.pathname === entry + '/authorize' && client && !used) {
      res.writeHead(302, {Location: authorize(client, callback, nonce, verifier).href, 'Cache-Control':'no-store','Referrer-Policy':'no-referrer'});
      return res.end();
    }
    if (req.method !== 'GET' || current.pathname !== entry + '/callback' || used || !client ||
        current.searchParams.get('state') !== nonce) return html(res, 404, '<p>授权入口或状态已失效。</p>');
    used = true;
    const code = current.searchParams.get('code');
    if (!code || current.searchParams.has('error')) {
      html(res, 200, '<h1>Google 授权未完成</h1><p>请返回 WorkSwarm。</p>');
      return finish({error: error('AUTH_DENIED', 'Google 授权已取消或拒绝。')});
    }
    const tokens = await requestToken(client, {grant_type:'authorization_code', code,
      redirect_uri:callback, code_verifier:verifier}, controller.signal);
    if (typeof tokens.refresh_token !== 'string' || !tokens.refresh_token) {
      throw error('AUTH_DENIED', 'Google 未返回可持续使用的授权，请在同意页批准读取联系人。');
    }
    await probe(tokens.access_token, controller.signal);
    if (controller.signal.aborted || store.read(store.location('attempt.json'), true)?.id !== attempt) {
      throw error('CANCELLED', '本机授权已取消，请返回 WorkSwarm。');
    }
    store.write('session.json', {attempt, refresh_token:tokens.refresh_token});
    html(res, 200, `<script nonce="${pageNonce}">history.replaceState(null,'','${entry}/complete')</script>
<h1>Google 联系人授权已完成</h1><p>已验证 People API，请返回 WorkSwarm。</p>`);
    return finish({});
  }

  const server = http.createServer((req,res) => {
    handle(req,res).catch(cause => {
      if (!res.headersSent && !res.destroyed) {
        const message = ['API_DISABLED','ACCESS_DENIED'].includes(cause.code) ? cause.message : '请返回 WorkSwarm 检查设置并重试。';
        html(res, 400, '<h1>Google 授权未完成</h1><p>' + message + '</p>');
      }
      finish({error:cause});
    });
  });
  server.requestTimeout = 24000;
  server.headersTimeout = 8000;
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0,'127.0.0.1',resolve);
  });
  base = 'http://127.0.0.1:' + server.address().port;
  const cancel = () => {
    controller.abort();
    finish({error:error('CANCELLED','已取消 Google 授权。')});
  };
  process.once('SIGTERM',cancel);
  process.once('SIGINT',cancel);
  try {
    timeout = setTimeout(() => { controller.abort(); finish({error:error('TIMEOUT','Google 授权超时，请从卡片重新连接。')}); }, 10 * 60 * 1000);
    onUrl(base + entry);
    heartbeat = setInterval(() => console.log('等待 Google 联系人授权…'), 10000);
    const completed = await result;
    if (completed.error) throw completed.error;
  } finally {
    clearTimeout(timeout);
    clearInterval(heartbeat);
    controller.abort();
    server.close();
    server.closeIdleConnections?.();
    process.removeListener('SIGTERM',cancel);
    process.removeListener('SIGINT',cancel);
  }
}

async function accessToken() {
  const config = store.read(store.location('client.json'), true);
  const session = store.read(store.location('session.json'), true);
  if (!config || !session?.refresh_token || session.attempt !== store.read(store.location('attempt.json'), true)?.id) {
    throw error('AUTH_REQUIRED', '请先从 WorkSwarm 卡片连接 Google 联系人。');
  }
  const client = store.client(config).installed;
  return (await requestToken(client,{grant_type:'refresh_token',refresh_token:session.refresh_token})).access_token;
}

const errors = new Set(['BAD_ARGUMENTS','UNSAFE_STORAGE','INVALID_CREDENTIALS','INVALID_CLIENT','INVALID_RESPONSE',
  'NETWORK_ERROR','AUTH_REQUIRED','AUTH_DENIED','OAUTH_FAILED','API_DISABLED','ACCESS_DENIED','NOT_FOUND',
  'SERVICE_FAILED','CANCELLED','TIMEOUT','NODE_VERSION']);

async function main(args = process.argv.slice(2)) {
  const [mode,flag,file] = args;
  try {
    if (args.length === 1 && mode === 'version') return console.log(VERSION);
    if (args.length === 1 && mode === 'prepare') {
      if (Number(process.versions.node.split('.')[0]) < 22) throw error('NODE_VERSION','请使用 WorkSwarm 内置 Node 或 Node.js 22 及以上版本。');
      store.directory();
      return print({ok:true,message:'Google 联系人运行环境已就绪。'});
    }
    if (args.length === 1 && mode === 'login') {
      await login();
      return print({ok:true,connected:true,message:'Google 联系人授权完成，People API 校验通过。'});
    }
    if (args.length === 1 && mode === 'logout') {
      store.write('attempt.json',{id:random()});
      fs.rmSync(store.location('session.json'),{force:true});
      return print({ok:true,connected:false,message:'Google 联系人已断开本机授权。'});
    }
    if (args.length === 1 && mode === 'status') {
      await probe(await accessToken());
      return print({ok:true,connected:true,message:'Google 联系人授权有效。'});
    }
    if (!['search','read'].includes(mode) || args.length !== 3 || flag !== '--input-file') {
      throw error('BAD_ARGUMENTS','支持 search 或 read --input-file 参数.json，以及 prepare、version、login、logout、status。');
    }
    const info = fs.statSync(file);
    if (!info.isFile() || info.size > 16384) throw error('BAD_ARGUMENTS','请提供不超过 16 KiB 的 UTF-8 JSON 参数文件。');
    let parsed;
    try { parsed = JSON.parse(fs.readFileSync(file,'utf8')); }
    catch { throw error('BAD_ARGUMENTS','请提供可读取的 UTF-8 JSON。'); }
    const input = parameters(mode,parsed);
    const token = await accessToken();
    const result = mode === 'search' ? await search(input,token) : await readContact(input,token);
    print({ok:true,operation:mode,result});
  } catch (cause) {
    const known = errors.has(cause.code);
    print({ok:false,connected:false,code:known ? cause.code : 'CLIENT_FAILED',
      message:known ? cause.message : 'Google 联系人操作未完成，请核对网络和参数。'});
    if (mode !== 'status') process.exitCode = 1;
  }
}

function print(value) {
  console.log(JSON.stringify(value));
}

module.exports = {main, login, authorize, parameters, search, readContact, VERSION, SCOPE};
if (require.main === module) main();
