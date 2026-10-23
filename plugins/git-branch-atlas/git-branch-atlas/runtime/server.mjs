import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { context, token, InputError, object } from './common.mjs';
import config from './config.mjs';
import { execute } from './engine.mjs';

const ctx = context(process.argv[2], config);
const key = token();
const ui = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../ui');
const registry = path.join(ctx.dir, 'ui-session.json');
let lastUse = Date.now();
const started = lastUse;
const serve = (res, code, body, type = 'application/json') => {
  const b = Buffer.from(type === 'application/json' ? JSON.stringify(body) : body);
  res.writeHead(code, { 'Content-Type': type + '; charset=utf-8', 'Content-Length': b.length, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY', 'Referrer-Policy': 'no-referrer', 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; form-action 'self'; base-uri 'none'" });
  res.end(b);
};
let closing = false;
function close() {
  if (closing) return;
  closing = true;
  try { const saved = JSON.parse(fs.readFileSync(registry, 'utf8')); if (saved.token === key) fs.unlinkSync(registry); } catch {}
  server.close(() => { ctx.close(); process.exit(0); });
  setTimeout(() => process.exit(0), 1500).unref();
}
const server = http.createServer(async (req, res) => {
  const host = `127.0.0.1:${server.address().port}`;
  if (req.headers.host !== host || req.socket.remoteAddress !== '127.0.0.1') return serve(res, 403, { ok: false, message: '仅允许本机回环访问。' });
  const pathname = (req.url || '').split('?')[0];
  if (req.method === 'GET') {
    if (pathname === '/health') return serve(res, 200, { ok: true, slug: config.slug, version: config.version, bundle_id: config.bundle_id });
    const files = { '/': ['index.html', 'text/html'], '/app.js': ['app.js', 'text/javascript'], '/style.css': ['style.css', 'text/css'] };
    if (!files[pathname]) return serve(res, 404, { ok: false, message: '页面不存在。' });
    const [name, type] = files[pathname];
    return serve(res, 200, fs.readFileSync(path.join(ui, name)), type);
  }
  if (req.method !== 'POST' || !['/api', '/stop'].includes(pathname)) return serve(res, 405, { ok: false, message: '请求方式不支持。' });
  if (req.headers.authorization !== `Bearer ${key}` || (req.headers.origin && req.headers.origin !== `http://${host}`) || req.headers['content-type'] !== 'application/json') return serve(res, 403, { ok: false, message: '访问凭据或来源不正确，请从工具返回的完整链接重新打开。' });
  const length = Number(req.headers['content-length']);
  if (!Number.isSafeInteger(length) || length < 2 || length > 256000) return serve(res, 413, { ok: false, message: '请求过大或长度不正确。' });
  try {
    let body = ''; for await (const piece of req) { body += piece; if (Buffer.byteLength(body) > 256000) throw new InputError('请求过大。'); }
    const q = JSON.parse(body);
    if (!object(q) || 'workspace_dir' in q) throw new InputError('请求只能操作绑定的工作目录。');
    lastUse = Date.now();
    if (pathname === '/stop') { serve(res, 200, { ok: true, message: '交互窗口服务已关闭；数据已保留。' }); return close(); }
    if (!config.actions.includes(q.action)) throw new InputError('操作不支持，请查看中文帮助。');
    const out = await execute(ctx, q.action, q.payload || {});
    serve(res, 200, { ok: true, plugin: config.slug, version: config.version, ...out });
  } catch (e) { serve(res, e instanceof SyntaxError ? 400 : 200, { ok: false, message: e instanceof InputError ? e.message : '本地操作失败；未确认保存成功。' }); }
});
server.requestTimeout = 15000;
server.headersTimeout = 10000;
server.maxRequestsPerSocket = 100;
server.listen(0, '127.0.0.1', () => {
  const record = { token: key, port: server.address().port, slug: config.slug, version: config.version, bundle_id: config.bundle_id, started_at: new Date().toISOString() };
  const tmp = registry + '.' + process.pid;
  fs.writeFileSync(tmp, JSON.stringify(record), { mode: 0o600 }); fs.renameSync(tmp, registry);
});
setInterval(() => { if (Date.now() - lastUse > 30 * 60 * 1000 || Date.now() - started > 4 * 60 * 60 * 1000) close(); }, 30000).unref();
process.on('SIGTERM', close); process.on('SIGINT', close);
