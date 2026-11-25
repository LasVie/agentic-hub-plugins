'use strict';

const {createInterface} = require('node:readline');

const ENDPOINT = 'https://api.monday.com/v2';
const API_VERSION = '2026-10';
const VERSION = '1.1.0';
const PROTOCOLS = ['2025-11-25', '2025-06-18', '2024-11-05'];
const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
const UNKNOWN_WRITE = 'monday.com 创建结果未确认。请先在同一看板查找同名条目，再决定是否重试。';
const AUTH_FAILURE = 'monday.com 无法验证访问令牌。请检查卡片凭据和该账号的 API 访问限制。';
const PERMISSION_FAILURE = 'monday.com 拒绝访问。请核对当前账号对目标看板或条目的权限。';
const INVALID_RESPONSE = 'monday.com 返回的数据格式不完整。';
const ID = {type: 'string', pattern: '^[1-9][0-9]{0,31}$'};

function tool(name, description, properties, required = [], readOnly = true) {
  return {
    name, description,
    inputSchema: {type: 'object', properties, required, additionalProperties: false},
    annotations: readOnly
      ? {readOnlyHint: true, openWorldHint: true}
      : {readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: true},
  };
}

const TOOLS = [
  tool('monday_status', '检查卡片中保存的 monday.com 个人访问令牌是否有效。', {}),
  tool('monday_list_board_items', '列出指定看板的条目。需要下一页时传入上次从相同看板获得的游标。', {
    board_id: ID,
    limit: {type: 'integer', minimum: 1, maximum: 100, default: 25},
    cursor: {type: 'string', minLength: 1, maxLength: 8192},
  }, ['board_id']),
  tool('monday_read_item', '按条目 ID 读取标题、列文本和所属看板。回读写入时传入原看板 ID 核对。', {
    item_id: ID, board_id: ID,
  }, ['item_id']),
  tool('monday_create_item', '在用户指定且确认的看板上创建一条新条目，只填写标题。', {
    board_id: ID, title: {type: 'string', minLength: 1, maxLength: 255},
  }, ['board_id', 'title'], false),
];

const OPERATIONS = {
  monday_status: 'query CurrentUser { me { id } }',
  first_page: `query BoardItems($board: ID!, $limit: Int!) {
    boards(ids: [$board]) { id name items_page(limit: $limit) { cursor items { id name url board { id } } } }
  }`,
  next_page: `query NextBoardItems($cursor: String!, $limit: Int!) {
    next_items_page(cursor: $cursor, limit: $limit) { cursor items { id name url board { id } } }
  }`,
  monday_read_item: `query ReadItem($item: ID!) {
    items(ids: [$item]) { id name url board { id } column_values { id text } }
  }`,
  monday_create_item: `mutation CreateItem($board: ID!, $title: String!) {
    create_item(board_id: $board, item_name: $title) { id name url board { id } }
  }`,
};

const SCHEMAS = new Map(TOOLS.map(({name, inputSchema}) => [name, inputSchema]));
const NUMERIC_ID = new RegExp(ID.pattern, 'u');
const isRecord = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const hasId = value => typeof value === 'string' && NUMERIC_ID.test(value);

function validate(name, args) {
  const schema = SCHEMAS.get(name);
  if (!schema) throw new Error('此连接器仅提供已声明的 monday.com 工具。');
  if (!isRecord(args)) throw new Error('工具参数必须为 JSON 对象。');
  for (const key of schema.required) {
    if (!Object.hasOwn(args, key)) throw new Error('缺少参数 ' + key + '。');
  }
  for (const [key, value] of Object.entries(args)) {
    if (!Object.hasOwn(schema.properties, key)) throw new Error('存在不受支持的参数。');
    const spec = schema.properties[key];
    const valid = spec.type === 'integer'
      ? Number.isSafeInteger(value) && value >= spec.minimum && value <= spec.maximum
      : spec.pattern
        ? hasId(value)
        : typeof value === 'string' && value.trim().length > 0 && value.length <= spec.maxLength &&
          !/[\u0000-\u001f\u007f]/u.test(value);
    if (!valid) throw new Error('参数 ' + key + ' 格式或范围无效。');
  }
}

function credential(raw) {
  const token = raw?.trim();
  if (!token || token.startsWith('$' + '{')) {
    throw new Error('请在 WorkSwarm 卡片填写 monday.com 个人访问令牌。');
  }
  if (!/^[!-~]+$/u.test(token) || token.includes('@')) {
    throw new Error('令牌格式无效。请从 monday.com API token 页面复制完整令牌。');
  }
  return token;
}

const HTTP_ERRORS = {
  400: 'monday.com 拒绝了查询或输入，请核对 API 版本和参数。',
  401: AUTH_FAILURE,
  403: PERMISSION_FAILURE,
  404: 'monday.com 找不到目标资源，或当前账号无法访问。',
  429: 'monday.com 请求过于频繁。请等待配额恢复后再试。',
};

const GRAPHQL_ERRORS = {
  UserUnauthorizedException: PERMISSION_FAILURE,
  USER_ACCESS_DENIED: PERMISSION_FAILURE,
  InvalidBoardIdException: HTTP_ERRORS[404],
  InvalidItemIdException: HTTP_ERRORS[404],
  ResourceNotFoundException: HTTP_ERRORS[404],
  InvalidVersionException: HTTP_ERRORS[400],
  GRAPHQL_VALIDATION_FAILED: HTTP_ERRORS[400],
  ComplexityException: HTTP_ERRORS[429],
};

