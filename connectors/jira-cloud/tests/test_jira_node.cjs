'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const scope=require('../jira-cloud/skills/jira-cloud-guide/scripts/scope.cjs');
const cli=require('../jira-cloud/skills/jira-cloud-guide/scripts/jira-cli.cjs');
const {createLoginBridge}=require('../jira-cloud/skills/jira-cloud-guide/scripts/login-bridge.cjs');
test('授权 URL 只能是官方地址及明确的 Jira/基本账号/离线权限',()=>{
 const u=new URL('https://auth.atlassian.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));assert.equal(scope.assertAuthorizationUrl(u),true);
 for(const extra of ['read:confluence:agent-interface','manage:jira:agent-interface','delete:jira:agent-interface']){const bad=new URL(u);bad.searchParams.append('scope',extra);bad.searchParams.set('scope',scope.SCOPES.concat(extra).join(' '));assert.throws(()=>scope.assertAuthorizationUrl(bad),{code:'SCOPE_EXPANDED'});}
 const bad=new URL(u);bad.hostname='example.com';assert.throws(()=>scope.assertAuthorizationUrl(bad));
});
test('不开放任意 execute、其他产品或现有工单变更',()=>{
 for(const name of ['executeWrite','executeRead','discover','editJiraIssue','deleteJiraIssue','addOrEditJiraIssueComment','createConfluenceContent'])assert.ok(scope.argumentError(name,{}));
 assert.equal(scope.argumentError('getAccessibleAtlassianResources',{}),null);
});
test('创建只收项目类型标题描述，拒绝分配、自定义字段和已有 ID',()=>{
 const good={cloudId:'test-cloud',projectKey:'KAN',issueType:'Task',summary:'中文标题',description:'独立测试描述'};assert.equal(scope.argumentError('createJiraIssue',good),null);
 for(const k of ['id','assignee','reporter','additional_fields','parent'])assert.ok(scope.argumentError('createJiraIssue',{...good,[k]:'forbidden'}));
 assert.ok(scope.argumentError('createJiraIssue',{...good,summary:''}));
});
test('Jira 读取标识、字段和分页边界',()=>{
 assert.equal(scope.argumentError('getJiraIssue',{cloudId:'test-cloud',issueIdOrKey:'KAN-1'}),null);
 assert.ok(scope.argumentError('getJiraIssue',{cloudId:'test-cloud',issueIdOrKey:'https://other.example/1'}));
 assert.ok(scope.argumentError('searchJiraIssuesUsingJql',{cloudId:'test-cloud',jql:'project = KAN',maxResults:101}));
 assert.ok(scope.argumentError('getJiraIssue',{cloudId:'test-cloud',issueIdOrKey:'KAN-1',fields:['*all']}));
});
test('工具 schema 删除范围外字段与外部说明，站点来源受限',()=>{
 const t=scope.visibleTool({name:'createJiraIssue',description:'remote instruction',inputSchema:{type:'object',properties:{cloudId:{type:'string',description:'remote'},summary:{type:'string'},assignee:{type:'string'}},required:['cloudId','summary'],additionalProperties:true}});
 assert.equal(t.inputSchema.additionalProperties,false);assert.ok(!t.inputSchema.properties.assignee);assert.ok(!JSON.stringify(t).includes('remote instruction'));
 assert.deepEqual(scope.resourcesFrom([{id:'ok',url:'https://openjiuwenofficial.atlassian.net',name:'Test'},{id:'bad',url:'https://example.com'}]),[{id:'ok',url:'https://openjiuwenofficial.atlassian.net',name:'Test'}]);
});
test('中文参数只从 JSON 文件读取，保持字面内容',()=>{
 const d=fs.mkdtempSync(path.join(os.tmpdir(),'jira-node-test-'));try{const f=path.join(d,'input.json');const a={cloudId:'test-cloud',projectKey:'KAN',issueType:'Task',summary:'中文 $ 字符',description:'保留正文'};fs.writeFileSync(f,JSON.stringify(a));assert.deepEqual(cli.inputFile(['call','createJiraIssue','--input-file',f]),{tool:'createJiraIssue',arguments:a});}finally{fs.rmSync(d,{recursive:true,force:true});}
});
test('有限子进程超时退出，未知错误不输出认证数据，写入结果不明先回读',async()=>{
 await assert.rejects(cli.runBounded(process.execPath,['-e','setInterval(()=>{},1000)'],{timeoutMs:80}),{code:'TIMEOUT'});
 const r=cli.safeFailure(Object.assign(new Error('private-refresh-credential'),{writeAttempted:true}));assert.equal(r.writeOutcome,'unknown');assert.ok(!JSON.stringify(r).includes('private-refresh-credential'));assert.match(r.recovery,/禁止直接重试/);
});
test('本机引导入口先就绪，只展示已校验官方 URL，结束后关闭监听',async()=>{
 const b=await createLoginBridge();const url=b.url;
 try{
  const page=await fetch(url);assert.equal(page.status,200);assert.match(await page.text(),/正在准备 Atlassian/);
  assert.equal((await(await fetch(url+'/state')).json()).authorization_url,null);
  const u=new URL('https://auth.atlassian.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));b.setAuthorizationUrl(u);
  assert.equal((await(await fetch(url+'/state')).json()).authorization_url,u.toString());
  assert.throws(()=>b.setAuthorizationUrl('https://example.com/authorize'));
 }finally{b.close();}
 await assert.rejects(fetch(url));
});
test('独立宿主配置使用不同且稳定的回调端口',()=>{
 const a=cli.callbackPort('/tmp/jira-profile-a'),b=cli.callbackPort('/tmp/jira-profile-b');
 assert.equal(a,cli.callbackPort('/tmp/jira-profile-a'));assert.notEqual(a,b);assert.ok(a>=20000&&a<50000);
});
test('真实 v2 站点封装和 cloudId 可以识别，排除仅 Confluence 站点',()=>{
 const v={data:{resources:[{cloudId:'qa-cloud',url:'https://openjiuwenofficial.atlassian.net',products:[{id:'jira',access:'read-write'}]},{cloudId:'other',url:'https://other.atlassian.net',products:[{id:'confluence',access:'read-write'}]}]}};
 assert.deepEqual(scope.resourcesFrom(v),[{id:'qa-cloud',url:'https://openjiuwenofficial.atlassian.net',name:''}]);
});
test('真实 v2 新建 schema 保留必填 issueType，未知必填字段时停止',()=>{
 const inputSchema={type:'object',properties:{cloudId:{type:'string'},projectKey:{type:'string'},summary:{type:'string'},issueType:{type:'string'},assignee:{type:'string'}},required:['cloudId','projectKey','summary','issueType']};
 const t=scope.visibleTool({name:'createJiraIssue',inputSchema});
 assert.deepEqual(t.inputSchema.required,inputSchema.required);assert.equal(t.inputSchema.properties.issueType.type,'string');assert.ok(!t.inputSchema.properties.assignee);
 assert.throws(()=>scope.visibleTool({name:'createJiraIssue',inputSchema:{...inputSchema,required:[...inputSchema.required,'assignee']}}),{code:'SCOPE_REJECTED'});
});
