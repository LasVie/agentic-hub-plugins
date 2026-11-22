'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {validate,perform}=require('./standard-mcp.cjs');
test('未知操作、更新参数及路径注入在请求前拒绝',()=>{
  assert.throws(()=>validate('delete_task',{item:'123'}));
  assert.throws(()=>validate('asana_create_task',{container:'123',title:'测试',assignee:'anyone'}));
  assert.throws(()=>validate('asana_read_task',{item:'../users/me'}));
  assert.throws(()=>validate('asana_list_tasks',{container:'123',limit:101}));
  assert.throws(()=>validate('asana_create_task',{container:'123',title:' '}));
});
test('中文创建只发送项目与标题，不发更新或分配请求',async()=>{
  let call;
  const result=await perform('asana_create_task',{container:'123',title:'中文测试'},'synthetic-test-token',undefined,async(url,options)=>{
    call={url:String(url),options};
    return new Response(JSON.stringify({data:{gid:'456',name:'中文测试'}}),{status:201});
  });
  assert.equal(call.url,'https://app.asana.com/api/1.0/tasks');
  assert.equal(call.options.method,'POST');
  assert.equal(call.options.redirect,'error');
  assert.deepEqual(JSON.parse(call.options.body),{data:{projects:['123'],name:'中文测试'}});
  assert.equal(result.data.gid,'456');
});
test('缺凭据不发请求；失效授权与权限错误用中文且不回显敏感响应',async()=>{
  let calls=0;
  await assert.rejects(()=>perform('asana_status',{},'',undefined,async()=>{calls++;}),/个人访问令牌/);
  assert.equal(calls,0);
  for(const code of [401,403,429,503]){
    await assert.rejects(()=>perform('asana_status',{},'synthetic-test-token',undefined,
      async()=>new Response('DO_NOT_ECHO_PRIVATE_RESPONSE',{status:code})),error=>{
      assert.doesNotMatch(error.message,/PRIVATE|synthetic/);assert.match(error.message,/[\u4e00-\u9fff]/);return true;
    });
  }
});
test('写入网络异常只请求一次，明确要求回读',async()=>{
  let calls=0;
  await assert.rejects(()=>perform('asana_create_task',{container:'123',title:'测试'},'synthetic-test-token',undefined,
    async()=>{calls++;throw Error('private network detail');}),/先按唯一标题回读/);
  assert.equal(calls,1);
});
