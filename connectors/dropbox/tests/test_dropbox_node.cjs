'use strict';
const {test,after} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const net = require('node:net');
const scripts = path.join(__dirname,'../dropbox/skills/dropbox-guide/scripts');
const C = require(path.join(scripts,'common.cjs'));
const O = require(path.join(scripts,'operations.cjs'));
const A = require(path.join(scripts,'oauth-gate.cjs'));
const CLI = require(path.join(scripts,'dropbox-cli.cjs'));
const temp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'dropbox-node-test-')));
const previous = process.env.JIUWENSWARM_DATA_DIR;
process.env.JIUWENSWARM_DATA_DIR = temp;
after(()=>{if(previous===undefined)delete process.env.JIUWENSWARM_DATA_DIR;else process.env.JIUWENSWARM_DATA_DIR=previous;fs.rmSync(temp,{recursive:true,force:true});});
const code = expected => e=>e.code===expected;
const bytes = Buffer.from('独立中文文件核对。\n第二行 emoji 😀 & <标记>。\n','utf8');
const m = {'.tag':'file',id:'id:unit-fixture',name:'测试.txt',path_display:'/测试/测试.txt',path_lower:'/测试/测试.txt',size:bytes.length,rev:'abc0123',content_hash:O.contentHash(bytes),is_downloadable:true};
test('only four read operations and exact parameter fields',()=>{
  for(const op of ['upload','delete','share','dash_search','getUrl'])assert.throws(()=>O.validate(op,{}),code('SCOPE_REJECTED'));
  assert.throws(()=>O.validate('readText',{path:'/ok',url:'https://example.com'}),code('SCOPE_REJECTED'));
  for(const p of ['relative','/a/../b','/a\\b','id:bad@id','/a\n'])assert.throws(()=>O.validate('readText',{path:p}),code('BAD_ARGUMENTS'));
  assert.equal(O.validate('readText',{path:'id:unit-fixture'}).path,'id:unit-fixture');
});
test('filename search and folder pagination remain explicit',async()=>{
  const calls=[];const deps={bearer:async()=> 'unit-test',rpc:async(route,args)=>{calls.push({route,args});return {matches:[{metadata:{metadata:m}}],has_more:true,cursor:'next-page'};}};
  const r=await O.execute('searchFiles',{query:'测试.txt',path:'/测试',limit:3},deps);
  assert.equal(r.entries[0].id,m.id);assert.equal(r.has_more,true);assert.equal(r.search_index_may_be_incomplete,true);
  assert.deepEqual(calls[0],{route:'files/search_v2',args:{query:'测试.txt',options:{filename_only:true,max_results:3,path:'/测试'},match_field_options:{include_highlights:false}}});
  await O.execute('searchFiles',{cursor:r.cursor},deps);assert.deepEqual(calls[1].args,{cursor:'next-page'});
  assert.throws(()=>O.validate('searchFiles',{cursor:'next-page',path:'/other'}),code('BAD_ARGUMENTS'));
  assert.throws(()=>O.validate('listFolder',{limit:101}),code('BAD_ARGUMENTS'));
});
test('listing is non-recursive and preserves has_more',async()=>{
  let call;const deps={bearer:async()=> 'unit-test',rpc:async(route,args)=>{call={route,args};return {entries:[m],has_more:false,cursor:'ignored'};}};
  const r=await O.execute('listFolder',{path:'/测试',limit:10},deps);
  assert.deepEqual(call,{route:'files/list_folder',args:{path:'/测试',recursive:false,include_deleted:false,limit:10}});
  assert.equal(r.cursor,null);assert.equal(r.entries.length,1);
});
test('UTF-8 full read has independent byte/hash/version verification',()=>{
  const r=O.verifyRead(m,{bytes,metadata:JSON.stringify(m)});
  assert.equal(r.text,bytes.toString('utf8'));assert.equal(r.sha256,crypto.createHash('sha256').update(bytes).digest('hex'));
  assert.equal(r.full_read,true);assert.equal(r.truncated,false);assert.equal(r.dropbox_content_hash_verified,true);
  assert.equal(O.contentHash(Buffer.alloc(0)),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855');
});
test('actual Dropbox Download FileMetadata has no union tag',()=>{
  const {['.tag']:ignored,...header}=m;
  assert.equal(O.verifyRead(m,{bytes,metadata:JSON.stringify(header)}).text,bytes.toString('utf8'));
  assert.throws(()=>O.verifyRead(m,{bytes,metadata:JSON.stringify({...header,'.tag':'folder'})}),code('READ_UNVERIFIED'));
  assert.throws(()=>O.verifyRead(m,{bytes,metadata:JSON.stringify({...header,rev:'changed'})}),code('READ_UNVERIFIED'));
});
test('changed revision, hash, ID, length and missing download metadata stop',()=>{
  for(const delta of [{rev:'changed'},{content_hash:'0'.repeat(64)},{id:'id:other'},{size:2}])assert.throws(()=>O.verifyRead(m,{bytes,metadata:JSON.stringify({...m,...delta})}),code('READ_UNVERIFIED'));
  assert.throws(()=>O.verifyRead(m,{bytes:bytes.subarray(0,-1),metadata:JSON.stringify(m)}),code('READ_UNVERIFIED'));
  assert.throws(()=>O.verifyRead(m,{bytes,metadata:null}),code('READ_UNVERIFIED'));
});
test('invalid UTF-8 and NUL are not ordinary text',()=>{
  for(const [b,error] of [[Buffer.from([0xc3,0x28]),'NOT_UTF8'],[Buffer.from('x\0y'),'NOT_TEXT']]){
    const meta={...m,size:b.length,content_hash:O.contentHash(b)};
    assert.throws(()=>O.verifyRead(meta,{bytes:b,metadata:JSON.stringify(meta)}),code(error));
  }
});
test('large or cloud-only objects never start download',async()=>{
  let downloaded=0;for(const meta of [{...m,size:C.MAX_TEXT+1},{...m,is_downloadable:false}]){
    const deps={bearer:async()=> 'unit-test',rpc:async()=>meta,request:async()=>{downloaded++;}};
    await assert.rejects(O.execute('readText',{path:m.id},deps),code(meta.is_downloadable===false?'NOT_DOWNLOADABLE':'TOO_LARGE'));
  }assert.equal(downloaded,0);
});
test('bounded stream rejects oversize and incomplete content',async()=>{
  await assert.rejects(C.collect(new Response(Buffer.from('12345')),4),code('TOO_LARGE'));
  await assert.rejects(C.collect(new Response(Buffer.from('123'),{headers:{'content-length':'5'}}),10),code('INCOMPLETE_READ'));
  assert.equal((await C.collect(new Response(Buffer.from('123')),3)).length,3);
});
test('scope set and PKCE authorization match original read-only boundary',()=>{
  const f=A.flow('public_test_app',false,'epoch');const u=new URL(f.url);
  assert.equal(u.origin,'https://www.dropbox.com');assert.equal(u.pathname,'/oauth2/authorize');
  assert.equal(u.searchParams.get('redirect_uri'),C.REDIRECT);assert.equal(u.searchParams.get('code_challenge_method'),'S256');
  assert.equal(u.searchParams.get('code_challenge'),crypto.createHash('sha256').update(f.verifier).digest('base64url'));
  assert.deepEqual(C.scopeCheck(u.searchParams.get('scope')),C.SCOPES);
  assert.throws(()=>C.scopeCheck(C.SCOPES.join(' ')+' files.content.write'),code('SCOPE_MISMATCH'));
  assert.throws(()=>C.scopeCheck('files.metadata.read'),code('SCOPE_MISMATCH'));
  assert.equal(new URL(A.flow('public_test_app',true,'epoch').url).searchParams.has('redirect_uri'),false);
});
test('exchange verifies account and scope before saving, code is one-use',async()=>{
  const f=A.flow('public_test_app',false,'epoch');let saved=0,checked=0;
  const deps={request:async(url,{form})=>{assert.equal(form.code_verifier,f.verifier);assert.equal(form.client_secret,undefined);return {access_token:'unit-only',scope:C.SCOPES.join(' ')};},scopeCheck:C.scopeCheck,rpc:async()=>{checked++;return {account_id:'dbid:unit-only'};},commitToken:()=>{assert.equal(checked,1);saved++;}};
  assert.equal((await A.exchange(f,'unit-code-123',deps)).connected,true);assert.equal(saved,1);
  await assert.rejects(A.exchange(f,'unit-code-123',deps),code('BAD_CALLBACK'));
  const bad=A.flow('public_test_app',false,'epoch');
  await assert.rejects(A.exchange(bad,'unit-code-123',{...deps,request:async()=>({scope:'files.content.write'})}),code('SCOPE_MISMATCH'));assert.equal(saved,1);
});
test('private local session and logout epoch prevent late credential writes',()=>{
  C.writeJSON('app.json',{app_key:'public_test_app'});const ep=C.epoch();
  const t={access_token:'unit-access-only',refresh_token:'unit-refresh-only',expires_in:3600,token_type:'bearer',scope:C.SCOPES.join(' ')};
  C.commitToken(t,'public_test_app',ep);assert.equal(C.session().app_key,'public_test_app');
  if(process.platform!=='win32')assert.equal(fs.statSync(path.join(C.stateDir(),'session.json')).mode&0o777,0o600);
  C.logout();assert.throws(()=>C.session(),code('AUTH_REQUIRED'));assert.throws(()=>C.commitToken(t,'public_test_app',ep),code('AUTH_CANCELLED'));
});
test('symlink and repository private-state locations rejected',()=>{
  const saved=process.env.JIUWENSWARM_DATA_DIR;const real=path.join(temp,'real');fs.mkdirSync(real);
  const link=path.join(temp,'linked');fs.symlinkSync(real,link,'dir');process.env.JIUWENSWARM_DATA_DIR=link;
  assert.throws(()=>C.stateDir(),code('UNSAFE_STATE'));
  const repo=path.join(temp,'repo');fs.mkdirSync(repo);fs.mkdirSync(path.join(repo,'.git'));process.env.JIUWENSWARM_DATA_DIR=repo;
  assert.throws(()=>C.stateDir(),code('UNSAFE_STATE'));process.env.JIUWENSWARM_DATA_DIR=saved;
});
test('malformed local JSON has a clear safe argument error',()=>{
  const p=path.join(temp,'bad-params.json');fs.writeFileSync(p,'{"path":"/a"} extra');
  assert.throws(()=>CLI.parse(['call','readText','--params-file',p]),code('BAD_ARGUMENTS'));
  assert.throws(()=>CLI.parse(['status','extra']),code('BAD_ARGUMENTS'));
  assert.deepEqual(C.publicError(new Error('untrusted secret text')),{ok:false,code:'CLIENT_FAILED',message:'Dropbox 操作未完成，请检查连接后重试。'});
});
test('hostile API URL is rejected before any network request',async()=>{
  await assert.rejects(C.request('https://example.com/collect',{token:'unit-only'}),code('SCOPE_REJECTED'));
  await assert.rejects(C.request('https://api.dropboxapi.com/2/files/delete_v2',{json:{path:'/a'}}),code('SCOPE_REJECTED'));
});
async function freePort(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
async function isOpen(port){return new Promise(r=>{const s=net.connect(port,'127.0.0.1');s.once('connect',()=>{s.destroy();r(true);});s.once('error',()=>r(false));});}
test('loopback config rejects CSRF, wrong state stays pending, Deny closes',async()=>{
  const port=await freePort();let gate;let ready;const opened=new Promise(r=>{ready=r;});
  const login=A.login({port,lifetime:10000,onUrl:u=>{gate=u;ready();}});const observed=login.catch(e=>e);await opened;
  let response=await fetch(gate);assert.equal(response.status,200);assert.equal(response.headers.get('referrer-policy'),'same-origin');assert.match(response.headers.get('content-security-policy'),/form-action 'self' https:\/\/www\.dropbox\.com/);
  response=await fetch(gate+'/config',{method:'POST',headers:{Origin:'https://evil.example','Content-Type':'application/x-www-form-urlencoded'},body:'app_key=public_test_app&mode=redirect'});assert.equal(response.status,400);
  response=await fetch(gate+'/config',{method:'POST',redirect:'manual',headers:{Origin:'http://127.0.0.1:'+port,'Content-Type':'application/x-www-form-urlencoded'},body:'app_key=public_test_app&mode=redirect'});assert.equal(response.status,303);
  response=await fetch(new URL(response.headers.get('location'),gate),{redirect:'manual'});assert.equal(response.status,302);
  const official=new URL(response.headers.get('location')),state=official.searchParams.get('state');
  response=await fetch('http://localhost:'+port+'/oauth/callback?state=wrong&error=access_denied');assert.equal(response.status,400);assert.equal(await isOpen(port),true);
  response=await fetch('http://localhost:'+port+'/oauth/callback?state='+state+'&error=access_denied');assert.equal(response.status,400);assert.match(await response.text(),/授权已拒绝或取消/);
  assert.equal((await observed).code,'AUTH_DENIED');assert.equal(await isOpen(port),false);
});
test('bounded worker closes callback on timeout',async()=>{
  let seen=false;const result=await CLI.bounded({mode:'login'},{timeoutMs:1200,onUrl:()=>{seen=true;}});
  assert.equal(seen,true);assert.equal(result.code,'AUTH_TIMEOUT');
  for(let n=0;n<20&&await isOpen(C.PORT);n++)await new Promise(r=>setTimeout(r,50));
  assert.equal(await isOpen(C.PORT),false);
});
