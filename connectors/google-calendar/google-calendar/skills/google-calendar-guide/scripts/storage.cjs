'use strict';
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), crypto = require('node:crypto');
function error(code, message) { return Object.assign(new Error(message), {code}); }
function directory() {
  const root = process.env.JIUWENSWARM_DATA_DIR || process.env.JIUWENSWARM_HOME || path.join(os.homedir(), '.jiuwenswarm');
  const dir = path.resolve(root, 'connector-data/google-calendar/node-v1');
  for (let p = dir; ; p = path.dirname(p)) {
    if (fs.existsSync(path.join(p, '.git'))) throw error('UNSAFE_STORAGE', '凭据目录须位于源码仓库之外。');
    if (fs.existsSync(p) && fs.lstatSync(p).isSymbolicLink()) throw error('UNSAFE_STORAGE', '凭据目录不能经过符号链接。');
    if (p === path.dirname(p)) break;
  }
  fs.mkdirSync(dir, {recursive: true, mode: 0o700});
  const st = fs.statSync(dir);
  if (process.platform !== 'win32' && (st.uid !== process.getuid() || st.mode & 0o077)) throw error('UNSAFE_STORAGE', '凭据目录须归当前用户所有，权限为 700。');
  return dir;
}
function location(name) { return path.join(directory(), name); }
function read(file, optional = false) {
  let fd;
  try {
    fd = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW || 0) | (fs.constants.O_NONBLOCK || 0));
    const st = fs.fstatSync(fd);
    if (!st.isFile() || st.size > 65536 || process.platform !== 'win32' && (st.uid !== process.getuid() || st.mode & 0o077)) throw new Error();
    return JSON.parse(fs.readFileSync(fd, 'utf8'));
  } catch (e) {
    if (optional && e.code === 'ENOENT') return null;
    throw error('INVALID_CREDENTIALS', '本地配置不可读取，请从卡片重新配置或授权。');
  } finally { if (fd !== undefined) fs.closeSync(fd); }
}
function write(name, value) {
  const dest = location(name), tmp = dest + '.' + crypto.randomBytes(12).toString('hex');
  if (fs.existsSync(dest) && fs.lstatSync(dest).isSymbolicLink()) throw error('UNSAFE_STORAGE', '凭据文件不能是符号链接。');
  try {
    fs.writeFileSync(tmp, JSON.stringify(value), {flag: 'wx', mode: 0o600});
    fs.renameSync(tmp, dest);
  } finally { fs.rmSync(tmp, {force: true}); }
}
function client(value) {
  const v = value?.installed;
  if (!v || typeof v.client_id !== 'string' || !v.client_id.endsWith('.apps.googleusercontent.com') || typeof v.client_secret !== 'string' || !v.client_secret || v.token_uri !== 'https://oauth2.googleapis.com/token' || !['https://accounts.google.com/o/oauth2/auth','https://accounts.google.com/o/oauth2/v2/auth'].includes(v.auth_uri)) throw error('INVALID_CLIENT', '请使用 Google Cloud 创建的 Desktop app OAuth JSON。');
  return {installed: {client_id: v.client_id, client_secret: v.client_secret, token_uri: v.token_uri, auth_uri: v.auth_uri}};
}
function loadClient() {
  const current = read(location('client.json'), true);
  if (current) return client(current);
  // Existing team Workspace config may supply the public Desktop client only;
  // never import or reuse another connector's tokens.
  const legacy = path.join(process.env.WORKSWARM_GOOGLE_WORKSPACE_HOME || path.join(os.homedir(), '.local/share/agentic-hub/google-workspace'), 'client.json');
  const value = read(legacy, true);
  if (value) { const result = client(value); write('client.json', result); return result; }
  return null;
}
module.exports = {directory, location, read, write, client, loadClient, error};
