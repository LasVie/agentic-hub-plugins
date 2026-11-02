import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import { TextDecoder } from 'node:util';
import { isIndexedSource } from '../vendor/deps.js';

const run = promisify(execFile);
export const limits = Object.freeze({ tracked: 5000, indexed: 1500, blob: 262144, total: 16777216, changed: 100, items: 200, depth: 3 });
export function gitEnvironment() {
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('GIT_')));
  return { ...env, GIT_CONFIG_NOSYSTEM: '1', GIT_CONFIG_GLOBAL: '/dev/null', GIT_TERMINAL_PROMPT: '0',
    GIT_NO_LAZY_FETCH: '1', GIT_NO_REPLACE_OBJECTS: '1', GIT_OPTIONAL_LOCKS: '0', GIT_LITERAL_PATHSPECS: '1', LC_ALL: 'C' };
}
export async function git(root, args, maxBuffer = 4000000) {
  try {
    const result = await run('git', ['--no-pager', '-c', 'core.fsmonitor=false', '-c', 'core.hooksPath=/dev/null',
      '-c', 'core.quotePath=false', ...args], { cwd: root, env: gitEnvironment(), encoding: 'buffer', maxBuffer, timeout: 20000 });
    return result.stdout;
  } catch (error) {
    if (error.code === 'ENOENT') throw new Error('未找到本地 Git；请先确认系统已安装 Git。');
    throw new Error('Git 读取失败：请检查仓库、提交是否本地可用，以及文件规模是否超限。未拉取远程、修改安全配置或执行项目代码。');
  }
}
export function safePath(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 800 && !value.includes('\\') &&
    !/[\x00-\x1f\x7f]/.test(value) && !path.posix.isAbsolute(value) &&
    !value.split('/').some(part => !part || part === '..' || part === '.' || part.startsWith('.')) &&
    !/(?:^|\/)(?:node_modules|vendor|dist|build|coverage)(?:\/|$)/.test(value) &&
    !/(?:^|\/)(?:credentials|secrets?)(?:[./]|$)|\.(?:pem|key|p12|pfx)$/i.test(value);
}
function utf8(buffer) {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(buffer); }
  catch { throw new Error('Git 输出包含不支持的非 UTF-8 路径。'); }
}
export async function repository(root) {
  if (typeof root !== 'string' || !path.isAbsolute(root) || root.length > 1000) throw new Error('请提供明确授权的本地仓库绝对路径；不接受远程地址。');
  let actual;
  try { actual = await fs.realpath(root); } catch { throw new Error('本地仓库路径不存在或不可访问。'); }
  if (actual === path.parse(actual).root) throw new Error('不能将磁盘根目录作为分析项目。');
  const top = utf8(await git(actual, ['rev-parse', '--show-toplevel'])).trim();
  if (await fs.realpath(top) !== actual) throw new Error('请明确指定 Git 仓库顶层目录，不自动扩大扫描范围。');
  return actual;
}
export async function resolve(root, ref) {
  if (typeof ref !== 'string' || !ref || ref.length > 180 || ref.startsWith('-') || /[\s\x00-\x1f]/.test(ref)) throw new Error('提交引用格式无效。');
  const sha = utf8(await git(root, ['rev-parse', '--verify', '--end-of-options', ref + '^{commit}'])).trim();
  if (!/^[a-f0-9]{40}(?:[a-f0-9]{24})?$/.test(sha)) throw new Error('未能解析出本地提交对象。');
  return sha;
}
export async function changed(root, base, head) {
  const parts = utf8(await git(root, ['diff', '--no-ext-diff', '--no-textconv', '--no-renames', '--name-status', '-z', base, head, '--'])).split('\0');
  const changes = [];
  while (parts.length > 1) {
    const status = parts.shift();
    const file = parts.shift();
    if (!/^[ADMTUXB]$/.test(status) || !file) throw new Error('不支持的 Git 差异记录。');
    changes.push({ path: file, status });
  }
  if (changes.length > limits.changed) throw new Error(`变更超过 ${limits.changed} 个文件，请缩小提交范围。`);
  return changes;
}
export async function snapshot(root, sha) {
  const raw = await git(root, ['ls-tree', '-r', '-z', '-l', sha, '--'], 8000000);
  const entries = utf8(raw).split('\0').filter(Boolean);
  if (entries.length > limits.tracked) throw new Error(`提交树超过 ${limits.tracked} 个路径，请缩小项目。`);
  const files = new Map();
  const omissions = {};
  const omit = key => { omissions[key] = (omissions[key] || 0) + 1; };
  let bytes = 0;
  const candidates = [];
  for (const record of entries) {
    const match = record.match(/^(\d+) (\w+) ([a-f0-9]+)\s+(\d+|-|BAD)\t([\s\S]*)$/);
    if (!match) throw new Error('提交树格式无法解析。');
    const [, mode, type, oid, sizeText, file] = match;
    if (!safePath(file) || !isIndexedSource(file)) { omit('保护路径或不支持的类型'); continue; }
    if (!/^100(?:644|755)$/.test(mode) || type !== 'blob') { omit('符号链接或子模块'); continue; }
    if (sizeText === 'BAD') throw new Error('所选提交包含本地缺失的源码对象。请先在正常 Git 工作流中备妥提交内容；本插件不会联网补齐或用工作区代替。');
    const size = Number(sizeText);
    if (size > limits.blob) { omit('单文件超限'); continue; }
    if (candidates.length >= limits.indexed || bytes + size > limits.total) { omit('索引数量或总字节超限'); continue; }
    candidates.push({ file, oid, size }); bytes += size;
  }
  for (let start = 0; start < candidates.length; start += 8) {
    const contents = await Promise.all(candidates.slice(start, start + 8).map(async ({ file, oid }) => {
      const buffer = await git(root, ['cat-file', 'blob', oid], limits.blob + 1024);
      if (buffer.includes(0)) { omit('二进制内容'); return null; }
      try { return [file, new TextDecoder('utf-8', { fatal: true }).decode(buffer)]; }
      catch { omit('非 UTF-8 内容'); return null; }
    }));
    for (const entry of contents) if (entry) files.set(...entry);
  }
  return { files, counts: { tree_count: entries.length, indexed_count: files.size, indexed_bytes: bytes, omissions } };
}
