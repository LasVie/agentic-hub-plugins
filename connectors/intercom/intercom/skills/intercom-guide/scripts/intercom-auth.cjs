'use strict';

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const http = require('node:http');
const crypto = require('node:crypto');
const {setTimeout: delay} = require('node:timers/promises');
const {CLIENT, origin, failure, oauthPost, withMcp, checkTools} = require('./intercom-mcp.cjs');

const callbackPath = '/oauth/callback';
const scope = 'mcp operator';
const nonce = () => crypto.randomBytes(32).toString('base64url');

function privateDirectory() {
  const root = process.env.JIUWENSWARM_DATA_DIR || process.env.JIUWENSWARM_HOME || path.join(os.homedir(), '.jiuwenswarm');
  const dir = path.resolve(root, 'connector-data', 'intercom');
  for (let p = dir; ; p = path.dirname(p)) {
    if (fs.existsSync(path.join(p, '.git')) || (fs.existsSync(p) && fs.lstatSync(p).isSymbolicLink())) {
      throw failure('STORAGE_ERROR', 'Intercom 授权目录需位于源码仓库之外，且不能经过符号链接。');
    }
    if (p === path.dirname(p)) break;
  }
  fs.mkdirSync(dir, {recursive: true, mode: 0o700});
  const stat = fs.statSync(dir);
  if (process.platform !== 'win32' && (stat.uid !== process.getuid() || stat.mode & 0o077)) {
    throw failure('STORAGE_ERROR', 'Intercom 授权目录需归当前用户所有，权限为 700。');
  }
  return dir;
}

function readState(dir) {
  const file = path.join(dir, 'session.json');
  try {
    const stat = fs.lstatSync(file);
    if (!stat.isFile() || stat.size > 65536 || (process.platform !== 'win32' && stat.mode & 0o077)) {
      throw failure('STORAGE_ERROR', 'Intercom 本地授权文件权限或格式错误。');
    }
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return {generation: ''};
    throw error;
  }
}

function writeState(dir, data) {
  const temp = path.join(dir, nonce() + '.tmp');
  try {
    fs.writeFileSync(temp, JSON.stringify(data), {mode: 0o600, flag: 'wx'});
    fs.renameSync(temp, path.join(dir, 'session.json'));
  } finally {
    fs.rmSync(temp, {force: true});
  }
}

async function withStateLock(dir, fn) {
  const lock = path.join(dir, 'state.lock');
  const deadline = Date.now() + 15000;
  while (true) {
    try {
      fs.mkdirSync(lock, {mode: 0o700});
      break;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      try {
        if (Date.now() - fs.lstatSync(lock).mtimeMs > 120000) fs.rmdirSync(lock);
      } catch (stale) {
        if (!['ENOENT', 'ENOTEMPTY'].includes(stale.code)) throw stale;
      }
      if (Date.now() >= deadline) throw failure('BUSY', 'Intercom 连接正在更新，请稍后重试。');
      await delay(120 + crypto.randomInt(100));
    }
  }
  try { return await fn(); } finally { fs.rmdirSync(lock); }
}

function tokenState(result, existing) {
  if (typeof result.access_token !== 'string' || !result.access_token || !/^bearer$/i.test(result.token_type ?? '')) {
    throw failure('OAUTH_FAILED', 'Intercom 未返回可用的授权。');
  }
  return {
    ...existing,
    accessToken: result.access_token,
    refreshToken: result.refresh_token || existing.refreshToken || null,
    expiresAt: typeof result.expires_in === 'number' ? Date.now() + result.expires_in * 1000 : null,
  };
}

function reply(res, status, node) {
  res.writeHead(status, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store',
    'Referrer-Policy': 'same-origin', 'X-Content-Type-Options': 'nosniff',
    'Content-Security-Policy': "default-src 'none'; base-uri 'none'; frame-ancestors 'none'"});
  res.end('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>连接 Intercom</title>' + node + '</html>');
}

