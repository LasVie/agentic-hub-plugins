'use strict';

const {error} = require('./storage.cjs');

const GRAPH = 'https://graph.microsoft.com';
const VIEW = '/v1.0/me/calendar/calendarView';
const EVENT = '/v1.0/me/calendar/events/';
const FIELDS = 'id,subject,start,end,isAllDay,isCancelled,location,webLink';
const PERMISSION = 'Calendars.ReadBasic';
const SCOPE = 'offline_access https://graph.microsoft.com/' + PERMISSION;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/iu;

function clientConfig(tenant, client) {
  if (typeof tenant !== 'string' || typeof client !== 'string' ||
      !UUID.test(tenant.trim()) || !UUID.test(client.trim())) {
    throw error('INVALID_CLIENT', '目录（租户）ID 和应用程序（客户端）ID 都须为有效的 UUID。');
  }
  return {tenant: tenant.trim().toLowerCase(), client: client.trim().toLowerCase()};
}

function identityUrl(config, path) {
  const {tenant} = clientConfig(config.tenant, config.client);
  return new URL('https://login.microsoftonline.com/' + tenant + '/oauth2/v2.0/' + path);
}

function authorizationUrl(config, {redirect, state, challenge}) {
  const url = identityUrl(config, 'authorize');
  url.search = new URLSearchParams({
    client_id: config.client, response_type: 'code', response_mode: 'query',
    scope: SCOPE, redirect_uri: redirect, state, code_challenge: challenge,
    code_challenge_method: 'S256', prompt: 'select_account',
  }).toString();
  return url;
}

async function fetchJson(url, options, request) {
  let response;
  try {
    response = await request(url, {
      ...options, redirect: 'error', signal: AbortSignal.timeout(15_000),
    });
  } catch {
    throw error('NETWORK_ERROR', 'Microsoft 请求未完成，请检查网络后重试。');
  }
  let size = 0;
  const chunks = [];
  for await (const chunk of response.body ?? []) {
    size += chunk.byteLength;
    if (size > 2 * 1024 * 1024) throw error('RESPONSE_LIMIT', 'Microsoft 返回内容过大，请缩小日程查询范围。');
    chunks.push(Buffer.from(chunk));
  }
  let data;
  try {
    data = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    if (response.ok) throw error('INVALID_RESPONSE', 'Microsoft 返回了无法读取的响应。');
  }
  return {status: response.status, ok: response.ok, data};
}

async function exchange(config, grant, request = fetch) {
  const {status, ok, data} = await fetchJson(identityUrl(config, 'token'), {
    method: 'POST',
    headers: {'Content-Type': 'application/x-www-form-urlencoded', Accept: 'application/json'},
    body: new URLSearchParams({client_id: config.client, scope: SCOPE, ...grant}),
  }, request);
  if (!ok) {
    if (['interaction_required', 'invalid_grant', 'consent_required'].includes(data?.error)) {
      throw error('AUTH_REQUIRED', 'Microsoft 授权已失效或需要重新确认，请从卡片连接。');
    }
    if (data?.error === 'invalid_client') {
      throw error('INVALID_CLIENT', 'Microsoft 拒绝了应用配置，请核对租户、客户端和桌面回调。');
    }
    if (status === 429) throw error('RATE_LIMIT', 'Microsoft 请求过于频繁，请稍后重试。');
    throw error('AUTH_FAILED', 'Microsoft 授权失败，请核对应用注册、租户策略和授权状态。');
  }
  const scopes = typeof data?.scope === 'string' ? data.scope.toLowerCase().split(/\s+/u) : [];
  if (!scopes.some(scope => scope === PERMISSION.toLowerCase() || scope === GRAPH + '/' + PERMISSION.toLowerCase())) {
    throw error('ACCESS_DENIED', 'Microsoft 没有授予 Outlook 日历基本读取权限。');
  }
  if (typeof data.access_token !== 'string' || !data.access_token ||
      !Number.isFinite(data.expires_in) || data.expires_in <= 0) {
    throw error('INVALID_RESPONSE', 'Microsoft 没有返回可用的访问令牌。');
  }
  const refreshToken = data.refresh_token || grant.refresh_token;
  if (typeof refreshToken !== 'string' || !refreshToken) {
    throw error('AUTH_REQUIRED', 'Microsoft 没有返回续期授权，请从卡片重新连接。');
  }
  return {
    access_token: data.access_token,
    refresh_token: refreshToken,
    expires_at: Date.now() + data.expires_in * 1000,
  };
}

function timestamp(value) {
  if (typeof value !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/u.test(value) ||
      value.slice(11, 13) === '24' || !Number.isFinite(Date.parse(value))) {
    throw error('BAD_ARGUMENTS', '时间须为带时区的 ISO 8601 时间。');
  }
  const day = value.slice(0, 10);
  const midnight = new Date(day);
  if (!Number.isFinite(+midnight) || midnight.toISOString().slice(0, 10) !== day) {
    throw error('BAD_ARGUMENTS', '日程日期无效。');
  }
  return new Date(value).toISOString();
}

