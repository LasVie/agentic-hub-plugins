'use strict';
const http = require('node:http');
const crypto = require('node:crypto');
const C = require('./common.cjs');
const LOGIN_MS = 30 * 60 * 1000;
const esc = v => String(v).replace(/[&<>"']/g, x => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x]));
function flow(key, manual, expectedEpoch) {
  C.appKey(key); const verifier = crypto.randomBytes(48).toString('base64url'), state = crypto.randomBytes(32).toString('base64url');
  const url = new URL('https://www.dropbox.com/oauth2/authorize');
  const p = {client_id: key, response_type: 'code', state, code_challenge_method: 'S256', code_challenge: crypto.createHash('sha256').update(verifier).digest('base64url'), scope: C.SCOPES.join(' '), token_access_type: 'offline'};
  if (!manual) p.redirect_uri = C.REDIRECT;
  for (const [k,v] of Object.entries(p)) url.searchParams.set(k,v);
  return {key, manual, expectedEpoch, verifier, state, url: url.toString(), used: false};
}
function same(a, b) { return typeof a === 'string' && typeof b === 'string' && a.length === b.length && crypto.timingSafeEqual(Buffer.from(a),Buffer.from(b)); }
async function formBody(req, origin) {
  if (req.headers.origin !== origin || !String(req.headers['content-type'] || '').startsWith('application/x-www-form-urlencoded')) throw C.fault('BAD_ORIGIN', '请从当前本机连接页提交。');
  const size = Number(req.headers['content-length']); if (!Number.isInteger(size) || size < 1 || size > 4096) throw C.fault('BAD_ARGUMENTS', '本机表单大小不正确。');
  const parts = []; let n = 0;
  for await (const part of req) { n += part.length; if (n > 4096) throw C.fault('BAD_ARGUMENTS','本机表单过大。'); parts.push(part); }
  return new URLSearchParams(Buffer.concat(parts).toString('utf8'));
}
async function exchange(auth, code, deps = C) {
  if (!auth || auth.used || typeof code !== 'string' || !/^[!-~]{8,2048}$/.test(code)) throw C.fault('BAD_CALLBACK', 'Dropbox 授权码无效或已使用，请从卡片重新连接。');
  auth.used = true;
  const form = {grant_type: 'authorization_code', code, client_id: auth.key, code_verifier: auth.verifier};
  if (!auth.manual) form.redirect_uri = C.REDIRECT;
  const token = await deps.request('https://api.dropboxapi.com/oauth2/token', {form});
  deps.scopeCheck(token.scope);
  const account = await deps.rpc('users/get_current_account', null, token.access_token);
  if (typeof account?.account_id !== 'string' || !account.account_id) throw C.fault('AUTH_UNVERIFIED','Dropbox 账号验证未完成，未保存凭据。');
  deps.commitToken(token, auth.key, auth.expectedEpoch);
  return {ok: true, connected: true, account_id: account.account_id, scope: C.SCOPES, message: 'Dropbox 授权与账号验证成功。'};
}
function login({onUrl = () => {}, port = C.PORT, lifetime = LOGIN_MS, deps = C} = {}) {
  const gateHost = '127.0.0.1:' + port, callbackHost = 'localhost:' + port, origin = 'http://' + gateHost;
  const route = '/' + crypto.randomBytes(24).toString('hex'), expectedEpoch = deps.epoch();
  let auth, finished = false;
  return new Promise((resolve, reject) => {
    let timer;
    const server = http.createServer(async (req,res) => {
      const respond = (status, body, location) => {
        res.writeHead(status, {'Content-Type': 'text/html; charset=utf-8','Cache-Control':'no-store','Referrer-Policy':'same-origin','X-Content-Type-Options':'nosniff','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self' https://www.dropbox.com; base-uri 'none'; frame-ancestors 'none'",...(location?{Location:location}:{})});
        res.end('<!doctype html><meta charset="utf-8"><title>连接 Dropbox</title><style>body{font:16px system-ui;max-width:740px;margin:48px auto;padding:20px;line-height:1.7}input{width:90%;padding:10px}button{margin:12px 12px 0 0;padding:10px}code{overflow-wrap:anywhere}</style>' + body);
      };
      const done = (error, result) => {
        if (finished) return; finished = true; clearTimeout(timer);
        const close = () => { server.close(); server.closeAllConnections(); error ? reject(error) : resolve(result); };
        if (res.writableFinished) setImmediate(close); else res.once('finish', () => setImmediate(close));
      };
      try {
        if (finished) { respond(410,'<p>连接已结束，请返回 WorkSwarm。</p>'); return; }
        const host = req.headers.host;
        if (![gateHost,callbackHost].includes(host)) { respond(403,'<p>只允许本机连接。</p>'); return; }
        const target = new URL(req.url, 'http://' + host);
        if (req.method === 'GET' && host === callbackHost && target.pathname === '/oauth/callback') {
          const p = target.searchParams;
          if (!auth || auth.manual || p.getAll('state').length !== 1 || !same(p.get('state'),auth.state) || p.getAll('code').length > 1 || p.getAll('error').length > 1 || (p.has('code') && p.has('error'))) { respond(400,'<p>回调校验失败，请使用当前卡片的授权入口。</p>'); return; }
          if (p.has('error')) {
            const error = C.fault(p.get('error') === 'access_denied' ? 'AUTH_DENIED':'AUTH_FAILED','Dropbox 授权已拒绝或取消，可以从卡片重新连接。');
            respond(400,'<p>Dropbox 授权已拒绝或取消。请返回 WorkSwarm。</p>'); done(error); return;
          }
          try { const result = await exchange(auth,p.get('code'),deps); respond(200,'<h1>Dropbox 授权完成</h1><p>账号已验证。请返回 WorkSwarm。</p>'); done(null,result); }
          catch (e) { respond(400,'<p>'+esc(C.publicError(e).message)+'</p><p>请返回 WorkSwarm 重新连接。</p>'); done(e); }
          return;
        }
        if (host !== gateHost || target.search) { respond(400,'<p>本机连接入口不正确。</p>'); return; }
        if (req.method === 'GET' && target.pathname === route) {
          const key = deps.configuredKey() || '';
          respond(200,'<h1>连接 Dropbox 文件</h1><p>使用你或团队维护的 Dropbox API 应用；App key 是公开标识，请勿填写 App secret、授权码或访问令牌。</p><p>在开发者控制台启用 <code>'+C.SCOPES.join('、')+'</code>，登记回调 <code>'+C.REDIRECT+'</code> 并启用 Public clients。读取已有文件时选 Full Dropbox；App folder 只能读取自己的应用目录。Development 应用只允许它已开放的用户。</p><form method="post" action="'+route+'/config"><label>公开 App key<input name="app_key" value="'+esc(key)+'" required minlength="5" maxlength="128" autocomplete="off"></label><button name="mode" value="redirect">保存并前往 Dropbox 授权</button><button name="mode" value="manual">回调不可用，使用一次性授权码</button></form><p>本机入口最长等待 30 分钟。取消请返回 WorkSwarm 点「取消连接」。本次只申请账号资料和文件读取，不申请上传、修改、删除或共享。</p><p><a href="https://docs.dropboxapi.com/dropbox-api/docs/oauth" target="_blank" rel="noopener noreferrer">Dropbox 官方配置说明</a></p>'); return;
        }
        if (req.method === 'POST' && target.pathname === route + '/config') {
          const p = await formBody(req,origin);
          if (p.getAll('app_key').length !== 1 || p.getAll('mode').length !== 1 || !['redirect','manual'].includes(p.get('mode'))) throw C.fault('BAD_ARGUMENTS','请选择授权方式并填写公开 App key。');
          const key = deps.appKey(p.get('app_key').trim());
          deps.writeJSON('app.json',{app_key:key}); auth = flow(key,p.get('mode') === 'manual',expectedEpoch);
          respond(303,'<p>正在前往授权入口。</p>',route+(auth.manual?'/manual':'/authorize')); return;
        }
        if (req.method === 'GET' && target.pathname === route + '/authorize' && auth && !auth.manual && !auth.used) { respond(302,'<p>正在前往 Dropbox 官方授权页。</p>',auth.url); return; }
        if (req.method === 'GET' && target.pathname === route + '/manual' && auth?.manual && !auth.used) {
          respond(200,'<h1>Dropbox 一次性授权码</h1><p><a href="'+esc(auth.url)+'" target="_blank" rel="noopener noreferrer">前往 Dropbox 获取授权码</a></p><p>在官方页面同意后，将显示的授权码只填到本页，不要发到聊天。</p><form method="post" action="'+route+'/code"><label>一次性授权码<input name="code" type="password" required autocomplete="off" maxlength="2048"></label><button>完成连接</button></form>'); return;
        }
        if (req.method === 'POST' && target.pathname === route + '/code' && auth?.manual) {
          const p = await formBody(req,origin); if (p.getAll('code').length !== 1) throw C.fault('BAD_ARGUMENTS','请填写一次性授权码。');
          try { const result = await exchange(auth,p.get('code'),deps); respond(200,'<h1>Dropbox 授权完成</h1><p>请返回 WorkSwarm。</p>'); done(null,result); }
          catch (e) { respond(400,'<p>'+esc(C.publicError(e).message)+'</p>'); done(e); } return;
        }
        respond(404,'<p>连接入口不存在。</p>');
      } catch (e) { if (!res.headersSent) respond(400,'<p>'+esc(C.publicError(e).message)+'</p>'); }
    });
    server.requestTimeout = 10000; server.headersTimeout = 5000;
    server.on('error', () => { if (finished) return; finished = true; clearTimeout(timer); reject(C.fault('CALLBACK_BUSY','无法监听 Dropbox 本机端口 53682，请关闭占用它的旧连接后重试。')); });
    server.listen(port,'127.0.0.1',() => {
      onUrl(origin+route);
      timer = setTimeout(() => { if (finished) return; finished = true; server.close(); server.closeAllConnections(); reject(C.fault('AUTH_TIMEOUT','Dropbox 授权超时，请从卡片重新连接。')); },lifetime);
    });
  });
}
module.exports = {LOGIN_MS, flow, same, formBody, exchange, login};
