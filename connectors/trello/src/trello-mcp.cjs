'use strict';

const {createInterface} = require('node:readline');

const API = 'https://api.trello.com/1/';
const VERSION = '1.0.0';
const VALID_PROTOCOLS = ['2025-11-25', '2025-06-18', '2024-11-05'];
const ID = {type: 'string', pattern: '^[0-9a-fA-F]{24}$'};
const QUERY = {type: 'string', minLength: 1, maxLength: 200, description: '名称中的文字。'};
const PAGINATION = {
  offset: {type: 'integer', minimum: 0, maximum: 100_000, default: 0},
  limit: {type: 'integer', minimum: 1, maximum: 100, default: 25},
};
const CARD_FIELDS = 'id,name,desc,idBoard,idList,closed,shortUrl';

function tool(name, description, properties, required = [], readOnly = true) {
  return {
    name,
    description,
    inputSchema: {type: 'object', properties, required, additionalProperties: false},
    annotations: readOnly ? {readOnlyHint: true, openWorldHint: true} :
      {readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true},
  };
}

const TOOLS = [
  tool('trello_status', '检查卡片填入的 Trello Key 和用户令牌是否有效。', {}),
  tool('trello_list_boards', '查询当前用户加入的开放看板，可按名称匹配。', {query: QUERY, ...PAGINATION}),
  tool('trello_list_lists', '查询指定看板的开放列表。', {board_id: ID, query: QUERY, ...PAGINATION}, ['board_id']),
  tool('trello_list_cards', '查询指定列表的开放卡片，可按名称匹配。', {list_id: ID, query: QUERY, ...PAGINATION}, ['list_id']),
  tool('trello_get_card', '按卡片 ID 读取名称、描述、看板和列表。', {card_id: ID}, ['card_id']),
  tool('trello_create_card', '在已确认的看板和列表中新建一张卡片。', {
    board_id: ID,
    list_id: ID,
    name: {type: 'string', minLength: 1, maxLength: 300},
    description: {type: 'string', minLength: 0, maxLength: 8192},
  }, ['board_id', 'list_id', 'name'], false),
];

const SCHEMAS = new Map(TOOLS.map(({name, inputSchema}) => [name, inputSchema]));
function validate(name, args) {
  const schema = SCHEMAS.get(name);
  if (!schema) throw new Error('此连接器不提供该工具。');
  if (!args || typeof args !== 'object' || Array.isArray(args)) throw new Error('参数必须为 JSON 对象。');
  for (const key of schema.required) {
    if (!Object.hasOwn(args, key)) throw new Error('缺少必填参数 ' + key + '。');
  }
  for (const [key, value] of Object.entries(args)) {
    if (!Object.hasOwn(schema.properties, key)) throw new Error('存在不受支持的参数。');
    const rule = schema.properties[key];
    if (rule.type === 'string') {
      if (typeof value !== 'string' || (rule.minLength !== 0 && !value.trim()) ||
          value.length > (rule.maxLength ?? 24) || (rule.pattern && !new RegExp(rule.pattern, 'u').test(value))) {
        throw new Error('参数 ' + key + ' 格式无效。');
      }
    } else if (!Number.isSafeInteger(value) || value < rule.minimum || value > rule.maximum) {
      throw new Error('参数 ' + key + ' 超出允许范围。');
    }
  }
}

function identity(key, token) {
  const apiKey = key?.trim();
  const apiToken = token?.trim();
  if (!apiKey || !apiToken || apiKey.startsWith('$' + '{') || apiToken.startsWith('$' + '{')) {
    throw new Error('请在 WorkSwarm 卡片填写 Trello 应用 API Key 和用户令牌。');
  }
  if (!/^[a-zA-Z0-9_.~+/=-]{8,256}$/u.test(apiKey) || !/^[a-zA-Z0-9_.~+/=-]{8,512}$/u.test(apiToken)) {
    throw new Error('Trello Key 或用户令牌格式无效，请在卡片检查粘贴内容。');
  }
  return 'OAuth oauth_consumer_key="' + apiKey + '", oauth_token="' + apiToken + '"';
}

async function getJson(endpoint, authorization, signal, request, {params = {}, body} = {}) {
  const url = new URL(endpoint, API);
  url.search = new URLSearchParams(params).toString();
  const headers = {Accept: 'application/json', Authorization: authorization};
  const uncertain = 'Trello 创建结果未确认，请先在目标列表查同名卡片，再决定是否重试。';
  let response;
  try {
    if (body) headers['Content-Type'] = 'application/json';
    response = await request(url, {
      method: body ? 'POST' : 'GET', headers, redirect: 'error', signal,
      ...(body && {body: JSON.stringify(body)}),
    });
  } catch {
    throw new Error(body ? uncertain : 'Trello 读取未完成，请检查网络。');
  }
  if (!response.ok) {
    const errors = {
      400: 'Trello 拒绝了请求，请核对看板、列表和卡片参数。',
      401: 'Trello Key 或用户令牌无效或已过期，请从卡片重新连接。',
      403: '当前账号没有访问或写入目标的权限，请核对 Trello 授权和看板角色。',
      404: 'Trello 无法找到目标，或当前账号不能访问。',
      429: 'Trello 请求过于频繁，请稍后查询。',
    };
    throw new Error(errors[response.status] ?? (body ? uncertain : 'Trello 服务暂时无法完成读取。'));
  }

  let size = 0;
  const chunks = [];
  try {
    for await (const chunk of response.body ?? []) {
      size += chunk.byteLength;
      if (size > 4 * 1024 * 1024) break;
      chunks.push(Buffer.from(chunk));
    }
  } catch {
    throw new Error(body ? uncertain : 'Trello 响应传输未完成，请重试。');
  }
  if (size > 4 * 1024 * 1024) throw new Error(body ? uncertain : 'Trello 返回内容过大，请缩小读取范围。');
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error(body ? uncertain : 'Trello 返回了无法读取的响应。');
  }
}

