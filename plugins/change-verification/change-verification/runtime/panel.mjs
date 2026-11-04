import http from 'node:http';
import fs from 'node:fs/promises';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { load, publicReport } from './store.mjs';
import { result } from './engine.mjs';
import { html, markdown, csv } from './export.mjs';

let server;
let ready;
let address;
const token = randomBytes(32).toString('hex');
const assets = new Map([['/', ['index.html', 'text/html; charset=utf-8']], ['/app.js', ['app.js', 'text/javascript; charset=utf-8']], ['/style.css', ['style.css', 'text/css; charset=utf-8']]]);
function permitted(request) {
  const candidate = request.headers.authorization || '';
  const expected = 'Bearer ' + token;
  return Buffer.byteLength(candidate) === Buffer.byteLength(expected) && timingSafeEqual(Buffer.from(candidate), Buffer.from(expected));
}
function send(response, status, data, type = 'application/json; charset=utf-8') {
  response.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer', 'Cross-Origin-Resource-Policy': 'same-origin',
    'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'" });
  response.end(typeof data === 'string' || Buffer.isBuffer(data) ? data : JSON.stringify(data));
}
async function body(request) {
  const chunks = [];
  let bytes = 0;
  for await (const chunk of request) {
    bytes += chunk.length;
    if (bytes > 4500000) throw new Error('请求超过截图或备注大小限制。');
    chunks.push(chunk);
  }
  try { return JSON.parse(Buffer.concat(chunks).toString('utf8')); }
  catch { throw new Error('请求必须是有效 JSON。'); }
}
async function handle(request, response) {
  try {
    if (request.headers.host !== address.slice('http://'.length)) return send(response, 403, { ok: false, message: '拒绝不匹配的本地主机。' });
    if (request.headers.origin && request.headers.origin !== address) return send(response, 403, { ok: false, message: '拒绝跨站请求。' });
    const url = new URL(request.url, address);
    const asset = assets.get(url.pathname);
    if (asset && request.method === 'GET') return send(response, 200, await fs.readFile(fileURLToPath(new URL('../ui/' + asset[0], import.meta.url))), asset[1]);
    if (!permitted(request)) return send(response, 403, { ok: false, message: '缺少有效面板访问令牌，请通过插件重新打开。' });
    if (url.pathname === '/api/report' && request.method === 'GET') return send(response, 200, { ok: true, report: publicReport(await load(url.searchParams.get('id')), true) });
    if (url.pathname === '/api/result' && request.method === 'POST') {
      if (!/^application\/json(?:;|$)/i.test(request.headers['content-type'] || '')) throw new Error('保存结果必须使用 JSON 请求。');
      return send(response, 200, { ok: true, report: publicReport(await result(await body(request)), true) });
    }
    if (url.pathname === '/api/export' && request.method === 'GET') {
      const report = await load(url.searchParams.get('id'));
      const format = url.searchParams.get('format');
      if (!['html', 'markdown', 'csv', 'json'].includes(format)) throw new Error('不支持的导出格式。');
      const content = format === 'html' ? html(report) : format === 'markdown' ? markdown(report) : format === 'csv' ? csv(report) : JSON.stringify(publicReport(report, true), null, 2);
      return send(response, 200, { ok: true, content, name: `回归报告-${report.id.slice(0, 8)}-r${report.revision}.` + ({ markdown: 'md' }[format] || format) });
    }
    return send(response, 404, { ok: false, message: '该操作不存在。' });
  } catch (error) {
    return send(response, 400, { ok: false, message: error instanceof SyntaxError ? '报告或请求格式无效。' : error.message || '本地操作失败。' });
  }
}
export async function panelURL(id) {
  if (!ready) ready = new Promise((resolve, reject) => {
    server = http.createServer((request, response) => { void handle(request, response); });
    server.headersTimeout = 10000;
    server.requestTimeout = 20000;
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      address = 'http://127.0.0.1:' + server.address().port;
      resolve();
    });
  });
  await ready;
  return `${address}/?report=${encodeURIComponent(id)}#${token}`;
}
export async function closePanel() {
  if (!server) return;
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
