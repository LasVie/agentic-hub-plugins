'use strict';
const crypto = require('node:crypto');
const SCOPE = 'https://www.googleapis.com/auth/calendar.events.owned';
const FIELDS = 'id,summary,start,end,status,description,htmlLink,visibility,transparency,reminders,attendees';
function fail(message) { throw Object.assign(new Error(message), {code: 'BAD_ARGUMENTS'}); }
function text(v, label, limit, empty = false) {
  if (typeof v !== 'string' || (!empty && !v.trim()) || v.length > limit || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(v)) fail(label + '不符合要求。');
  return v;
}
function timestamp(v) {
  if (typeof v !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(v) || !Number.isFinite(Date.parse(v))) fail('起止时间须为带时区的有效 RFC 3339 时间。');
  // Date.parse normalizes invalid dates such as February 30; reject those.
  const d = new Date(v.slice(0, 10) + 'T00:00:00Z');
  if (d.toISOString().slice(0, 10) !== v.slice(0, 10)) fail('日程日期不存在。');
  return v;
}
function request(mode, value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail('参数须为 JSON 对象。');
  const allowed = {list: ['from','to','query','limit','page_token'], read: ['event_id'], create: ['from','to','summary','description']}[mode];
  if (!allowed || Object.keys(value).some(k => !allowed.includes(k))) fail('包含不支持的操作或字段；只操作主日历的个人日程。');
  if (mode === 'read') {
    const id = text(value.event_id, '日程标识', 1024);
    if (!/^[a-zA-Z0-9_@.-]+$/.test(id)) fail('日程标识不符合要求。');
    return {method: 'get', params: {calendarId: 'primary', eventId: id, fields: FIELDS}};
  }
  const from = timestamp(value.from), to = timestamp(value.to);
  if (Date.parse(from) >= Date.parse(to)) fail('结束时间须晚于开始时间。');
  if (mode === 'list') {
    const limit = value.limit ?? 30;
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) fail('结果数须为 1 至 100。');
    return {method: 'list', params: {calendarId: 'primary', timeMin: from, timeMax: to,
      singleEvents: true, orderBy: 'startTime', showDeleted: false, maxResults: limit,
      fields: `items(${FIELDS}),nextPageToken,timeZone`,
      ...(value.query !== undefined ? {q: text(value.query, '关键词', 300)} : {}),
      ...(value.page_token !== undefined ? {pageToken: text(value.page_token, '分页标识', 2048)} : {})}};
  }
  const body = {id: crypto.randomBytes(16).toString('hex'), summary: text(value.summary, '标题', 300),
    start: {dateTime: from}, end: {dateTime: to}, visibility: 'private', transparency: 'transparent',
    reminders: {useDefault: false},
    ...(value.description !== undefined ? {description: text(value.description, '描述', 3500, true)} : {})};
  return {method: 'insert', params: {calendarId: 'primary', sendUpdates: 'none', fields: FIELDS}, body};
}
module.exports = {request, SCOPE, FIELDS};
