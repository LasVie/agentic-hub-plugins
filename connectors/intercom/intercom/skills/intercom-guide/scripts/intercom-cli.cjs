'use strict';

const fs = require('node:fs');
const {VERSION, failure, checkTools, readTool} = require('./intercom-mcp.cjs');
const {privateDirectory, login, logout, useSession} = require('./intercom-auth.cjs');

function command(args) {
  const [mode, flag, file] = args;
  if (mode === 'search' || mode === 'fetch') {
    if (args.length !== 3 || flag !== '--input-file') {
      throw failure('BAD_ARGUMENTS', '搜索和读取请提供 --input-file 参数文件.json。');
    }
    const info = fs.statSync(file);
    if (!info.isFile() || info.size > 16384) throw failure('BAD_ARGUMENTS', '参数文件须为小于 16 KiB 的 UTF-8 JSON。');
    let data;
    try { data = JSON.parse(fs.readFileSync(file, 'utf8')); }
    catch { throw failure('BAD_ARGUMENTS', '请提供有效的 UTF-8 JSON 参数。'); }
    return {mode, input: readArguments(mode, data)};
  }
  if (args.length !== 1 || !['prepare', 'version', 'login', 'logout', 'status'].includes(mode)) {
    throw failure('BAD_ARGUMENTS', '支持 prepare、version、login、logout、status、search、fetch。');
  }
  return {mode};
}

function readArguments(mode, data) {
  if (!data || typeof data !== 'object' || Array.isArray(data) || Object.keys(data).length !== 1) {
    throw failure('BAD_ARGUMENTS', '参数必须是只含一个字段的 JSON 对象。');
  }
  if (mode === 'search') {
    const {query} = data;
    if (typeof query !== 'string' || query.length > 2000 || /[\r\n\u0000]/.test(query) ||
        !/^object_type:(conversations|contacts)(?: |$)/.test(query)) {
      throw failure('BAD_ARGUMENTS', '请提供 query，并以 object_type:conversations 或 object_type:contacts 开头。');
    }
    return {query};
  }
  const {id} = data;
  if (typeof id !== 'string' || !/^(conversation_\d{1,32}|contact_[A-Za-z0-9_-]{1,128})$/.test(id)) {
    throw failure('BAD_ARGUMENTS', '请提供搜索返回的 conversation_ 或 contact_ 资源标识。');
  }
  return {id};
}

const publicErrors = new Set(['AUTH_REQUIRED', 'AUTH_DENIED', 'OAUTH_FAILED', 'NETWORK_ERROR', 'INVALID_RESPONSE',
  'PERMISSION_DENIED', 'SERVICE_FAILED', 'TOOL_FAILED', 'BAD_ARGUMENTS', 'RESULT_TOO_LARGE', 'STORAGE_ERROR',
  'TIMEOUT', 'CANCELLED', 'BUSY']);

function print(value) {
  console.log(JSON.stringify(value));
}

async function main(args = process.argv.slice(2)) {
  let heartbeat;
  try {
    const {mode, input} = command(args);
    if (mode === 'version') return console.log(VERSION);
    const dir = privateDirectory();
    if (mode === 'prepare') return print({ok: true, message: 'Intercom 运行环境已就绪。'});
    if (mode === 'logout') {
      await logout(dir);
      return print({ok: true, connected: false, message: '本机连接已断开。远端授权可在 Intercom 管理。'});
    }
    if (mode === 'login') {
      heartbeat = setInterval(() => console.log('等待 Intercom 浏览器授权…'), 10000);
      const region = await login(dir, url => console.log(url));
      return print({ok: true, connected: true, region, message: 'Intercom 已授权，并已核对可用工具。'});
    }
    if (mode === 'status') {
      await useSession(dir, checkTools);
      return print({ok: true, connected: true, message: 'Intercom 授权有效。'});
    }
    const result = await useSession(dir, rpc => readTool(rpc, mode, input));
    print({ok: true, operation: mode, result});
  } catch (error) {
    const known = publicErrors.has(error.code);
    print({ok: false, connected: false, code: known ? error.code : 'CLIENT_FAILED',
      message: known ? error.message : 'Intercom 操作未完成，请检查参数、网络和连接状态。'});
    if (args[0] !== 'status') process.exitCode = 1;
  } finally {
    clearInterval(heartbeat);
  }
}

module.exports = {main, readArguments};
if (require.main === module) main();
