import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { spawnSync } from 'node:child_process';

export class InputError extends Error {}
export const fail = message => { throw new InputError(message); };
export const object = v => v !== null && typeof v === 'object' && !Array.isArray(v);
export function text(v, label, max = 2000, empty = false) {
  if (typeof v !== 'string' || (!empty && !v.trim()) || v.length > max || v.includes('\0')) fail(`${label}须为${empty ? '可为空的' : '非空'}文本，最多 ${max} 字。`);
  return v.trim();
}
export function integer(v, label, min, max) {
  if (!Number.isSafeInteger(v) || v < min || v > max) fail(`${label}须为 ${min} 至 ${max} 的整数。`);
  return v;
}
export const id = (v, label = '编号') => { if (typeof v !== 'string' || !/^[a-z][a-z0-9-]{0,47}$/.test(v)) fail(`${label}须为小写字母开头的字母、数字或短横线，最长 48 字。`); return v; };
export const hash = v => crypto.createHash('sha256').update(v).digest('hex');
export const now = () => new Date().toISOString();
export const token = () => crypto.randomBytes(32).toString('hex');
export function safeDir(parent, name) {
  const p = path.join(parent, name);
  try { fs.mkdirSync(p, { mode: 0o700 }); } catch (e) { if (e.code !== 'EEXIST') throw e; }
  if (fs.lstatSync(p).isSymbolicLink() || !fs.statSync(p).isDirectory() || fs.realpathSync(p) !== p) fail('插件数据目录不能是符号链接。');
  return p;
}
export function workspace(value) {
  if (typeof value !== 'string' || !path.isAbsolute(value)) fail('工作目录须为已存在目录的绝对路径。');
  const p = fs.realpathSync(value);
  if (!fs.statSync(p).isDirectory()) fail('工作目录不存在。');
  return p;
}
export function within(root, value, directory = false) {
  if (typeof value !== 'string' || !value || path.isAbsolute(value) || /[\x00-\x1f]/.test(value)) fail('路径须为工作目录内的相对路径。');
  if (value.split(/[\\/]/).includes('..')) fail('路径不能向上穿越。');
  const target = fs.realpathSync(path.resolve(root, value));
  if (target !== root && !target.startsWith(root + path.sep)) fail('路径越出工作目录。');
  if (directory ? !fs.statSync(target).isDirectory() : !fs.statSync(target).isFile()) fail('目标文件或目录类型不正确。');
  return target;
}
export function run(command, args, cwd, timeout = 8000) {
  const env = { PATH: process.env.PATH || '/usr/bin:/bin:/usr/sbin', LANG: 'en_US.UTF-8', LC_ALL: 'C', GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: process.platform === 'win32' ? 'NUL' : '/dev/null', GIT_OPTIONAL_LOCKS: '0', GIT_NO_LAZY_FETCH: '1', GIT_TERMINAL_PROMPT: '0', GIT_PAGER: 'cat' };
  const r = spawnSync(command, args, { cwd, env, encoding: 'utf8', shell: false, timeout, maxBuffer: 2 * 1024 * 1024, stdio: ['ignore', 'pipe', 'pipe'] });
  return { ok: !r.error && r.status === 0, stdout: r.stdout || '', status: r.status, reason: r.error?.code === 'ETIMEDOUT' ? '命令超时' : r.error?.code === 'ENOENT' ? '命令未安装' : r.error ? '命令不可用' : r.status === 0 ? '' : '命令未成功，可能权限不足或目录不适用' };
}
export function context(rootValue, config) {
  const root = workspace(rootValue);
  const dir = safeDir(safeDir(root, '.agentic-hub-plugins'), config.slug);
  const dbPath = path.join(dir, 'state.sqlite');
  if (fs.existsSync(dbPath) && (fs.lstatSync(dbPath).isSymbolicLink() || fs.statSync(dbPath).size > 30 * 1024 * 1024)) fail('本地数据库路径或大小不安全。');
  const db = new DatabaseSync(dbPath);
  fs.chmodSync(dbPath, 0o600);
  db.exec('PRAGMA busy_timeout=5000; PRAGMA journal_mode=DELETE; CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), revision INTEGER NOT NULL, data TEXT NOT NULL);');
  db.prepare('INSERT OR IGNORE INTO state VALUES (1,0,?)').run(JSON.stringify(config.initial));
  function read() {
    const row = db.prepare('SELECT revision,data FROM state WHERE id=1').get();
    let state; try { state = JSON.parse(row.data); } catch { fail('本地记录损坏；已停止，不会覆盖原记录。'); }
    if (!object(state) || state.schema !== 1) fail('本地记录版本不兼容；不会覆盖原记录。');
    return { revision: row.revision, state };
  }
  return { root, dir, db, read, close: () => db.close(), mutate(expected, fn) {
    integer(expected, '预期版本 expected_revision', 0, Number.MAX_SAFE_INTEGER);
    db.exec('BEGIN IMMEDIATE');
    try {
      const current = read();
      if (current.revision !== expected) fail('记录已有更新，请刷新后重试；本次没有覆盖新内容。');
      const result = fn(current.state);
      const data = JSON.stringify(current.state);
      if (Buffer.byteLength(data) > 12 * 1024 * 1024) fail('工作区记录已超过容量上限，请先导出整理。');
      db.prepare('UPDATE state SET revision=?,data=? WHERE id=1').run(expected + 1, data);
      db.exec('COMMIT');
      return { ...result, revision: expected + 1 };
    } catch (e) { db.exec('ROLLBACK'); throw e; }
  } };
}
