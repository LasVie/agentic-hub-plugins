'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const scope=require('../miro/skills/miro-guide/scripts/scope.cjs'),ops=require('../miro/skills/miro-guide/scripts/canvas-ops.cjs');
const cli=require('../miro/skills/miro-guide/scripts/miro-cli.cjs');
const {createLoginBridge}=require('../miro/skills/miro-guide/scripts/login-bridge.cjs');
const fixture=require('./fixtures/miro-live-readonly-20261123.json');
const url='https://miro.com/app/board/uXjVENX_jBk=/',marker='WSQA-MIRO-NODE-UNIT';
const note={boardUrl:url,text:'中文便签 '+marker,marker,x:1200,y:100};
const wrapped=d=>({structuredContent:d,isError:false});
const empty={success:true,svg:'<svg xmlns="http://www.w3.org/2000/svg"></svg>',item_count:0,skipped_count:0};
function directory(){return fs.mkdtempSync(path.join(os.tmpdir(),'miro-unit-'));}
test('OAuth 仅接受官方精确白板读写范围',()=>{
 const u=new URL('https://mcp.miro.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));assert.equal(scope.assertAuthorizationUrl(u),true);
 for(const scopes of ['boards:read boards:write openid','boards:read boards:write boards:write','boards:read']){const b=new URL(u);b.searchParams.set('scope',scopes);assert.throws(()=>scope.assertAuthorizationUrl(b),{code:'SCOPE_EXPANDED'});}
 const b=new URL(u);b.hostname='example.com';assert.throws(()=>scope.assertAuthorizationUrl(b));
});
test('不暴露原始 SVG、更新、删除、评论和权限工具',()=>{
 for(const name of ['canvas_create_from_svg','canvas_update_from_svg','section_delete','comment_create','board_role_update','__proto__'])assert.ok(scope.argumentError(name,{}));
 assert.equal(scope.argumentError('createStickyNote',note),null);
 for(const value of [{...note,svg:'<svg/>'},{...note,text:'没有唯一标记'},{...note,x:Infinity},{...note,y:1.5},{...note,widgetIds:['123']}])assert.ok(scope.argumentError('createStickyNote',value));
});
test('Miro URL 拒绝附加参数、凭据和其他站点',()=>{
 assert.equal(scope.boardUrl(url.slice(0,-1)),url);
 for(const bad of ['http://miro.com/app/board/abc/','https://miro.com.evil.test/app/board/abc/','https://user@miro.com/app/board/abc/',url+'?moveToWidget=123','https://miro.com/app/board/../foo/'])assert.throws(()=>scope.boardUrl(bad));
});
test('读取必须选择 ID 或矩形并限制边界',()=>{
 const good={boardUrl:url,widgetIds:['3458764690692182654']};assert.equal(scope.argumentError('readCanvas',good),null);
 for(const bad of [{boardUrl:url},{...good,area:{x:0,y:0,width:1,height:1}},{boardUrl:url,widgetIds:['1','1']},{boardUrl:url,area:{x:0,y:0,width:-1,height:100}}])assert.ok(scope.argumentError('readCanvas',bad));
});
test('真实 schema 能通过，新增未知必填参数先拒绝',()=>{
 const tools=Object.entries(fixture.schemas).map(([name,inputSchema])=>({name,inputSchema}));scope.assertSchemas(tools);
 const changed=structuredClone(tools);changed[0].inputSchema.required=['new_permission'];assert.throws(()=>scope.assertSchemas(changed),{code:'SCOPE_REJECTED'});
});
test('固定模板只生成一张便签，中文和注入文本保持纯文本',()=>{
 const text='中文 😀 "\' & <b>纯文本</b>\n<rect data-type="frame" /> '+marker;
 const svg=ops.svgForSticky({...note,text});assert.equal((svg.match(/<rect\b/g)||[]).length,1);assert.ok(!svg.includes('data-miro-id='));assert.ok(!svg.includes('<b>'));
 const echoed=svg.replace('id="ws_note"','id="m123" data-miro-id="123"');assert.equal(ops.stickyNotes(echoed)[0].text,text);
});
test('解析真实中文便签，不把截断 SVG 视为完整读取',()=>{
 const d=ops.readData(wrapped(fixture.test_area));assert.equal(d.sticky_notes.length,2);assert.equal(d.sticky_notes[1].text,'WorkSwarm Miro 聊天验收 WSQA-261117-M1');
 assert.throws(()=>ops.readData(wrapped({...empty,svg:'<svg>'})),{code:'READ_UNVERIFIED'});
});
test('目标 ID 未返回时不报告回读成功',async()=>{
 await assert.rejects(ops.executeOperation('readCanvas',{boardUrl:url,widgetIds:['123']},{call:async()=>wrapped({...empty,skipped_count:1})}),{code:'READ_UNVERIFIED'});
});
test('区域非空或读取有遗漏时不触发写入',async()=>{
 const root=directory();try{for(const data of [fixture.test_area,{...empty,skipped_count:1}]){let calls=0,write=false;await assert.rejects(ops.executeOperation('createStickyNote',note,{receiptRoot:root,call:async name=>{calls++;assert.equal(name,'canvas_read_as_svg');return wrapped(data);},beginWrite:()=>{write=true;}}),{code:'SCOPE_REJECTED'});assert.equal(calls,1);assert.equal(write,false);}}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('单次创建后相同标记只回读，不重复提交',async()=>{
 const root=directory();let creates=0,write=false;const echo=ops.svgForSticky(note).replace('id="ws_note"','id="m123" data-miro-id="123"');
 const call=async(name,args)=>{if(name==='canvas_read_as_svg')return wrapped(args.widget_ids?{...empty,svg:echo,item_count:1}:empty);if(name==='canvas_get_canvas_composer_skill')return wrapped({success:true,skill:'data-type="sticky" data-content data-color'});if(name==='canvas_create_from_svg'){creates++;assert.equal((args.svg.match(/<rect\b/g)||[]).length,1);return wrapped({success:true,result_svg:echo});}throw Error('Unplanned tool');};
 try{const a=await ops.executeOperation('createStickyNote',note,{receiptRoot:root,call,beginWrite:()=>{write=true;}});assert.equal(a.id,'123');assert.equal(write,true);const b=await ops.executeOperation('createStickyNote',note,{receiptRoot:root,call,beginWrite:()=>{throw Error('Duplicate write');}});assert.equal(b.already_submitted,true);assert.equal(creates,1);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('写入中断保留待核对记录，禁止再次发送',async()=>{
 const root=directory();let creates=0;const call=async name=>{if(name==='canvas_read_as_svg')return wrapped(empty);if(name==='canvas_get_canvas_composer_skill')return wrapped({success:true,skill:'data-type="sticky" data-content data-color'});creates++;throw Error('Network ended');};
 try{await assert.rejects(ops.executeOperation('createStickyNote',note,{receiptRoot:root,call,beginWrite:()=>{}}));await assert.rejects(ops.executeOperation('createStickyNote',note,{receiptRoot:root,call,beginWrite:()=>{}}),{code:'WRITE_UNCERTAIN'});assert.equal(creates,1);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('区域已含唯一标记时返回已有便签',async()=>{
 const root=directory(),echo=ops.svgForSticky(note).replace('id="ws_note"','id="m123" data-miro-id="123"');try{let count=0;const r=await ops.executeOperation('createStickyNote',note,{receiptRoot:root,call:async name=>{assert.equal(name,'canvas_read_as_svg');count++;return wrapped({...empty,svg:echo,item_count:1});},beginWrite:()=>{throw Error('No write allowed');}});assert.equal(r.duplicate,true);assert.equal(r.id,'123');assert.equal(count,1);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('超时终止有限子进程，未知写入提示不泄露异常内容',async()=>{
 await assert.rejects(cli.runBounded(process.execPath,['-e','setInterval(()=>{},1000)'],{timeoutMs:60}),{code:'TIMEOUT'});
 const r=cli.safeFailure(Object.assign(new Error('private-credential'),{writeAttempted:true}));assert.equal(r.writeOutcome,'unknown');assert.ok(!JSON.stringify(r).includes('private-credential'));assert.match(r.recovery,/禁止直接重试/);
});
test('本机引导拒绝非官方地址并能关闭',async()=>{
 const b=await createLoginBridge();try{assert.equal((await fetch(b.url)).status,200);const u=new URL('https://mcp.miro.com/authorize');u.searchParams.set('scope',scope.SCOPES.join(' '));b.setAuthorizationUrl(u);assert.equal((await(await fetch(b.url+'/state')).json()).authorization_url,u.toString());assert.throws(()=>b.setAuthorizationUrl('https://example.com'));}finally{b.close();}await assert.rejects(fetch(b.url));
});
