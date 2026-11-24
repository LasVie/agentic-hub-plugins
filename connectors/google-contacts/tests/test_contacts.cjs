'use strict';

const assert = require('node:assert/strict');
const {test} = require('node:test');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const base = '../google-contacts/skills/google-contacts-guide/scripts/';
const {login, authorize, parameters, search, readContact, SCOPE} = require(base + 'contacts-cli.cjs');
const store = require(base + 'storage.cjs');

const desktop = {installed:{client_id:'synthetic.apps.googleusercontent.com',client_secret:'fixture-local',
  auth_uri:'https://accounts.google.com/o/oauth2/auth',token_uri:'https://oauth2.googleapis.com/token'}};
const person = {resourceName:'people/c123',metadata:{sources:[{type:'CONTACT'}]},
  names:[{displayName:'虚构测试联系人'}],emailAddresses:[{value:'fixture@example.com'}]};

test('limits input to saved-contact search and resource reads', () => {
  assert.deepEqual(parameters('search',{query:'  联系人  ',limit:2}),{query:'联系人',limit:2});
  assert.deepEqual(parameters('read',{resource_name:'people/c123'}),{resource_name:'people/c123'});
  for (const input of [{query:'x',limit:0},{query:'x',limit:31},{query:'',limit:2},{query:'x',scope:'other'}]) {
    assert.throws(() => parameters('search',input),{code:'BAD_ARGUMENTS'});
  }
  for (const id of ['people/me','https://example.com','people/c1/other']) {
    assert.throws(() => parameters('read',{resource_name:id}),{code:'BAD_ARGUMENTS'});
  }
});

test('requests only Google Contacts read-only with S256 and no incremental grant', () => {
  const url=authorize(desktop.installed,'http://127.0.0.1:40000/callback','state','fixture');
  assert.equal(url.host,'accounts.google.com');
  assert.equal(url.searchParams.get('scope'),SCOPE);
  assert.equal(url.searchParams.get('include_granted_scopes'),'false');
  assert.equal(url.searchParams.get('code_challenge_method'),'S256');
  assert.equal(url.searchParams.get('code_challenge'),crypto.createHash('sha256').update('fixture').digest('base64url'));
});

test('performs empty warmup then search, and separately verifies the read result', async t => {
  const seen=[];
  t.mock.method(globalThis,'fetch',async (url, options) => {
    assert.equal(url.origin,'https://people.googleapis.com');
    assert.equal(url.searchParams.get('sources'),'READ_SOURCE_TYPE_CONTACT');
    assert.equal(options.headers.Authorization,'Bearer synthetic');
    seen.push([url.pathname,url.searchParams.get('query')]);
    if (url.pathname.endsWith('/c123')) return Response.json(person);
    return Response.json(url.searchParams.get('query') ? {results:[{person}]} : {});
  });
  const rows=await search(parameters('search',{query:'测试',limit:1}),'synthetic');
  const contact=await readContact(parameters('read',{resource_name:rows[0].resource_name}),'synthetic');
  assert.deepEqual(seen,[['/v1/people:searchContacts',''],['/v1/people:searchContacts','测试'],['/v1/people/c123',null]]);
  assert.deepEqual(contact,rows[0]);
  assert.deepEqual(contact.email_addresses,['fixture@example.com']);
});

test('rejects results for a different ID or non-contact source', async t => {
  t.mock.method(globalThis,'fetch',async () => Response.json({...person,resourceName:'people/c999'}));
  await assert.rejects(readContact({resource_name:'people/c123'},'synthetic'),{code:'NOT_FOUND'});
  globalThis.fetch.mock.mockImplementation(async () => Response.json({...person,metadata:{sources:[{type:'PROFILE'}]}}));
  await assert.rejects(readContact({resource_name:'people/c123'},'synthetic'),{code:'NOT_FOUND'});
});

test('binds import and callback, exchanges once and proves API before session storage', async t => {
  const root=fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()),'people-connector-test-'));
  const saved=process.env.JIUWENSWARM_DATA_DIR;
  process.env.JIUWENSWARM_DATA_DIR=root;
  t.after(() => {if (saved) process.env.JIUWENSWARM_DATA_DIR=saved; else delete process.env.JIUWENSWARM_DATA_DIR; fs.rmSync(root,{recursive:true,force:true});});
  let provide;
  const entry=new Promise(r => {provide=r;});
  const realFetch=globalThis.fetch;
  let authorization, exchanged=0;
  t.mock.method(globalThis,'fetch',async (url,opts) => {
    if (String(url).startsWith('http://127.0.0.1:')) return realFetch(url,opts);
    if (String(url)==='https://oauth2.googleapis.com/token') {
      exchanged++;
      assert.equal(opts.body.get('code'),'fixture-code');
      assert.equal(opts.body.get('redirect_uri'),authorization.searchParams.get('redirect_uri'));
      assert.equal(crypto.createHash('sha256').update(opts.body.get('code_verifier')).digest('base64url'),authorization.searchParams.get('code_challenge'));
      return Response.json({access_token:'test-access',refresh_token:'test-refresh',token_type:'Bearer',scope:SCOPE});
    }
    assert.equal(new URL(url).pathname,'/v1/people/me/connections');
    assert.equal(fs.existsSync(store.location('session.json')),false);
    return Response.json({totalItems:0});
  });
  const ready=login(provide);
  const url=await entry;
  const origin=new URL(url).origin;
  assert.match(await fetch(url).then(r=>r.text()),/Desktop OAuth JSON/);
  const config={method:'POST',headers:{Origin:origin,'Content-Type':'application/json'},body:JSON.stringify(desktop)};
  assert.equal((await fetch(url+'/configure',{...config,headers:{...config.headers,Origin:'https://example.com'}})).status,403);
  assert.equal((await fetch(url+'/configure',config)).status,200);
  const redir=await fetch(url+'/authorize',{redirect:'manual'});
  assert.equal(redir.status,302);
  authorization=new URL(redir.headers.get('location'));
  const callback=new URL(authorization.searchParams.get('redirect_uri'));
  callback.search=new URLSearchParams({code:'fixture-code',state:'wrong'});
  assert.equal((await fetch(callback)).status,404);
  callback.searchParams.set('state',authorization.searchParams.get('state'));
  assert.match(await fetch(callback).then(r=>r.text()),/授权已完成/);
  await ready;
  assert.equal(exchanged,1);
  assert.equal(store.read(store.location('session.json')).refresh_token,'test-refresh');
});

test('reports disabled API and a temporary provider error accurately', async t => {
  t.mock.method(globalThis,'fetch',async () => Response.json({error:{details:[{reason:'SERVICE_DISABLED'}]}},{status:403}));
  await assert.rejects(search({query:'test',limit:1},'synthetic'),{code:'API_DISABLED'});
  globalThis.fetch.mock.mockImplementation(async () => Response.json({error:{}},{status:503}));
  await assert.rejects(search({query:'test',limit:1},'synthetic'),{code:'SERVICE_FAILED'});
});
