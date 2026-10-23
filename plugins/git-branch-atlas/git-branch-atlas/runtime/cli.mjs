import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import config from './config.mjs';
import { context, InputError, object } from './common.mjs';
import { execute } from './engine.mjs';

async function readRegistry(ctx) {
  const f = path.join(ctx.dir, 'ui-session.json');
  try {
    if (fs.lstatSync(f).isSymbolicLink() || fs.statSync(f).size > 4096) return null;
    const r = JSON.parse(fs.readFileSync(f, 'utf8'));
    if (!Number.isInteger(r.port) || r.port < 1024 || r.port > 65535 || !/^[a-f0-9]{64}$/.test(r.token)) return null;
    const response = await fetch(`http://127.0.0.1:${r.port}/health`, { signal: AbortSignal.timeout(1200), redirect: 'error' });
    const h = await response.json();
    return h.ok && h.slug === config.slug && h.bundle_id === config.bundle_id ? r : null;
  } catch { return null; }
}
async function ui(ctx, stop = false) {
  let record = await readRegistry(ctx);
  if (stop) {
    if (!record) return { message: '当前没有可用的交互服务；数据已保留。' };
    const r = await fetch(`http://127.0.0.1:${record.port}/stop`, { method: 'POST', headers: { authorization: `Bearer ${record.token}`, 'content-type': 'application/json' }, body: '{}', signal: AbortSignal.timeout(2000) });
    const v = await r.json(); if (!v.ok) throw new InputError(v.message); return v;
  }
  if (!record) {
    const lock = path.join(ctx.dir, 'ui-open.lock'); let fd;
    try { fd = fs.openSync(lock, 'wx', 0o600); } catch (e) { if (e.code !== 'EEXIST') throw e; }
    if (fd !== undefined) {
      try {
        const p = spawn(process.execPath, ['--no-warnings', '--experimental-sqlite', '--experimental-strip-types', path.join(path.dirname(fileURLToPath(import.meta.url)), 'server.mjs'), ctx.root], { detached: true, stdio: 'ignore', env: { PATH: process.env.PATH || '/usr/bin:/bin:/usr/sbin', LANG: 'en_US.UTF-8' } });
        p.on('error', () => {}); p.unref();
        for (let i = 0; i < 40 && !record; i++) { await new Promise(r => setTimeout(r, 100)); record = await readRegistry(ctx); }
      } finally { fs.closeSync(fd); fs.unlinkSync(lock); }
    } else {
      for (let i = 0; i < 40 && !record; i++) { await new Promise(r => setTimeout(r, 100)); record = await readRegistry(ctx); }
      if (!record && fs.existsSync(lock) && Date.now() - fs.statSync(lock).mtimeMs > 30000) { if (fs.lstatSync(lock).isFile()) fs.unlinkSync(lock); }
    }
  }
  if (!record) throw new InputError('交互服务未能启动，请确认 Node.js 22.6+ 支持 SQLite 与类型擦除，稍后重试。');
  return { message: '中文交互工作台已就绪。链接仅供本机访问，请勿分享凭据；空闲 30 分钟自动关闭。', ui_url: `http://127.0.0.1:${record.port}/#${record.token}` };
}
let ctx;
try {
  let input = ''; for await (const chunk of process.stdin) { input += chunk; if (Buffer.byteLength(input) > 256000) throw new InputError('输入过大。'); }
  const q = JSON.parse(input);
  if (!object(q) || !object(q.payload || {}) || !['open_ui', 'stop_ui', 'help', ...config.actions].includes(q.action)) throw new InputError('输入或操作不正确。');
  ctx = context(q.workspace_dir, config);
  const result = q.action === 'help' ? { description: config.description, actions: config.help } : q.action === 'open_ui' || q.action === 'stop_ui' ? await ui(ctx, q.action === 'stop_ui') : await execute(ctx, q.action, q.payload || {});
  console.log(JSON.stringify({ ok: true, plugin: config.slug, version: config.version, ...result }));
} catch (e) {
  console.log(JSON.stringify({ ok: false, message: e instanceof InputError ? e.message : e instanceof SyntaxError ? 'JSON 格式不正确。' : '本地操作失败，请检查运行环境与权限；未确认保存成功。' }));
} finally { ctx?.close(); }