function providerError(value, writing) {
  if (writing && value.data?.create_item) return UNKNOWN_WRITE;
  for (const error of value.errors) {
    const ext = error?.extensions;
    const code = ext?.code ?? error?.error_code;
    const status = ext?.status_code ?? error?.status_code;
    if (Object.hasOwn(GRAPHQL_ERRORS, code)) return GRAPHQL_ERRORS[code];
    if (Object.hasOwn(HTTP_ERRORS, status)) return HTTP_ERRORS[status];
  }
  return writing ? UNKNOWN_WRITE : 'monday.com 未完成此查询，请核对看板、条目和额度。';
}

async function requestData(key, variables, token, signal, request) {
  const writing = key === 'monday_create_item';
  let response;
  try {
    response = await request(ENDPOINT, {
      method: 'POST', redirect: 'error', signal,
      headers: {Authorization: token, 'Content-Type': 'application/json', 'API-Version': API_VERSION},
      body: JSON.stringify({query: OPERATIONS[key], variables}),
    });
  } catch {
    throw new Error(writing ? UNKNOWN_WRITE : '无法连接 monday.com，请检查网络后重试。');
  }
  if (!response.ok) {
    await response.body?.cancel().catch(() => {});
    throw new Error(HTTP_ERRORS[response.status] ?? (writing ? UNKNOWN_WRITE : 'monday.com 服务暂时不可用。'));
  }
  const chunks = [];
  let received = 0;
  let value;
  try {
    for await (const chunk of response.body) {
      received += chunk.byteLength;
      if (received > MAX_RESPONSE_BYTES) throw new Error();
      chunks.push(Buffer.from(chunk));
    }
    value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw new Error(writing ? UNKNOWN_WRITE : 'monday.com 返回内容过大、传输中断或格式无效。');
  }
  if (Array.isArray(value?.errors) && value.errors.length) throw new Error(providerError(value, writing));
  if (!isRecord(value?.data)) throw new Error(writing ? UNKNOWN_WRITE : INVALID_RESPONSE);
  return value.data;
}

function itemLink(raw) {
  if (typeof raw !== 'string') return null;
  try {
    const url = new URL(raw);
    if (url.protocol === 'https:' && !url.port && !url.username && !url.password &&
        (url.hostname === 'monday.com' || url.hostname.endsWith('.monday.com'))) {
      return url.origin + url.pathname;
    }
  } catch {
    return null;
  }
  return null;
}

function item(value) {
  if (!hasId(value?.id) || !hasId(value?.board?.id) || typeof value.name !== 'string') {
    throw new Error(INVALID_RESPONSE);
  }
  return {id: value.id, title: value.name, board_id: value.board.id, url: itemLink(value.url)};
}

function page(value, boardId) {
  if (!Array.isArray(value?.items) || (value.cursor !== null && typeof value.cursor !== 'string')) {
    throw new Error(INVALID_RESPONSE);
  }
  const items = value.items.map(item);
  if (items.some(entry => entry.board_id !== boardId)) {
    throw new Error('游标或条目与指定看板不一致，请从该看板第一页重新查询。');
  }
  return {board_id: boardId, items, next_cursor: value.cursor};
}

async function perform(name, args, rawToken, signal, request = fetch) {
  validate(name, args);
  const token = credential(rawToken);
  const call = (operation, variables = {}) => requestData(operation, variables, token, signal, request);
  if (name === 'monday_status') {
    const data = await call(name);
    if (!hasId(data.me?.id)) throw new Error(INVALID_RESPONSE);
    return {connected: true, api_version: API_VERSION};
  }
  if (name === 'monday_list_board_items') {
    const limit = args.limit ?? 25;
    if (args.cursor) {
      const data = await call('next_page', {cursor: args.cursor, limit});
      return page(data.next_items_page, args.board_id);
    }
    const data = await call('first_page', {board: args.board_id, limit});
    const board = Array.isArray(data.boards) && data.boards.find(entry => entry?.id === args.board_id);
    if (!board) throw new Error(HTTP_ERRORS[404]);
    if (typeof board.name !== 'string') throw new Error(INVALID_RESPONSE);
    return {...page(board.items_page, args.board_id), board_name: board.name};
  }
  if (name === 'monday_read_item') {
    const data = await call(name, {item: args.item_id});
    const found = Array.isArray(data.items) && data.items.find(entry => entry?.id === args.item_id);
    if (!found || (args.board_id && found.board?.id !== args.board_id)) throw new Error(HTTP_ERRORS[404]);
    const columns = Array.isArray(found.column_values) ? found.column_values : [];
    return {...item(found), columns: columns.map(column => ({
      id: column.id, text: typeof column.text === 'string' ? column.text : null,
    }))};
  }
  const title = args.title.trim();
  const data = await call(name, {board: args.board_id, title});
  try {
    const created = item(data.create_item);
    if (created.board_id !== args.board_id || created.title !== title) throw new Error();
    return created;
  } catch {
    throw new Error(UNKNOWN_WRITE);
  }
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
        protocolVersion: PROTOCOLS.includes(protocol) ? protocol : PROTOCOLS[0],
        capabilities: {tools: {}},
        serverInfo: {name: 'monday', version: VERSION},
      });
    }
    if (method === 'ping') return result(id, {});
    if (method === 'tools/list') return result(id, {tools: TOOLS});
    if (method !== 'tools/call') return rpcError(id, -32601, '此连接器仅提供已声明的 monday.com 工具。');
    if (active.has(id)) return rpcError(id, -32600, '请求 ID 重复。');

    const control = new AbortController();
    active.set(id, control);
    const signal = AbortSignal.any([control.signal, AbortSignal.timeout(30_000)]);
    try {
      const value = await perform(params?.name, params?.arguments ?? {}, process.env.MONDAY_PERSONAL_TOKEN, signal);
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
