import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { randomUUID, createHash } from 'node:crypto';

export const cacheRoot = path.resolve(process.env.CHANGE_VERIFICATION_STATE_DIR || path.join(os.homedir(), '.cache/agentic-hub-change-verification'));
export const digest = value => createHash('sha256').update(value).digest('hex');
export const newID = () => randomUUID().replaceAll('-', '');
export async function directory(dir) {
  await fs.mkdir(dir, { recursive: true, mode: 0o700 });
  const stat = await fs.lstat(dir);
  if (!stat.isDirectory() || stat.isSymbolicLink() || await fs.realpath(dir) !== path.resolve(dir)) throw new Error('缓存目录不能是符号链接。');
  return dir;
}
export async function reportPath(id) {
  if (!/^[a-f0-9]{32}$/.test(id || '')) throw new Error('报告标识无效。');
  return path.join(await directory(path.join(cacheRoot, 'reports')), id + '.json');
}
export async function load(id) {
  const target = await reportPath(id);
  let stat;
  try { stat = await fs.lstat(target); } catch { throw new Error('没有找到该报告，请先查询实际报告标识。'); }
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 18000000) throw new Error('报告文件不可安全读取或超过大小限制。');
  let data;
  try { data = JSON.parse(await fs.readFile(target, 'utf8')); }
  catch (error) { if (error instanceof SyntaxError) throw new Error('报告 JSON 已损坏，未尝试自动重置。'); throw error; }
  if (data.id !== id || data.version !== '1.0.0' || !Array.isArray(data.items)) throw new Error('报告身份或版本不匹配。');
  return data;
}
async function atomic(target, data) {
  const temporary = target + '.' + newID() + '.tmp';
  try {
    await fs.writeFile(temporary, JSON.stringify(data), { flag: 'wx', mode: 0o600 });
    await fs.rename(temporary, target);
  } finally { await fs.rm(temporary, { force: true }); }
}
export async function saveNew(data) {
  const target = await reportPath(data.id);
  await fs.writeFile(target, JSON.stringify(data), { flag: 'wx', mode: 0o600 });
  return data;
}
export async function update(id, revision, mutate) {
  const target = await reportPath(id);
  const lockPath = target + '.lock';
  let lock;
  try { lock = await fs.open(lockPath, 'wx', 0o600); }
  catch { throw new Error('报告正在被另一个操作更新，请刷新后重试；不会覆盖已有结果。'); }
  try {
    const data = await load(id);
    if (!Number.isInteger(revision) || data.revision !== revision) throw new Error('报告版本已变化，请刷新后再保存。');
    mutate(data);
    data.revision += 1;
    data.updated_at = new Date().toISOString();
    if (Buffer.byteLength(JSON.stringify(data)) > 16000000) throw new Error('本报告证据总量已超限，请减少截图。');
    await atomic(target, data);
    return data;
  } finally { await lock.close(); await fs.rm(lockPath, { force: true }); }
}
export async function list() {
  const dir = await directory(path.join(cacheRoot, 'reports'));
  const names = (await fs.readdir(dir)).filter(name => /^[a-f0-9]{32}\.json$/.test(name));
  const selected = [];
  for (const name of names) {
    const stat = await fs.lstat(path.join(dir, name));
    selected.push({ name, time: stat.mtimeMs });
  }
  selected.sort((a, b) => b.time - a.time);
  const reports = [];
  for (const { name } of selected.slice(0, 50)) {
    const report = await load(name.slice(0, -5));
    reports.push({ id: report.id, root: report.root, base: report.base, head: report.head, created_at: report.created_at,
      revision: report.revision, demo: report.demo, counts: counts(report) });
  }
  return { reports, total: names.length, limited: names.length > 50 };
}
export function counts(report) {
  const result = { pending: 0, pass: 0, fail: 0, skip: 0 };
  for (const item of report.items) result[item.status] += 1;
  return result;
}
export function publicReport(report, images = false) {
  return { ...report, counts: counts(report), items: report.items.map(item => ({ ...item,
    screenshots: item.screenshots.map(shot => images ? shot : { name: shot.name, mime: shot.mime, bytes: shot.bytes, sha256: shot.sha256 }) })) };
}
