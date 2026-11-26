'use strict';
const test=require('node:test'), assert=require('node:assert/strict'), crypto=require('node:crypto');
const cli=require('../google-calendar/skills/google-calendar-guide/scripts/calendar-cli.cjs');
const {SCOPE}=require('../google-calendar/skills/google-calendar-guide/scripts/scope.cjs');
const span={from:'2026-11-24T20:00:00+08:00',to:'2026-11-24T20:15:00+08:00'};
test('主日历查询保留分页，不能改变日历和投射字段',()=>{
  const r=cli.request('list',{...span,query:'中文关键词',limit:4,page_token:'下一页'});
  assert.equal(r.params.calendarId,'primary');assert.equal(r.params.pageToken,'下一页');assert.equal(r.params.q,'中文关键词');
  assert.throws(()=>cli.request('list',{...span,calendarId:'other'}));
});
test('创建排除邀请、重复与未知字段；固定个人私密无提醒',()=>{
  const r=cli.request('create',{...span,summary:'中文测试',description:'正文\n第二行'});
  assert.equal(r.method,'insert');assert.match(r.body.id,/^[0-9a-f]{32}$/);
  assert.equal(r.body.visibility,'private');assert.equal(r.body.transparency,'transparent');
  assert.deepEqual(r.body.reminders,{useDefault:false});assert.equal(r.params.sendUpdates,'none');
  for(const field of ['attendees','recurrence','reminders','calendarId','sendUpdates'])assert.throws(()=>cli.request('create',{...span,summary:'测试',[field]:[]}));
});
test('拒绝不存在的日期、倒置时间与缺少时区',()=>{
  for(const from of ['2026-02-30T20:00:00+08:00','2026-11-24T20:00:00','2026-11-25T00:00:00Z'])assert.throws(()=>cli.request('list',{...span,from}));
});
test('按 ID 独立读取，不允许路径注入或业务命令逃逸',()=>{
  assert.equal(cli.request('read',{event_id:'fixture123'}).params.eventId,'fixture123');
  for(const id of ['../other','x?token=secret','x/y'])assert.throws(()=>cli.request('read',{event_id:id}));
  assert.throws(()=>cli.request('delete',{event_id:'fixture'}));
});
test('官方 OAuth 库生成唯一日历权限与 PKCE/state，不追加身份权限',()=>{
  const {OAuth2Client}=require(process.env.CALENDAR_REVIEW_AUTH_LIBRARY);
  const c=new OAuth2Client({clientId:'fixture.apps.googleusercontent.com',clientSecret:'fictional',redirectUri:'http://127.0.0.1:12345/callback'});
  const u=new URL(cli.authorizeOptions(c,c.redirectUri,'random-state','challenge'));
  assert.equal(u.searchParams.get('scope'),SCOPE);assert.equal(u.searchParams.get('state'),'random-state');
  assert.equal(u.searchParams.get('include_granted_scopes'),'false');assert.equal(u.searchParams.get('code_challenge_method'),'S256');
  assert.equal(u.searchParams.get('redirect_uri'),'http://127.0.0.1:12345/callback');
});
test('短时客户端超时清理子进程并屏蔽原始凭据错误',async()=>{
  await assert.rejects(cli.bounded(process.execPath,['-e','setInterval(()=>{},1000)'],{timeout:80}),{code:'TIMEOUT'});
  const result=cli.safeFailure(new Error('refresh_token=fictional-private-value'));
  assert.equal(result.code,'CLIENT_FAILED');assert.ok(!JSON.stringify(result).includes('fictional-private-value'));
});
test('写入结果未知时返回预生成标识及先回读提示',()=>{
  const result=cli.safeFailure(Object.assign(new Error('timeout'),{code:'TIMEOUT',writeOutcome:'unknown',event_id:'fixture123'}));
  assert.equal(result.writeOutcome,'unknown');assert.equal(result.event_id,'fixture123');assert.match(result.recovery,/禁止直接重试/);
});
