'use strict';

const CLIENT = 'WorkSwarm Intercom Connector';
const VERSION = '1.0.0';
const origins = new Map([
  ['us', 'https://mcp.intercom.com'],
  ['eu', 'https://mcp.eu.intercom.com'],
]);
const allowedTools = new Set(['search', 'fetch']);
const versions = new Set(['2025-03-26', '2025-06-18', '2025-11-25']);
const limitBytes = 2 * 1024 * 1024;

function failure(code, message) {
  return Object.assign(new Error(message), {code});
}

function origin(region) {
  if (!origins.has(region)) throw failure('BAD_ARGUMENTS', '请选择美区或欧区。');
  return origins.get(region);
}

async function request(url, options, timeout = 12000) {
  try {
    return await fetch(url, {
      ...options,
      headers: {'User-Agent': 'WorkSwarm-Intercom-Connector/' + VERSION, ...options.headers},
      redirect: 'error',
      signal: AbortSignal.timeout(timeout),
    });
  } catch {
    throw failure('NETWORK_ERROR', '无法访问 Intercom，请检查网络后重试。');
  }
}

async function readResponse(response, id) {
  if (!response.body) throw failure('INVALID_RESPONSE', 'Intercom 未返回结果。');
  const sse = (response.headers.get('content-type') || '').startsWith('text/event-stream');
  let text = '', size = 0;
  const reader = response.body.getReader(), decoder = new TextDecoder();
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limitBytes) throw failure('RESULT_TOO_LARGE', 'Intercom 返回内容过大，请缩小查询范围。');
      text += decoder.decode(value, {stream: true});
      if (!sse) continue;
      let separator;
      while ((separator = /\r?\n\r?\n/.exec(text))) {
        const event = text.slice(0, separator.index);
        text = text.slice(separator.index + separator[0].length);
        const data = event.split(/\r?\n/).filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
        if (!data) continue;
        const message = JSON.parse(data);
        if (message.jsonrpc === '2.0' && message.id === id) return message;
      }
    }
    if (!sse) return JSON.parse(text + decoder.decode());
    throw failure('INVALID_RESPONSE', 'Intercom 未返回对应的 MCP 结果。');
  } finally {
    await reader.cancel().catch(() => {});
  }
}

async function oauthPost(region, endpoint, body) {
  const form = body instanceof URLSearchParams;
  const response = await request(origin(region) + endpoint, {
    method: 'POST',
    headers: {Accept: 'application/json', 'Content-Type': form ? 'application/x-www-form-urlencoded' : 'application/json'},
    body: form ? body : JSON.stringify(body),
  });
  const payload = await readResponse(response);
  if (!response.ok) {
    if (payload.error === 'invalid_grant') throw failure('AUTH_REQUIRED', 'Intercom 授权已失效，请从卡片重新连接。');
    throw failure('OAUTH_FAILED', 'Intercom 拒绝了授权请求，请核对工作区地区后重试。');
  }
  return payload;
}

async function withMcp(region, token, action) {
  const url = origin(region) + '/mcp';
  const headers = {Authorization: 'Bearer ' + token, Accept: 'application/json, text/event-stream',
    'Content-Type': 'application/json'};
  let nextId = 0;

  async function rpc(method, params, notification = false) {
    const id = notification ? undefined : ++nextId;
    const response = await request(url, {method: 'POST', headers, body: JSON.stringify({jsonrpc: '2.0', id, method, params})});
    if (!response.ok || notification) {
      await response.body?.cancel().catch(() => {});
      if (response.status === 401) throw failure('AUTH_REQUIRED', 'Intercom 授权已失效，请从卡片重新连接。');
      if (response.status === 403) throw failure('PERMISSION_DENIED', '当前 Intercom 账号或工作区没有此权限。');
      if (!response.ok) throw failure('SERVICE_FAILED', 'Intercom 请求失败（HTTP ' + response.status + '）。');
      return;
    }
    if (method === 'initialize') {
      const session = response.headers.get('mcp-session-id');
      if (session) headers['Mcp-Session-Id'] = session;
    }
    const message = await readResponse(response, id);
    if (message?.jsonrpc !== '2.0' || message.id !== id || message.error || !message.result) {
      throw failure('SERVICE_FAILED', 'Intercom MCP 未能完成此请求。');
    }
    return message.result;
  }

  try {
    const session = await rpc('initialize', {
      protocolVersion: '2025-06-18', capabilities: {}, clientInfo: {name: CLIENT, version: VERSION},
    });
    if (!versions.has(session.protocolVersion) || !session.capabilities?.tools) {
      throw failure('SERVICE_FAILED', '当前 Intercom MCP 版本或工具不可用。');
    }
    headers['MCP-Protocol-Version'] = session.protocolVersion;
    await rpc('notifications/initialized', undefined, true);
    return await action(rpc);
  } finally {
    if (headers['Mcp-Session-Id']) {
      await request(url, {method: 'DELETE', headers}, 1500)
        .then(r => r.body?.cancel()).catch(() => {});
    }
  }
}

async function checkTools(rpc) {
  const seen = new Set(), found = new Set();
  let cursor;
  do {
    const page = await rpc('tools/list', cursor ? {cursor} : {});
    for (const tool of page.tools ?? []) {
      if (allowedTools.has(tool.name)) found.add(tool.name);
    }
    cursor = page.nextCursor;
    if (found.size === allowedTools.size) return;
    if (cursor && (seen.has(cursor) || seen.size >= 9)) break;
    if (cursor) seen.add(cursor);
  } while (cursor);
  throw failure('SERVICE_FAILED', '此工作区未提供必需的 Intercom 搜索和读取工具。');
}

async function readTool(rpc, name, args) {
  if (!allowedTools.has(name)) throw failure('BAD_ARGUMENTS', '此连接器只开放搜索和读取。');
  const result = await rpc('tools/call', {name, arguments: args});
  if (result.isError) throw failure('TOOL_FAILED', 'Intercom 未能完成查询，请核对条件、资源标识和账号权限。');
  if (result.structuredContent !== undefined) return result.structuredContent;
  const text = (result.content ?? []).filter(item => item.type === 'text').map(item => item.text);
  if (text.length === 1) {
    try { return JSON.parse(text[0]); } catch { return text[0]; }
  }
  return text;
}

module.exports = {CLIENT, VERSION, origin, failure, oauthPost, readResponse, withMcp, checkTools, readTool};
