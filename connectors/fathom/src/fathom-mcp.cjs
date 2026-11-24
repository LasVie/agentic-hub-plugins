'use strict';

const {createInterface} = require('node:readline');

const API = 'https://api.fathom.ai/external/v1/';
const VERSION = '1.0.1';
const MAX_RESPONSE_BYTES = 16 * 1024 * 1024;
const VALID_PROTOCOLS = ['2025-11-25', '2025-06-18', '2024-11-05'];
const RECORDING_ID = {type: 'string', pattern: '^[1-9][0-9]{0,18}$'};
const SHARE_LINK = String.raw`https://(?:www\.)?fathom\.(?:video|ai)/share/[^\s<>)"']+`;
const DATE = {
  type: 'string',
  description: 'UTC 日期 YYYY-MM-DD 或带时区的 ISO 8601 时间。',
  maxLength: 35,
};

function tool(name, description, properties, required = []) {
  return {
    name,
    description,
    inputSchema: {type: 'object', properties, required, additionalProperties: false},
    annotations: {readOnlyHint: true, destructiveHint: false, openWorldHint: true},
  };
}

const TOOLS = [
  tool('fathom_status', '使用 Fathom 会议接口检查卡片的 API Key 是否有效，只返回连接状态。', {}),
  tool('fathom_search_meetings', '按标题匹配 Fathom 会议的当前服务页，可按创建时间过滤并继续翻页。返回录制 ID。', {
    query: {type: 'string', minLength: 1, maxLength: 240, description: '标题中的文字。省略时列出当前页。'},
    created_after: DATE,
    created_before: DATE,
    cursor: {type: 'string', minLength: 1, maxLength: 4096, description: '上次返回的 next_cursor。'},
  }),
  tool('fathom_read_summary', '读取指定 Fathom 录制会议的现有摘要。', {
    recording_id: RECORDING_ID,
  }, ['recording_id']),
  tool('fathom_read_transcript', '读取指定 Fathom 录制会议的逐字稿原文、说话者与时间戳，按条分页。', {
    recording_id: RECORDING_ID,
    offset: {type: 'integer', minimum: 0, maximum: 1_000_000, default: 0},
    limit: {type: 'integer', minimum: 1, maximum: 50, default: 25},
  }, ['recording_id']),
];

const SCHEMAS = new Map(TOOLS.map(({name, inputSchema}) => [name, inputSchema]));

function validate(name, args) {
  const schema = SCHEMAS.get(name);
  if (!schema) throw new Error('此连接器不提供该工具。');
  if (!args || typeof args !== 'object' || Array.isArray(args)) {
    throw new Error('参数必须为 JSON 对象。');
  }
  for (const key of schema.required) {
    if (!Object.hasOwn(args, key)) throw new Error('缺少必填参数 ' + key + '。');
  }
  for (const [key, value] of Object.entries(args)) {
    if (!Object.hasOwn(schema.properties, key)) throw new Error('不支持参数 ' + key + '。');
    const rule = schema.properties[key];
    if (rule.type === 'string') {
      if (typeof value !== 'string' || !value.trim() || value.length > (rule.maxLength ?? 4096) ||
          (rule.pattern && !new RegExp(rule.pattern, 'u').test(value))) {
        throw new Error('参数 ' + key + ' 格式无效。');
      }
    } else if (!Number.isSafeInteger(value) || value < rule.minimum || value > rule.maximum) {
      throw new Error('参数 ' + key + ' 超出允许范围。');
    }
  }
}

function utcTimestamp(value) {
  if (!value) return undefined;
  if (!/^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2}))?$/u.test(value)) {
    throw new Error('日期须为 UTC 日期或带时区的 ISO 8601 时间。');
  }
  const day = value.slice(0, 10);
  const midnight = new Date(day);
  const timestamp = new Date(value);
  if (!Number.isFinite(+timestamp) || !Number.isFinite(+midnight) ||
      midnight.toISOString().slice(0, 10) !== day || value.slice(11, 13) === '24') {
    throw new Error('日期无效。');
  }
  return timestamp.toISOString();
}