function safeCursor(value, start, end) {
  if (typeof value !== 'string' || value.length > 8192) throw error('BAD_CURSOR', '请使用查询返回的下一页游标。');
  let url;
  try {
    url = new URL(value);
  } catch {
    throw error('BAD_CURSOR', '请使用查询返回的下一页游标。');
  }
  const params = url.searchParams;
  const allowed = new Set(['startDateTime', 'endDateTime', '$select', '$top', '$skip', '$skiptoken']);
  if (url.origin !== GRAPH || url.pathname.toLowerCase() !== VIEW.toLowerCase() ||
      url.username || url.password || url.hash || params.size !== new Set(params.keys()).size ||
      [...params.keys()].some(name => !allowed.has(name)) ||
      Date.parse(params.get('startDateTime')) !== Date.parse(start) ||
      Date.parse(params.get('endDateTime')) !== Date.parse(end) ||
      params.get('$select') !== FIELDS) {
    throw error('BAD_CURSOR', '下一页游标须来自相同时间范围的 Outlook 主日历查询。');
  }
  return url;
}

function listRequest(args) {
  if (!args || typeof args !== 'object' || Array.isArray(args) ||
      Object.keys(args).some(key => !['from', 'to', 'query', 'limit', 'cursor'].includes(key))) {
    throw error('BAD_ARGUMENTS', '日程查询参数无效。');
  }
  const start = timestamp(args.from);
  const end = timestamp(args.to);
  const interval = Date.parse(end) - Date.parse(start);
  if (interval <= 0 || interval > 90 * 86_400_000) {
    throw error('BAD_ARGUMENTS', '结束时间须晚于开始时间，查询范围最多 90 天。');
  }
  const limit = args.limit ?? 25;
  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
    throw error('BAD_ARGUMENTS', '每页数量须为 1 至 100。');
  }
  if (args.query !== undefined && (typeof args.query !== 'string' || !args.query.trim() || args.query.length > 240)) {
    throw error('BAD_ARGUMENTS', '标题筛选须为 1 至 240 个字符。');
  }
  const url = args.cursor === undefined ? new URL(VIEW, GRAPH) : safeCursor(args.cursor, start, end);
  if (args.cursor === undefined) {
    url.search = new URLSearchParams({startDateTime: start, endDateTime: end, '$select': FIELDS, '$top': String(limit)}).toString();
  }
  return {url, start, end, query: args.query?.trim()};
}

function detailRequest(args) {
  const id = args?.event_id;
  if (!args || Array.isArray(args) || Object.keys(args).length !== 1 ||
      typeof id !== 'string' || !/^[A-Za-z0-9+/_=-]{1,1024}$/u.test(id)) {
    throw error('BAD_ARGUMENTS', '请提供查询返回的 Outlook 日程 ID。');
  }
  const url = new URL(EVENT + encodeURIComponent(id), GRAPH);
  url.searchParams.set('$select', FIELDS);
  return url;
}

async function graph(url, accessToken, request = fetch) {
  const {status, ok, data} = await fetchJson(url, {
    method: 'GET',
    headers: {Authorization: 'Bearer ' + accessToken, Accept: 'application/json', Prefer: 'outlook.timezone="UTC"'},
  }, request);
  if (!ok) {
    if (status === 401) throw error('AUTH_REQUIRED', 'Outlook 授权已失效，请从卡片重新连接。');
    if (data?.error?.code === 'MailboxNotEnabledForRESTAPI' || status === 404 && url.pathname === VIEW) {
      throw error('MAILBOX_UNAVAILABLE', '此账号的 Outlook 邮箱未能通过 Graph 读取，请核对 Exchange Online 邮箱。');
    }
    if (status === 403) throw error('ACCESS_DENIED', 'Microsoft 拒绝读取工作日历，请核对租户同意和日历权限。');
    if (status === 404) throw error('NOT_FOUND', '当前主日历找不到该日程。');
    if (status === 429) throw error('RATE_LIMIT', 'Microsoft Graph 请求过于频繁，请稍后重试。');
    throw error('SERVICE_ERROR', 'Outlook 日历请求未成功，请核对参数或稍后重试。');
  }
  return data;
}

function record(item) {
  if (typeof item?.id !== 'string' || typeof item?.start?.dateTime !== 'string' || typeof item?.end?.dateTime !== 'string') {
    throw error('INVALID_RESPONSE', 'Microsoft 返回的日程缺少必要字段。');
  }
  return {
    event_id: item.id,
    title: item.subject ?? null,
    from: {value: item.start.dateTime, time_zone: item.start.timeZone},
    to: {value: item.end.dateTime, time_zone: item.end.timeZone},
    location: item.location?.displayName ?? null,
    is_all_day: item.isAllDay ?? false,
    is_cancelled: item.isCancelled ?? false,
    link: item.webLink ?? null,
  };
}

const normalize = value => typeof value === 'string' ? value.normalize('NFKC').toLowerCase() : '';

async function list(req, accessToken, request) {
  const data = await graph(req.url, accessToken, request);
  if (!Array.isArray(data?.value)) throw error('INVALID_RESPONSE', 'Microsoft 没有返回可用的主日历列表。');
  const needle = normalize(req.query);
  const events = data.value.filter(item => normalize(item?.subject).includes(needle)).map(record);
  const next = data['@odata.nextLink'];
  const cursor = next ? safeCursor(next, req.start, req.end).href : null;
  return {events, scanned: data.value.length, next_cursor: cursor === req.url.href ? null : cursor};
}

async function probe(accessToken, request) {
  const now = Date.now();
  const args = {from: new Date(now).toISOString(), to: new Date(now + 60_000).toISOString(), limit: 1};
  const data = await graph(listRequest(args).url, accessToken, request);
  if (!Array.isArray(data?.value)) throw error('INVALID_RESPONSE', 'Microsoft 没有返回可用的主日历。');
}

module.exports = {clientConfig, authorizationUrl, exchange, listRequest, detailRequest, graph, record, list, probe};
