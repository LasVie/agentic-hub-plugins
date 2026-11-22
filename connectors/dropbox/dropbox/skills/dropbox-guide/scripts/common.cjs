'use strict';
// Team implementation using Node built-ins and the public Dropbox API contract.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const crypto = require('node:crypto');
const VERSION = '1.1.0';
const SCOPES = ['account_info.read', 'files.metadata.read', 'files.content.read'];
const REDIRECT = 'http://localhost:53682/oauth/callback';
const PORT = 53682;
const MAX_TEXT = 1024 * 1024;
function fault(code, message) { return Object.assign(new Error(message), {code, safe: true}); }
function publicError(e) { return e?.safe ? {ok: false, code: e.code, message: e.message} : {ok: false, code: 'CLIENT_FAILED', message: 'Dropbox 操作未完成，请检查连接后重试。'}; }
function checkPath(p) {
  for (let x = path.resolve(p);; x = path.dirname(x)) {
    if (fs.existsSync(path.join(x, '.git'))) throw fault('UNSAFE_STATE', 'Dropbox 私有配置不能存放在代码仓库内。');
    try { if (fs.lstatSync(x).isSymbolicLink()) throw fault('UNSAFE_STATE', 'Dropbox 配置路径不能包含符号链接。'); }
    catch (e) { if (e.code !== 'ENOENT') throw e; }
    if (path.dirname(x) === x) break;
  }
}
function stateDir() {
  const root = process.env.JIUWENSWARM_DATA_DIR || process.env.JIUWENSWARM_HOME || path.join(os.homedir(), '.jiuwenswarm');
  const dir = path.resolve(root, 'connector-data/dropbox/cli-v1');
  checkPath(dir); fs.mkdirSync(dir, {recursive: true, mode: 0o700});
  const s = fs.statSync(dir);
  if (process.getuid && s.uid !== process.getuid()) throw fault('UNSAFE_STATE', 'Dropbox 配置目录不属于当前用户。');
  fs.chmodSync(dir, 0o700); return dir;
}
function filePath(name) { return path.join(stateDir(), name); }
function readJSON(name, limit = 65536) {
  const p = filePath(name); let fd;
  try {
    fd = fs.openSync(p, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0));
    const s = fs.fstatSync(fd);
    if (!s.isFile() || s.size > limit || (process.getuid && s.uid !== process.getuid())) throw fault('UNSAFE_STATE', 'Dropbox 配置文件不安全。');
    if (process.platform !== 'win32' && (s.mode & 0o077)) throw fault('UNSAFE_STATE', 'Dropbox 配置文件权限应仅允许当前用户。');
    return JSON.parse(fs.readFileSync(fd, 'utf8'));
  } catch (e) { if (e.code === 'ENOENT') return null; if (e.safe) throw e; throw fault('STATE_INVALID', 'Dropbox 配置损坏或无法安全读取，请从卡片重新连接。'); }
  finally { if (fd !== undefined) fs.closeSync(fd); }
}
function writeJSON(name, data) {
  const target = filePath(name); checkPath(target);
  const tmp = filePath('.' + name + '.' + crypto.randomBytes(12).toString('hex')); let fd;
  try {
    fd = fs.openSync(tmp, 'wx', 0o600); fs.writeFileSync(fd, JSON.stringify(data) + '\n'); fs.fsyncSync(fd); fs.closeSync(fd); fd = undefined;
    fs.renameSync(tmp, target);
  } finally { if (fd !== undefined) fs.closeSync(fd); try { fs.unlinkSync(tmp); } catch (e) { if (e.code !== 'ENOENT') throw e; } }
}
function epoch() { let x = readJSON('epoch.json'); if (!x) { x = {id: crypto.randomUUID()}; writeJSON('epoch.json', x); } return x.id; }
function logout() { writeJSON('epoch.json', {id: crypto.randomUUID()}); const p = filePath('session.json'); checkPath(p); try { fs.unlinkSync(p); } catch (e) { if (e.code !== 'ENOENT') throw e; } return {ok: true, connected: false, message: '本机 Dropbox 会话已清除；服务端授权可在 Dropbox 关联应用中管理。'}; }
function appKey(value) { if (typeof value !== 'string' || !/^[A-Za-z0-9_-]{5,128}$/.test(value)) throw fault('BAD_APP_KEY', '请输入公开的 Dropbox App key，不要填写 App secret 或令牌。'); return value; }
function configuredKey() { const value = readJSON('app.json'); return value ? appKey(value.app_key) : null; }
function scopeCheck(value) {
  if (typeof value !== 'string') throw fault('SCOPE_MISSING', 'Dropbox 未确认完整的只读权限，请重新授权。');
  const actual = value.split(/\s+/).filter(Boolean);
  if (actual.length !== SCOPES.length || !SCOPES.every(x => actual.includes(x))) throw fault('SCOPE_MISMATCH', 'Dropbox 返回的权限与三项只读范围不一致，请检查应用设置。');
  return actual;
}
function session() {
  const s = readJSON('session.json');
  if (!s || s.epoch !== epoch() || s.app_key !== configuredKey() || !Number.isFinite(s.expires_at) || typeof s.access_token !== 'string' || !s.access_token || typeof s.refresh_token !== 'string' || !s.refresh_token) throw fault('AUTH_REQUIRED', 'Dropbox 尚未授权或登录已失效，请从连接器卡片重新连接。');
  scopeCheck(s.scope); return s;
}
function commitToken(result, key, expectedEpoch, previous = null) {
  if (epoch() !== expectedEpoch || configuredKey() !== key) throw fault('AUTH_CANCELLED', 'Dropbox 连接已取消，未保存这次授权。');
  const scope = result.scope ?? previous?.scope;
  scopeCheck(scope);
  const refresh = result.refresh_token || previous?.refresh_token;
  if (typeof result.access_token !== 'string' || !result.access_token || result.access_token.length > 16384 || typeof refresh !== 'string' || !refresh || refresh.length > 16384 || !Number.isFinite(result.expires_in) || result.expires_in <= 0 || String(result.token_type).toLowerCase() !== 'bearer') throw fault('TOKEN_INVALID', 'Dropbox 未返回有效的离线授权，请从卡片重新连接。');
  const s = {app_key: key, access_token: result.access_token, refresh_token: refresh, expires_at: Date.now() + result.expires_in * 1000, scope, epoch: expectedEpoch};
  writeJSON('session.json', s); return s;
}
async function collect(response, limit) {
  const length = response.headers.get('content-length');
  if (length && Number(length) > limit) { await response.body?.cancel(); throw fault('TOO_LARGE', '返回内容超过连接器大小限制，未返回截断正文。'); }
  const reader = response.body?.getReader(); if (!reader) return Buffer.alloc(0);
  const chunks = []; let size = 0;
  try { while (true) { const x = await reader.read(); if (x.done) break; size += x.value.length; if (size > limit) throw fault('TOO_LARGE', '返回内容超过连接器大小限制，未返回截断正文。'); chunks.push(Buffer.from(x.value)); } }
  finally { try { await reader.cancel(); } catch {} reader.releaseLock(); }
  if (length && !response.headers.get('content-encoding') && Number(length) !== size) throw fault('INCOMPLETE_READ', '返回数据长度不完整，不能声称已读到全文。');
  return Buffer.concat(chunks);
}
async function request(url, {json, form, token, headers = {}, raw = false, timeout = 12000} = {}) {
  if (!['https://api.dropboxapi.com/oauth2/token','https://content.dropboxapi.com/2/files/download',
    ...['users/get_current_account','files/list_folder','files/list_folder/continue','files/search_v2','files/search/continue_v2','files/get_metadata'].map(x => 'https://api.dropboxapi.com/2/' + x)].includes(url)) throw fault('SCOPE_REJECTED', '只允许固定的 Dropbox OAuth 和文件读取接口。');
  const h = {'Accept-Encoding': 'identity', ...headers}; if (token) h.Authorization = 'Bearer ' + token;
  let body;
  if (form) { h['Content-Type'] = 'application/x-www-form-urlencoded'; body = new URLSearchParams(form).toString(); }
  else if (json !== undefined) { h['Content-Type'] = 'application/json'; body = JSON.stringify(json); }
  try {
    const response = await fetch(url, {method: 'POST', headers: h, body, redirect: 'error', signal: AbortSignal.timeout(timeout)});
    const bytes = await collect(response, response.ok && raw ? MAX_TEXT : 4 * MAX_TEXT);
    if (!response.ok) {
      let e; try { e = JSON.parse(bytes.toString('utf8')); } catch {}
      if (response.status === 401 || e?.error === 'invalid_grant') throw fault('AUTH_REQUIRED', 'Dropbox 授权无效、已撤销或已过期，请从卡片重新连接。');
      if (response.status === 403) throw fault('ACCESS_DENIED', '当前 Dropbox 账号或应用没有所需读取权限。');
      if (response.status === 409 && /not_found/.test(e?.error_summary || '')) throw fault('NOT_FOUND', '指定的 Dropbox 文件或目录不存在，或当前账号无法访问。');
      if (response.status === 429) throw fault('RATE_LIMITED', 'Dropbox 请求超出限额，请稍后重试。');
      throw fault('PROVIDER_ERROR', 'Dropbox 服务返回 HTTP ' + response.status + '，请检查应用配置和请求范围。');
    }
    if (raw) return {bytes, metadata: response.headers.get('dropbox-api-result')};
    try { return JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes)); }
    catch { throw fault('INVALID_RESPONSE', 'Dropbox 返回的 JSON 无法完整解析。'); }
  } catch (e) { if (e.safe) throw e; throw fault('NETWORK_ERROR', '无法连接 Dropbox 或请求超时，请检查网络后重试。'); }
}
async function bearer() {
  let s = session(); if (s.expires_at - Date.now() > 60000) return s.access_token;
  // Only one refresh process may rotate this private session at a time.
  const lock = filePath('refresh.lock'); let fd;
  for (let n = 0; n < 60; n++) {
    try { fd = fs.openSync(lock, 'wx', 0o600); fs.writeFileSync(fd, JSON.stringify({pid: process.pid, time: Date.now()})); break; }
    catch (e) {
      if (e.code !== 'EEXIST') throw e;
      const owner = readJSON('refresh.lock'); let alive = true;
      if (owner?.pid) try { process.kill(owner.pid, 0); } catch (x) { if (x.code === 'ESRCH') alive = false; }
      if (!alive) { try { fs.unlinkSync(lock); } catch {} continue; }
      await new Promise(r => setTimeout(r, 100));
    }
  }
  if (fd === undefined) throw fault('REFRESH_BUSY', 'Dropbox 正在刷新授权，请稍后重试。');
  try {
    s = session(); if (s.expires_at - Date.now() > 60000) return s.access_token;
    const result = await request('https://api.dropboxapi.com/oauth2/token', {form: {grant_type: 'refresh_token', refresh_token: s.refresh_token, client_id: s.app_key}});
    return commitToken(result, s.app_key, s.epoch, s).access_token;
  } finally { fs.closeSync(fd); try { fs.unlinkSync(lock); } catch (e) { if (e.code !== 'ENOENT') throw e; } }
}
function rpc(route, args, token) { return request('https://api.dropboxapi.com/2/' + route, {json: args, token}); }
module.exports = {VERSION, SCOPES, REDIRECT, PORT, MAX_TEXT, fault, publicError, stateDir, readJSON, writeJSON, epoch, logout, appKey, configuredKey, scopeCheck, session, commitToken, collect, request, bearer, rpc};