async function getJson(url, apiKey, signal, request) {
  let response;
  try {
    response = await request(url, {
      method: 'GET',
      redirect: 'error',
      signal,
      headers: {Accept: 'application/json', 'X-Api-Key': apiKey},
    });
  } catch {
    throw new Error('Fathom 请求未完成，请检查网络或稍后重试。');
  }
  if (!response.ok) {
    const errors = {
      400: 'Fathom 拒绝了查询参数，请核对日期、游标或录制 ID。',
      401: 'Fathom API Key 无效，请在 WorkSwarm 卡片重新填写。',
      403: 'Fathom 拒绝访问，请核对 API Key 和账号的录制访问权限。',
      404: '当前账号无法读取这条录制或内容尚不可用，请核对录制 ID。',
      429: 'Fathom 请求过于频繁，请稍后重试。',
    };
    throw new Error(errors[response.status] ?? 'Fathom 服务暂时无法完成请求。');
  }

  const chunks = [];
  let size = 0;
  try {
    for await (const chunk of response.body ?? []) {
      size += chunk.byteLength;
      if (size > MAX_RESPONSE_BYTES) break;
      chunks.push(Buffer.from(chunk));
    }
  } catch {
    throw new Error('Fathom 响应传输未完成，请稍后重试。');
  }
  if (size > MAX_RESPONSE_BYTES) throw new Error('Fathom 响应超过大小限制。');
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error('Fathom 返回了无法读取的响应。');
  }
}

function meetingRecord(item) {
  const rawId = item?.recording_id;
  if ((typeof rawId !== 'string' && !Number.isSafeInteger(rawId)) ||
      !/^[1-9][0-9]{0,18}$/u.test(String(rawId))) {
    throw new Error('Fathom 会议结果缺少有效的录制 ID。');
  }
  return {
    recording_id: String(rawId),
    title: item.title ?? item.meeting_title ?? null,
    meeting_title: item.meeting_title ?? null,
    created_at: item.created_at ?? null,
    recording_start_time: item.recording_start_time ?? null,
    url: item.url ?? null,
  };
}

function titleText(value) {
  return typeof value === 'string' ? value.normalize('NFKC').toLowerCase() : '';
}

function removeRecordingShareLinks(markdown) {
  const linkedLabel = new RegExp(String.raw`\[([^\]\r\n]+)\]\(<?` + SHARE_LINK + String.raw`>?\)`, 'giu');
  return markdown.replace(linkedLabel, '$1').replace(new RegExp(SHARE_LINK, 'giu'), '[分享链接已省略]');
}

async function search(args, apiKey, signal, request) {
  const url = new URL('meetings', API);
  const after = utcTimestamp(args.created_after);
  const before = utcTimestamp(args.created_before);
  if (after && before && after >= before) throw new Error('结束时间须晚于开始时间。');
  if (after) url.searchParams.set('created_after', after);
  if (before) url.searchParams.set('created_before', before);
  if (args.cursor) url.searchParams.set('cursor', args.cursor);

  const data = await getJson(url, apiKey, signal, request);
  if (!Array.isArray(data?.items)) throw new Error('Fathom 响应缺少会议列表。');
  const query = titleText(args.query?.trim());
  const matches = data.items.filter(item =>
    titleText(item?.title).includes(query) || titleText(item?.meeting_title).includes(query)
  );
  return {
    meetings: matches.map(meetingRecord),
    scanned: data.items.length,
    next_cursor: typeof data.next_cursor === 'string' && data.next_cursor.length &&
      data.next_cursor !== args.cursor ? data.next_cursor : null,
  };
}

