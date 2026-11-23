'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const scope=require('../confluence-cloud/skills/confluence-cloud-guide/scripts/scope.cjs');
const cli=require('../confluence-cloud/skills/confluence-cloud-guide/scripts/confluence-cli.cjs');
const {createLoginBridge}=require('../confluence-cloud/skills/confluence-cloud-guide/scripts/login-bridge.cjs');
test('官方授权只含 Confluence、基本账号和离线刷新',()=>{
 const u=new URL('https://auth.atlassian.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));assert.equal(scope.assertAuthorizationUrl(u),true);
 for(const extra of ['read:jira:agent-interface','write:jira:agent-interface','search:rovo:agent-interface']){const b=new URL(u);b.searchParams.set('scope',scope.SCOPES.concat(extra).join(' '));assert.throws(()=>scope.assertAuthorizationUrl(b),{code:'SCOPE_EXPANDED'});}
 const b=new URL(u);b.hostname='example.com';assert.throws(()=>scope.assertAuthorizationUrl(b));
});
test('拒绝已有内容修改、删除、评论、权限和任意执行',()=>{
 for(const t of ['updateConfluenceContent','archiveConfluenceContent','createConfluenceComment','addConfluenceContentPermissions','enableConfluencePublicLink','createJiraIssue','executeWrite','discover'])assert.ok(scope.argumentError(t,{}));
});
test('新建限明确空间、父页、标题和 Markdown 普通页面',()=>{
 const good={cloudId:'qa-cloud',parent:{spaceId:'123',parentContentId:'589826'},title:'中文唯一测试页',body:{format:'markdown',value:'完整测试正文'}};assert.equal(scope.argumentError('createConfluenceContent',good),null);
 for(const v of [{...good,contentType:'blogpost'},{...good,body:{format:'html',value:'<p>正文</p>'}},{...good,permissions:{}},{...good,parent:{spaceId:'123',parentContentId:''}},{...good,parent:{spaceId:'SD',parentContentId:'589826'}},{...good,parent:{...good.parent,parentContentUrl:'https://example.com'}},{...good,body:{...good.body,url:'https://example.com'}},{...good,draft:true}])assert.ok(scope.argumentError('createConfluenceContent',v));
 assert.deepEqual(scope.prepareArguments('createConfluenceContent',good),{...good,contentType:'page'});
});
test('搜索限定普通页面，分页和标识有边界',()=>{
 assert.equal(scope.prepareArguments('searchConfluence',{cloudId:'qa',cql:'space = SD'}).cql,'type = page AND (space = SD)');
 assert.ok(scope.argumentError('searchConfluence',{cloudId:'qa',cql:'space = SD',limit:101}));
 assert.ok(scope.argumentError('getConfluenceContent',{cloudId:'qa',content_id:'https://example.com'}));
 assert.ok(scope.argumentError('getConfluenceContent',{cloudId:'qa',content_id:'123',detail:'summary'}));
 assert.deepEqual(scope.prepareArguments('getConfluenceContent',{cloudId:'qa',content_id:'123'}),{cloudId:'qa',content_id:'123',detail:'full',content_format:'markdown'});
});
test('CQL 页面限制不破坏顶层排序，也不误读标题中的 order by',()=>{
 assert.equal(scope.pageCql('space = SD ORDER BY created DESC'),'type = page AND (space = SD) ORDER BY created DESC');
 assert.equal(scope.pageCql('title = "order by 中文"'),'type = page AND (title = "order by 中文")');
 assert.equal(scope.pageCql('(space = SD OR space = QA) ORDER BY title'),'type = page AND ((space = SD OR space = QA)) ORDER BY title');
 assert.throws(()=>scope.pageCql('space = SD)'),{code:'SCOPE_REJECTED'});
});
test('实际 v2 站点封装只接受 Confluence 产品',()=>{
 assert.deepEqual(scope.resourcesFrom({data:{resources:[{cloudId:'c',url:'https://openjiuwenofficial.atlassian.net',products:[{id:'confluence'}]},{cloudId:'j',url:'https://jiraonly.atlassian.net',products:[{id:'jira'}]}]}}),[{id:'c',url:'https://openjiuwenofficial.atlassian.net',name:''}]);
});
test('工具过滤拒绝范围外新必填字段',()=>{
 const inputSchema={type:'object',properties:{cloudId:{type:'string'},parent:{type:'object'},contentType:{type:'string'},title:{type:'string'},body:{type:'object'},permissions:{type:'object'}},required:['cloudId','parent','contentType','title']};
 const t=scope.visibleTool({name:'createConfluenceContent',inputSchema});assert.ok(!t.inputSchema.properties.permissions);assert.equal(t.inputSchema.additionalProperties,false);
 assert.deepEqual(t.inputSchema.properties.parent.required,['spaceId','parentContentId']);assert.equal(t.inputSchema.properties.body.properties.format.const,'markdown');assert.ok(t.inputSchema.required.includes('body'));
 assert.throws(()=>scope.visibleTool({name:'createConfluenceContent',inputSchema:{...inputSchema,required:['permissions']}}),{code:'SCOPE_REJECTED'});
});
test('中文和特殊字符仅通过 JSON 文件传递',()=>{
 const d=fs.mkdtempSync(path.join(os.tmpdir(),'confluence-node-'));try{const f=path.join(d,'args.json'),a={cloudId:'qa',parent:{spaceId:'123',parentContentId:'589826'},title:'中文 $ 字符',body:{format:'markdown',value:'正文保持字面内容'}};fs.writeFileSync(f,JSON.stringify(a));assert.deepEqual(cli.inputFile(['call','createConfluenceContent','--input-file',f]),{tool:'createConfluenceContent',arguments:a});}finally{fs.rmSync(d,{recursive:true,force:true});}
});
test('读取和新建前核对普通页面类型、目标 ID 与父页所属空间',()=>{
 const page={id:'589826',type:'page',spaceId:'229380'};
 assert.deepEqual(scope.assertPage({data:page},{id:'589826',spaceId:'229380'}),page);
 for(const value of [{...page,type:'blogpost'},{...page,spaceId:'999'},{...page,id:'123'},{}])assert.throws(()=>scope.assertPage({data:value},{id:'589826',spaceId:'229380'}),{code:'SCOPE_REJECTED'});
});
test('有限子进程超时结束，写入结果不明禁止自动重试',async()=>{
 await assert.rejects(cli.runBounded(process.execPath,['-e','setInterval(()=>{},1000)'],{timeoutMs:60}),{code:'TIMEOUT'});
 const e=cli.safeFailure(Object.assign(new Error('private-credential'),{writeAttempted:true}));assert.equal(e.writeOutcome,'unknown');assert.ok(!JSON.stringify(e).includes('private-credential'));assert.match(e.recovery,/禁止直接重试/);
});
test('本机引导先就绪，只转交官方精确范围 URL 并能关闭',async()=>{
 const b=await createLoginBridge();try{assert.equal((await fetch(b.url)).status,200);const u=new URL('https://auth.atlassian.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));b.setAuthorizationUrl(u);assert.equal((await(await fetch(b.url+'/state')).json()).authorization_url,u.toString());assert.throws(()=>b.setAuthorizationUrl('https://example.com'));}finally{b.close();}await assert.rejects(fetch(b.url));
});
test('不同配置目录回调端口隔离且稳定',()=>{
 assert.equal(cli.callbackPort('/tmp/confluence-a'),cli.callbackPort('/tmp/confluence-a'));assert.notEqual(cli.callbackPort('/tmp/confluence-a'),cli.callbackPort('/tmp/confluence-b'));
});
