'use strict';
const crypto = require('node:crypto');
const C = require('./common.cjs');
const OPERATIONS = {
  listFolder: {description: '非递归列出指定目录的一页；有 cursor 时读取下一页', fields: ['path','limit','cursor']},
  searchFiles: {description: '按文件名搜索，可用 path 限定目录；搜索索引可能延迟且不能证明全库完整', fields: ['query','path','limit','cursor']},
  getMetadata: {description: '按文件 ID 或绝对 Dropbox 路径读取元数据', fields: ['path']},
  readText: {description: '完整读取最多 1 MiB UTF-8 文本并核对元数据/内容哈希', fields: ['path']}
};
function text(v, max, label) { if (typeof v !== 'string' || !v || v.length > max || /[\u0000-\u001f\u007f]/.test(v)) throw C.fault('BAD_ARGUMENTS', label + '为空、过长或包含控制字符。'); return v; }
function selector(v, root = false, allowId = true) {
  if (v === '' && root) return '';
  text(v, 4096, '文件或目录路径');
  if (allowId && /^id:[A-Za-z0-9_-]+$/.test(v)) return v;
  if (!v.startsWith('/') || v.includes('\\') || v.split('/').some(x => x === '.' || x === '..') || (v.length > 1 && v.endsWith('/'))) throw C.fault('BAD_ARGUMENTS', '请输入 Dropbox 绝对路径或真实文件 ID。');
  return v;
}
function validate(operation, p) {
  const op = OPERATIONS[operation]; if (!op) throw C.fault('SCOPE_REJECTED', '只开放 listFolder、searchFiles、getMetadata 和 readText 四项读取操作。');
  if (!p || typeof p !== 'object' || Array.isArray(p) || Object.keys(p).some(k => !op.fields.includes(k))) throw C.fault('SCOPE_REJECTED', '请求包含未开放参数。');
  p = {...p};
  if (p.cursor !== undefined) {
    text(p.cursor, 8192, '分页 cursor');
    if (Object.keys(p).length !== 1) throw C.fault('BAD_ARGUMENTS', '分页请求仅传入上一次返回的 cursor。');
    return p;
  }
  if (['getMetadata','readText'].includes(operation)) { p.path = selector(p.path); return p; }
  if (p.limit === undefined) p.limit = 30;
  if (!Number.isInteger(p.limit) || p.limit < 1 || p.limit > 100) throw C.fault('BAD_ARGUMENTS', '每页数量必须是 1 到 100 的整数。');
  p.path = selector(p.path ?? '', true, false);
  if (operation === 'searchFiles') p.query = text(p.query, 1000, '文件名查询');
  return p;
}
function metadata(m) {
  if (!m || !['file','folder'].includes(m['.tag']) || typeof m.id !== 'string' || typeof m.name !== 'string') throw C.fault('INVALID_RESPONSE', 'Dropbox 未返回有效的文件或目录元数据。');
  return Object.fromEntries(['.tag','id','name','path_display','path_lower','size','rev','content_hash','is_downloadable'].filter(k => m[k] !== undefined).map(k => [k, m[k]]));
}
function page(r, entries) {
  if (!Array.isArray(entries) || typeof r.has_more !== 'boolean' || (r.has_more && (typeof r.cursor !== 'string' || !r.cursor))) throw C.fault('INVALID_RESPONSE', 'Dropbox 分页响应不完整。');
  return {entries: entries.map(metadata), has_more: r.has_more, cursor: r.has_more ? r.cursor : null, complete_page: true};
}
function contentHash(bytes) {
  const chunks = []; for (let i = 0; i < bytes.length; i += 4 * C.MAX_TEXT) chunks.push(crypto.createHash('sha256').update(bytes.subarray(i, i + 4 * C.MAX_TEXT)).digest());
  return crypto.createHash('sha256').update(Buffer.concat(chunks)).digest('hex');
}
function verifyRead(before, download) {
  let after;
  try {
    // Download returns FileMetadata, whereas get_metadata returns a tagged union.
    const value = JSON.parse(download.metadata);
    if (!value || typeof value !== 'object' || Array.isArray(value) || (value['.tag'] !== undefined && value['.tag'] !== 'file')) throw Error();
    after = metadata({...value, '.tag': 'file'});
  } catch { throw C.fault('READ_UNVERIFIED', 'Dropbox 下载没有可核验的元数据，不能声称全文读取成功。'); }
  const b = download.bytes;
  if (after['.tag'] !== 'file' || before.id !== after.id || before.rev !== after.rev || !Number.isInteger(before.size) || b.length !== before.size || b.length !== after.size || b.length > C.MAX_TEXT || !/^[a-f0-9]{64}$/.test(after.content_hash || '') || before.content_hash !== after.content_hash || contentHash(b) !== after.content_hash) throw C.fault('READ_UNVERIFIED', '文件版本、长度或内容哈希不一致，请重新读取；未返回未经核对的正文。');
  let value; try { value = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(b); } catch { throw C.fault('NOT_UTF8', '此连接器只读取完整 UTF-8 文本，不解析二进制文件。'); }
  if (value.includes('\u0000')) throw C.fault('NOT_TEXT', '文件含 NUL 字符，不能按普通文本返回。');
  return {metadata: after, bytes: b.length, text: value, full_read: true, truncated: false, sha256: crypto.createHash('sha256').update(b).digest('hex'), dropbox_content_hash_verified: true};
}
async function execute(operation, params, deps = C) {
  const p = validate(operation, params), token = await deps.bearer();
  if (operation === 'listFolder') {
    const r = await deps.rpc(p.cursor ? 'files/list_folder/continue' : 'files/list_folder', p.cursor ? {cursor: p.cursor} : {path: p.path, recursive: false, include_deleted: false, limit: p.limit}, token);
    return page(r, r.entries);
  }
  if (operation === 'searchFiles') {
    const r = await deps.rpc(p.cursor ? 'files/search/continue_v2' : 'files/search_v2', p.cursor ? {cursor: p.cursor} : {query: p.query, options: {filename_only: true, max_results: p.limit, path: p.path}, match_field_options: {include_highlights: false}}, token);
    if (!Array.isArray(r.matches)) throw C.fault('INVALID_RESPONSE', 'Dropbox 搜索响应不完整。');
    return {...page(r, r.matches.map(x => x.metadata?.metadata)), filename_only: true, search_index_may_be_incomplete: true};
  }
  const m = metadata(await deps.rpc('files/get_metadata', {path: p.path}, token));
  if (operation === 'getMetadata') return m;
  if (m['.tag'] !== 'file' || m.is_downloadable === false) throw C.fault('NOT_DOWNLOADABLE', '此对象不是可下载的普通文件；不导出云文档。');
  if (!Number.isInteger(m.size) || m.size < 0 || m.size > C.MAX_TEXT) throw C.fault('TOO_LARGE', '仅支持最多 1 MiB 的完整 UTF-8 文本，未开始下载。');
  const arg = JSON.stringify({path: m.id}).replace(/[\u007f-\uffff]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
  const download = await deps.request('https://content.dropboxapi.com/2/files/download', {token, headers: {'Dropbox-API-Arg': arg}, raw: true});
  return verifyRead(m, download);
}
module.exports = {OPERATIONS, validate, metadata, contentHash, verifyRead, execute};