const normalized = value => typeof value === 'string' ? value.normalize('NFKC').toLowerCase() : '';

function page(data, args, map) {
  if (!Array.isArray(data)) throw new Error('Trello 响应缺少列表数据。');
  const needle = normalized(args.query?.trim());
  const matches = data.filter(item => item?.closed !== true && normalized(item?.name).includes(needle));
  const offset = args.offset ?? 0;
  const limit = args.limit ?? 25;
  const end = offset + limit;
  return {
    items: matches.slice(offset, end).map(map), matched: matches.length,
    next_offset: end < matches.length ? end : null,
  };
}

function named(item) {
  if (!item || typeof item.id !== 'string' || typeof item.name !== 'string') {
    throw new Error('Trello 响应缺少对象名称或 ID。');
  }
  return {id: item.id, name: item.name};
}

function trelloLink(value) {
  if (typeof value !== 'string') return null;
  try {
    const url = new URL(value);
    return url.origin === 'https://trello.com' && !url.username && !url.password && /^\/[bc]\//u.test(url.pathname) ?
      url.origin + url.pathname : null;
  } catch {
    return null;
  }
}

function card(item, includeDescription = false) {
  const basic = named(item);
  if (typeof item.idBoard !== 'string' || typeof item.idList !== 'string') {
    throw new Error('Trello 响应缺少卡片所属的看板或列表。');
  }
  return {
    ...basic, board_id: item.idBoard, list_id: item.idList, url: trelloLink(item.shortUrl ?? item.url),
    ...(includeDescription && {description: item.desc ?? '', archived: item.closed === true}),
  };
}

async function perform(name, args, key, token, signal, request = fetch) {
  validate(name, args);
  const authorization = identity(key, token);
  const get = (endpoint, params) => getJson(endpoint, authorization, signal, request, {params});
  if (name === 'trello_status') {
    const member = await get('members/me', {fields: 'id'});
    if (typeof member?.id !== 'string') throw new Error('Trello 未返回当前用户信息。');
    return {connected: true};
  }
  if (name === 'trello_list_boards') {
    return page(await get('members/me/boards', {filter: 'open', fields: 'id,name,shortUrl,closed'}), args,
      item => ({...named(item), url: trelloLink(item.shortUrl)}));
  }
  if (name === 'trello_list_lists') {
    return page(await get('boards/' + args.board_id + '/lists', {filter: 'open', fields: 'id,name,closed'}), args, named);
  }
  if (name === 'trello_list_cards') {
    return page(await get('lists/' + args.list_id + '/cards'), args, item => card(item));
  }
  if (name === 'trello_get_card') {
    return card(await get('cards/' + args.card_id, {fields: CARD_FIELDS}), true);
  }

  const list = await get('lists/' + args.list_id, {fields: 'id,idBoard,closed'});
  if (typeof list?.idBoard !== 'string' || list.idBoard.toLowerCase() !== args.board_id.toLowerCase()) {
    throw new Error('目标列表属于其他看板，请重新核对看板和列表。');
  }
  if (list.closed !== false) throw new Error('目标列表不可写，请检查是否已经归档。');

  const body = {idList: args.list_id, name: args.name.trim()};
  if (args.description !== undefined) body.desc = args.description;
  const result = await getJson('cards', authorization, signal, request, {body});
  if (typeof result?.idBoard !== 'string' || result.idBoard.toLowerCase() !== args.board_id.toLowerCase() ||
      typeof result.idList !== 'string' || result.idList.toLowerCase() !== args.list_id.toLowerCase() ||
      typeof result?.id !== 'string' || typeof result?.name !== 'string') {
    throw new Error('Trello 创建结果未确认，请先在目标列表查同名卡片，再决定是否重试。');
  }
  return card(result, true);
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
        serverInfo: {name: 'trello', version: VERSION},
      });
    }
    if (method === 'ping') return result(id, {});
    if (method === 'tools/list') return result(id, {tools: TOOLS});
    if (method !== 'tools/call') return rpcError(id, -32601, '此连接器仅提供已声明的 Trello 工具。');
    if (active.has(id)) return rpcError(id, -32600, '请求 ID 重复。');

    const control = new AbortController();
    active.set(id, control);
    const signal = AbortSignal.any([control.signal, AbortSignal.timeout(30_000)]);
    try {
      const value = await perform(params?.name, params?.arguments ?? {}, process.env.TRELLO_API_KEY, process.env.TRELLO_API_TOKEN, signal);
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