async function login(dir, onUrl) {
  const generation = readState(dir).generation;
  const state = nonce(), verifier = nonce(), entry = '/' + nonce();
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
  const timeoutMs = 15 * 60 * 1000;
  let pending, starting = false, used = false, cancelled = false, finish, timeout, base;
  const outcome = new Promise(resolve => { finish = resolve; });
  const server = http.createServer((req, res) => {
    handle(req, res).catch(error => {
      if (!res.headersSent) reply(res, 502, '<h1>Intercom 连接失败</h1><p>请返回 WorkSwarm，检查地区和网络后重试。</p>');
      finish({error});
    });
  });
  async function handle(req, res) {
    if (cancelled || req.headers.host !== new URL(base).host) return reply(res, 403, '<p>连接来源不匹配。</p>');
    const url = new URL(req.url, base);
    if (req.method === 'GET' && url.pathname === entry && !url.search) {
      return reply(res, 200, `<h1>连接 Intercom</h1>
<p>请选择工作区地区。app.intercom.com 为美区，app.eu.intercom.com 为欧区。</p>
<p>WorkSwarm 只提供客服会话和联系人的搜索及读取。Intercom 官方同意页也会申请添加内部备注、创建或更新文章、查看 Fin 受众和使用 Fin Operator。请核对工作区与权限后自行决定是否继续。</p>
<p><a href="${entry}/us">连接美区</a>　<a href="${entry}/eu">连接欧区</a></p>`);
    }
    if (req.method === 'GET' && !url.search && [entry + '/us', entry + '/eu'].includes(url.pathname)) {
      if (req.headers['sec-fetch-site'] === 'cross-site') return reply(res, 403, '<p>连接来源不匹配。</p>');
      const region = url.pathname.slice(-2);
      const issuer = origin(region);
      if (starting) return reply(res, 409, '<p>连接请求已经发起。</p>');
      starting = true;
      const redirectUri = base + callbackPath;
      const client = await oauthPost(region, '/register', {client_name: CLIENT, client_uri: 'https://workswarm.app',
        redirect_uris: [redirectUri], grant_types: ['authorization_code', 'refresh_token'],
        response_types: ['code'], token_endpoint_auth_method: 'none', scope});
      if (typeof client.client_id !== 'string' || !client.client_id ||
          client.token_endpoint_auth_method !== 'none' || !client.redirect_uris?.includes(redirectUri)) {
        throw failure('OAUTH_FAILED', 'Intercom 返回的客户端注册数据不符合本机授权要求。');
      }
      pending = {region, clientId: client.client_id, redirectUri};
      const query = new URLSearchParams({client_id: client.client_id, redirect_uri: redirectUri,
        response_type: 'code', scope, state, code_challenge: challenge, code_challenge_method: 'S256',
        resource: issuer + '/mcp'});
      res.writeHead(303, {Location: issuer + '/authorize?' + query, 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'});
      return res.end();
    }
    if (req.method !== 'GET' || url.pathname !== callbackPath || used || !pending ||
        url.searchParams.get('state') !== state) return reply(res, 404, '<p>授权入口不存在或已经失效。</p>');
    const code = url.searchParams.get('code');
    used = true;
    if (!code || url.searchParams.has('error')) {
      reply(res, 400, '<h1>Intercom 授权未完成</h1><p>可以返回 WorkSwarm 重新连接。</p>');
      return finish({error: failure('AUTH_DENIED', 'Intercom 授权未完成或已拒绝。')});
    }
    const token = await oauthPost(pending.region, '/token', new URLSearchParams({grant_type: 'authorization_code',
      code, client_id: pending.clientId, code_verifier: verifier, redirect_uri: pending.redirectUri,
      resource: origin(pending.region) + '/mcp'}));
    const session = tokenState(token, {generation: nonce(), region: pending.region, clientId: pending.clientId});
    await withMcp(session.region, session.accessToken, checkTools);
    await withStateLock(dir, () => {
      if (cancelled || readState(dir).generation !== generation) throw failure('CANCELLED', '此连接已取消或已有更新的授权。');
      writeState(dir, session);
    });
    reply(res, 200, '<h1>Intercom 授权已完成</h1><p>请返回 WorkSwarm。</p>');
    finish({region: session.region});
  }

  server.requestTimeout = 10000;
  server.headersTimeout = 5000;
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  base = 'http://127.0.0.1:' + server.address().port;
  function cancel(error = failure('CANCELLED', 'Intercom 连接已取消。')) {
    cancelled = true;
    finish({error});
  }
  const onSignal = () => cancel();
  process.once('SIGINT', onSignal);
  process.once('SIGTERM', onSignal);
  try {
    timeout = setTimeout(() => cancel(failure('TIMEOUT', 'Intercom 授权超时，请从卡片重新连接。')), timeoutMs);
    onUrl(base + entry);
    const result = await outcome;
    if (result.error) throw result.error;
    return result.region;
  } finally {
    clearTimeout(timeout);
    process.removeListener('SIGINT', onSignal);
    process.removeListener('SIGTERM', onSignal);
    server.close();
    server.closeIdleConnections?.();
  }
}

async function useSession(dir, action) {
  const session = readState(dir);
  if (!session.accessToken) throw failure('AUTH_REQUIRED', '请先从 WorkSwarm 连接器卡片完成 Intercom 授权。');
  const run = current => withMcp(current.region, current.accessToken, action);
  if (!session.expiresAt || session.expiresAt > Date.now() + 30000) {
    try { return await run(session); } catch (error) {
      if (error.code !== 'AUTH_REQUIRED') throw error;
    }
  }
  const refreshed = await withStateLock(dir, async () => {
    const current = readState(dir);
    if (current.generation !== session.generation || !current.refreshToken) {
      throw failure('AUTH_REQUIRED', 'Intercom 授权已断开或到期，请从卡片重新连接。');
    }
    if (current.accessToken !== session.accessToken) return current;
    const result = await oauthPost(current.region, '/token', new URLSearchParams({grant_type: 'refresh_token',
      refresh_token: current.refreshToken, client_id: current.clientId, resource: origin(current.region) + '/mcp'}));
    const next = tokenState(result, current);
    writeState(dir, next);
    return next;
  });
  return run(refreshed);
}

async function logout(dir) {
  return withStateLock(dir, () => writeState(dir, {generation: nonce()}));
}

module.exports = {privateDirectory, login, logout, useSession};