async function perform(name, args, key, signal, request = fetch) {
  validate(name, args);
  const apiKey = key?.trim();
  if (!apiKey || apiKey === '$' + '{FATHOM_API_KEY}') {
    throw new Error('请先在 WorkSwarm 的 Fathom 连接器卡片填写 API Key。');
  }

  if (name === 'fathom_status') {
    const data = await getJson(new URL('meetings', API), apiKey, signal, request);
    if (!Array.isArray(data?.items)) throw new Error('Fathom 响应缺少会议列表。');
    return {connected: true};
  }
  if (name === 'fathom_search_meetings') return search(args, apiKey, signal, request);

  const recording_id = args.recording_id;
  if (name === 'fathom_read_summary') {
    const data = await getJson(new URL('recordings/' + recording_id + '/summary', API), apiKey, signal, request);
    if (data?.summary === null) return {recording_id, available: false};
    if (typeof data?.summary?.markdown_formatted !== 'string') {
      throw new Error('Fathom 响应缺少摘要内容。');
    }
    const summary = removeRecordingShareLinks(data.summary.markdown_formatted);
    return {recording_id, available: Boolean(summary.trim()), summary};
  }

  const data = await getJson(new URL('recordings/' + recording_id + '/transcript', API), apiKey, signal, request);
  if (data?.transcript === null) return {recording_id, available: false};
  if (!Array.isArray(data?.transcript)) throw new Error('Fathom 响应缺少逐字稿。');
  const offset = args.offset ?? 0;
  const segments = data.transcript.slice(offset, offset + (args.limit ?? 25)).map(item => {
    if (typeof item?.text !== 'string' || typeof item.timestamp !== 'string') {
      throw new Error('Fathom 返回的逐字稿片段不完整。');
    }
    return {speaker: item.speaker?.display_name ?? null, text: item.text, timestamp: item.timestamp};
  });
  const next = offset + segments.length;
  return {
    recording_id,
    available: data.transcript.length > 0,
    total: data.transcript.length,
    offset,
    segments,
    next_offset: next < data.transcript.length ? next : null,
  };
}

function start() {
  const active = new Map();
  const send = data => process.stdout.write(JSON.stringify({jsonrpc: '2.0', ...data}) + '\n');
  const result = (id, value) => send({id, result: value});
  const rpcError = (id, code, message) => send({id, error: {code, message}});
  const input = createInterface({input: process.stdin, crlfDelay: Infinity});
  input.on('close', () => {
    for (const control of active.values()) control.abort();
  });
  input.on('line', async line => {
    if (Buffer.byteLength(line) > 1024 * 1024) return rpcError(null, -32600, 'MCP 消息过大。');
    let message;
    try {
      message = JSON.parse(line);
    } catch {
      return rpcError(null, -32700, 'MCP JSON 解析失败。');
    }
    if (message?.jsonrpc !== '2.0' || typeof message.method !== 'string') {
      return rpcError(null, -32600, '无效的 MCP 请求。');
    }
    const {id, method, params} = message;
    if (id === undefined) {
      if (method === 'notifications/cancelled') active.get(params?.requestId)?.abort();
      return;
    }
    if (typeof id !== 'string' && typeof id !== 'number') return rpcError(null, -32600, '无效的请求 ID。');
    if (method === 'initialize') {
      const protocol = params?.protocolVersion;
      return result(id, {
        protocolVersion: VALID_PROTOCOLS.includes(protocol) ? protocol : VALID_PROTOCOLS[0],
        capabilities: {tools: {}},
        serverInfo: {name: 'fathom', version: VERSION},
      });
    }
    if (method === 'ping') return result(id, {});
    if (method === 'tools/list') return result(id, {tools: TOOLS});
    if (method !== 'tools/call') return rpcError(id, -32601, '此连接器仅提供已声明的 Fathom 工具。');
    if (active.has(id)) return rpcError(id, -32600, '请求 ID 重复。');

    const control = new AbortController();
    active.set(id, control);
    const signal = AbortSignal.any([control.signal, AbortSignal.timeout(30_000)]);
    try {
      const value = await perform(params?.name, params?.arguments ?? {}, process.env.FATHOM_API_KEY, signal);
      result(id, {content: [{type: 'text', text: JSON.stringify(value)}]});
    } catch (error) {
      result(id, {isError: true, content: [{type: 'text', text: error.message}]});
    } finally {
      active.delete(id);
    }
  });
}

module.exports = {perform, TOOLS};
if (!require.main || require.main === module) start();
