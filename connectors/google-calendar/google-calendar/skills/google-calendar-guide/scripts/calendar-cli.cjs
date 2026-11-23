/* Team-authored bounded Calendar CLI. Google OAuth uses the unmodified pinned
 * google-auth-library API; Calendar requests use the unmodified pinned gws.
 * No generic gws command, token export or automatic business-flow login.
 */
'use strict';
const fs = require('node:fs'), path = require('node:path'), http = require('node:http'), crypto = require('node:crypto');
const {spawn} = require('node:child_process');
const store = require('./storage.cjs'), {request, SCOPE} = require('./scope.cjs');
const {error} = store;
const VERSION = '1.1.0';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
function runtimeDir() { return store.location('runtime'); }
function minimalEnv() {
  const out = {};
  for (const k of ['HOME','USERPROFILE','APPDATA','LOCALAPPDATA','SYSTEMROOT','SystemRoot','COMSPEC','TEMP','TMP','TMPDIR','LANG','LC_ALL','PATH','HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy']) if (process.env[k]) out[k] = process.env[k];
  out.PATH = path.dirname(process.execPath) + path.delimiter + (out.PATH || '');
  return out;
}
function bounded(file, args, {env = minimalEnv(), timeout = 25000} = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, {env, shell: false, stdio: ['ignore','pipe','pipe'], detached: process.platform !== 'win32'});
    let stdout = '', stderr = '', failure, killTimer;
    const kill = sig => {try { if (process.platform === 'win32') child.kill(sig); else process.kill(-child.pid, sig); } catch {}};
    const stop = code => { failure ||= error(code, code === 'CANCELLED' ? '操作已取消。' : '请求超时，请检查网络。'); kill('SIGTERM'); killTimer ||= setTimeout(() => kill('SIGKILL'), 1000); };
    const abort = () => stop('CANCELLED');
    process.once('SIGINT', abort); process.once('SIGTERM', abort);
    const timer = setTimeout(() => stop('TIMEOUT'), timeout);
    for (const [stream, key] of [[child.stdout, 'out'],[child.stderr, 'err']]) stream.on('data', b => {
      if (key === 'out') stdout += b.toString(); else stderr += b.toString();
      if (Buffer.byteLength(stdout) + Buffer.byteLength(stderr) > 2*1024*1024) stop('OUTPUT_LIMIT');
    });
    child.once('error', () => { failure = error('RUNTIME_MISSING', '无法启动固定版本客户端，请从卡片重新安装。'); });
    child.once('close', code => {
      clearTimeout(timer); clearTimeout(killTimer); process.removeListener('SIGINT', abort); process.removeListener('SIGTERM', abort);
      if (failure) reject(failure); else resolve({code, stdout, stderr});
    });
  });
}
function runtime() {
  const root = runtimeDir(), record = store.read(store.location('runtime.json'));
  const binary = path.join(root, 'node_modules/@googleworkspace/cli/bin', process.platform === 'win32' ? 'gws.exe' : 'gws');
  const auth = path.join(root, 'node_modules/google-auth-library');
  for (const [dir, version] of [[path.dirname(path.dirname(binary)), '0.22.5'],[auth, '11.3.4']]) {
    if (JSON.parse(fs.readFileSync(path.join(dir, 'package.json'))).version !== version) throw error('RUNTIME_MISMATCH', '固定版本客户端校验失败，请重新安装。');
  }
  if (record.lock_sha256 !== sha(fs.readFileSync(path.join(__dirname,'package-lock.json'))) || record.binary_sha256 !== sha(fs.readFileSync(binary))) throw error('RUNTIME_MISMATCH', '客户端文件校验失败，请重新安装。');
  return {root, binary, auth};
}
async function prepare() {
  if (Number(process.versions.node.split('.')[0]) < 22) throw error('NODE_VERSION', '本连接器需要 Node.js 22 或更新版本。');
  try {runtime(); return {ok: true, message: '固定版本客户端已经准备好。'};} catch {}
  const bin = path.dirname(process.execPath), npm = [path.join(bin,'../lib/node_modules/npm/bin/npm-cli.js'),path.join(bin,'node_modules/npm/bin/npm-cli.js')].find(p => fs.existsSync(p));
  if (!npm) throw error('NPM_MISSING', '当前 Node.js 缺少 npm，请使用包含 Node.js 与 npm 的 WorkSwarm 环境。');
  fs.mkdirSync(runtimeDir(), {recursive: true, mode: 0o700});
  for (const f of ['package.json','package-lock.json']) fs.copyFileSync(path.join(__dirname,f), path.join(runtimeDir(),f));
  const env = {...minimalEnv(), npm_config_cache: store.location('npm-cache'), npm_config_update_notifier:'false'};
  let result = await bounded(process.execPath,[npm,'ci','--prefix',runtimeDir(),'--ignore-scripts','--no-audit','--no-fund','--registry=https://registry.npmjs.org/'],{env,timeout:105000});
  if (result.code !== 0) throw error('INSTALL_FAILED', '客户端下载失败，请检查 registry.npmjs.org 网络后重试。');
  result = await bounded(process.execPath,[path.join(runtimeDir(),'node_modules/@googleworkspace/cli/install.js')],{env,timeout:105000});
  if (result.code !== 0) throw error('INSTALL_FAILED', 'gws 下载失败，请检查 GitHub Release 网络后重试。');
  const binary = path.join(runtimeDir(),'node_modules/@googleworkspace/cli/bin',process.platform === 'win32' ? 'gws.exe':'gws');
  result = await bounded(binary,['--version']);
  if (result.code !== 0 || !result.stdout.startsWith('gws 0.22.5')) throw error('RUNTIME_MISMATCH','gws 版本不匹配。');
  store.write('runtime.json',{lock_sha256:sha(fs.readFileSync(path.join(__dirname,'package-lock.json'))),binary_sha256:sha(fs.readFileSync(binary))});
  runtime();
  return {ok:true,message:'Google 日历固定版本客户端准备完成，无需安装 Python。'};
}
function providerFailure(result) {
  let code, status;
  try {const e=JSON.parse(result.stdout).error; code=e?.code; status=e?.status;} catch {}
  const diagnostic = result.stdout + result.stderr; // inspect locally; never print raw credential-bearing errors
  if (code === 401 || status === 'UNAUTHENTICATED' || /invalid_grant|invalid_token|Token has been expired|No credentials found|Token refresh failed with status 400/.test(diagnostic)) return error('AUTH_REQUIRED','Google 授权已失效，请从日历卡片重新连接。');
  if (code === 403 || status === 'PERMISSION_DENIED') return error('ACCESS_DENIED','Google 拒绝访问，请检查 Calendar API、授权范围及主日历权限。');
  if (code === 404) return error('NOT_FOUND','未找到这条日程，请核对日程标识和账号。');
  return error('SERVICE_FAILED','Google 日历请求未完成，请检查网络与服务状态；写入请先回读核对。');
}
async function api(req) {
  const rt = runtime(), creds = store.read(store.location('credentials.json'),true);
  if (!creds?.refresh_token) throw error('AUTH_REQUIRED','Google 日历尚未授权，请从连接器卡片连接。');
  // gws's own token acquisition failed in the real 0.2.8 test, while the
  // official Node refresh and gws direct-token path both succeeded. Keep
  // refresh management in Google's Node library; pass only a short-lived
  // access token to the finite gws child, never through argv or stdout.
  const {OAuth2Client}=require(rt.auth);
  const auth=new OAuth2Client({clientId:creds.client_id,clientSecret:creds.client_secret,transporterOptions:{timeout:15000,retry:false}});
  auth.setCredentials({refresh_token:creds.refresh_token});
  let token;
  try { token=(await auth.getAccessToken()).token; }
  catch(e) {
    if(e.response?.status===400 || e.response?.status===401)throw error('AUTH_REQUIRED','Google 授权已失效，请从日历卡片重新连接。');
    throw error('SERVICE_FAILED','Google 令牌刷新未完成，请检查网络后重试。');
  }
  if(!token)throw error('AUTH_REQUIRED','Google 未返回有效会话，请从日历卡片重新连接。');
  const env = {...minimalEnv(), GOOGLE_WORKSPACE_CLI_CONFIG_DIR:store.location('gws'),GOOGLE_WORKSPACE_CLI_TOKEN:token};
  fs.mkdirSync(env.GOOGLE_WORKSPACE_CLI_CONFIG_DIR,{recursive:true,mode:0o700});
  const args = ['calendar','events',req.method,'--params',JSON.stringify(req.params),'--format','json', ...(req.body ? ['--json',JSON.stringify(req.body)] : [])];
  try {
    const result = await bounded(rt.binary,args,{env});
    if (result.code !== 0) throw providerFailure(result);
    const value=JSON.parse(result.stdout);
    if (!value || value.error) throw providerFailure(result);
    return value;
  } catch(e) {
    if (req.body) {e.event_id=req.body.id; e.writeOutcome='unknown';}
    throw e;
  }
}
function authorizeOptions(client, redirect, state, challenge) {
  return client.generateAuthUrl({access_type:'offline',prompt:'select_account consent',scope:[SCOPE],include_granted_scopes:false,
    redirect_uri:redirect,state,code_challenge:challenge,code_challenge_method:'S256'});
}
async function login() {
  const rt=runtime(), {OAuth2Client}=require(rt.auth);
  const attempt=crypto.randomBytes(24).toString('hex');
  store.write('attempt.json',{id:attempt});
  let config=store.loadClient(), client, verifier, state, used=false, completed=false, done, rejectDone, timer, heartbeat;
  const controller=new AbortController();
  const finished = new Promise((resolve,reject)=>{done=resolve;rejectDone=reject;});
  const server=http.createServer(async(req,res)=>{
    res.setHeader('Cache-Control','no-store'); res.setHeader('Referrer-Policy','no-referrer');res.setHeader('X-Content-Type-Options','nosniff');
    const reply=(code,body,type='text/html; charset=utf-8')=>{if(!res.destroyed){res.writeHead(code,{'Content-Type':type});res.end(body);}};
    try {
      const u=new URL(req.url,'http://127.0.0.1');
      if (req.headers.host !== `127.0.0.1:${server.address().port}`) return reply(403,'请求来源不匹配。');
      if (u.pathname===`/${attempt}` && req.method==='GET') return reply(200,`<!doctype html><meta charset="utf-8"><title>连接 Google 日历</title><h1>连接 Google 日历</h1><p>仅申请您自有日历的日程权限。授权信息只保存在本机。</p>${config?`<a href="/${attempt}/authorize">前往 Google 授权</a>`:`<p>请上传您在 Google Cloud 创建的 Desktop app OAuth JSON。</p><input id="file" type="file" accept=".json"><button id="save">保存并继续</button><p id="result"></p><script>document.getElementById('save').onclick=async()=>{try{const f=document.getElementById('file').files[0];if(!f)throw Error();const r=await fetch(location.pathname+'/configure',{method:'POST',headers:{'Content-Type':'application/json'},body:await f.text()});if(r.ok)location.reload();else document.getElementById('result').textContent='无法保存，请核对 Desktop OAuth JSON。'}catch{document.getElementById('result').textContent='请先选择有效的 JSON 文件。'}};</script>`}`);
      if (u.pathname===`/${attempt}/configure` && req.method==='POST' && !config) {
        if (req.headers.origin !== `http://127.0.0.1:${server.address().port}` || !req.headers['content-type']?.startsWith('application/json')) return reply(403,'请求来源不匹配。');
        let body='';for await(const chunk of req){body+=chunk;if(Buffer.byteLength(body)>32768)throw error('INVALID_CLIENT','文件过大。');}
        config=store.client(JSON.parse(body));store.write('client.json',config);return reply(200,'配置已保存。');
      }
      if (u.pathname===`/${attempt}/authorize` && req.method==='GET' && config && !used) {
        if (!client) {
          const redirect=`http://127.0.0.1:${server.address().port}/${attempt}/callback`;
          client=new OAuth2Client({clientId:config.installed.client_id,clientSecret:config.installed.client_secret,redirectUri:redirect,transporterOptions:{timeout:20000,retry:false,signal:controller.signal}});
          verifier=await client.generateCodeVerifierAsync();state=crypto.randomBytes(32).toString('hex');
        }
        res.writeHead(302,{Location:authorizeOptions(client,client.redirectUri,state,verifier.codeChallenge)});return res.end();
      }
      if (u.pathname===`/${attempt}/callback` && req.method==='GET' && client && !used) {
        if (u.searchParams.get('state') !== state) return reply(400,'授权状态不匹配，请返回 WorkSwarm 重新连接。');
        used=true;
        if (u.searchParams.has('error')) {reply(200,'Google 授权未完成，请返回 WorkSwarm 重新连接。');rejectDone(error('AUTH_DENIED','Google 授权已被拒绝，可以从卡片重新连接。'));return;}
        const code=u.searchParams.get('code');if(!code)throw error('AUTH_DENIED','Google 没有返回授权码。');
        const {tokens}=await client.getToken({code,codeVerifier:verifier.codeVerifier});
        if(!tokens.refresh_token || tokens.scope && !tokens.scope.split(' ').includes(SCOPE))throw error('AUTH_DENIED','Google 未返回所需日历权限，请从卡片重试并同意。');
        if(store.read(store.location('attempt.json'),true)?.id!==attempt)throw error('CANCELLED','这次授权已被取消或替代。');
        store.write('credentials.json',{type:'authorized_user',client_id:config.installed.client_id,client_secret:config.installed.client_secret,refresh_token:tokens.refresh_token});
        completed=true;reply(200,`<!doctype html><meta charset="utf-8"><title>Google 日历授权完成</title><script>history.replaceState(null,'','/${attempt}/complete')</script><h1>Google 授权已返回本机</h1><p>请返回 WorkSwarm。</p>`);done();return;
      }
      reply(404,'页面不存在或授权入口已经失效。');
    } catch(e) {reply(400,'授权未完成，请返回 WorkSwarm 检查配置并重试。');rejectDone(e);}
  });
  server.requestTimeout=25000;server.headersTimeout=10000;
  const abort=()=>{controller.abort();rejectDone(error('CANCELLED','Google 授权已取消。'));};
  process.once('SIGINT',abort);process.once('SIGTERM',abort);
  try {
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    console.log(`http://127.0.0.1:${server.address().port}/${attempt}`);
    heartbeat=setInterval(()=>console.log('等待 Google 授权完成…'),2000);
    timer=setTimeout(()=>rejectDone(error('TIMEOUT','Google 授权超时，请从卡片重新连接。')),180000);
    await finished;
    const check=await api(request('list',{from:new Date().toISOString(),to:new Date(Date.now()+60000).toISOString(),limit:1}));
    return {ok:true,connected:true,message:'Google 日历授权成功，已实际查询主日历验证。',verified:true};
  } finally {
    controller.abort();
    if(!completed && store.read(store.location('attempt.json'),true)?.id===attempt)store.write('attempt.json',{id:crypto.randomBytes(24).toString('hex')});
    clearTimeout(timer);clearInterval(heartbeat);server.close();server.closeAllConnections?.();process.removeListener('SIGINT',abort);process.removeListener('SIGTERM',abort);
  }
}
function safeFailure(e) {
  const known=new Set(['BAD_ARGUMENTS','UNSAFE_STORAGE','INVALID_CREDENTIALS','INVALID_CLIENT','RUNTIME_MISSING','RUNTIME_MISMATCH','NODE_VERSION','NPM_MISSING','INSTALL_FAILED','CANCELLED','TIMEOUT','OUTPUT_LIMIT','AUTH_REQUIRED','AUTH_DENIED','ACCESS_DENIED','NOT_FOUND','SERVICE_FAILED']);
  return {ok:false,code:known.has(e.code)?e.code:'CLIENT_FAILED',message:known.has(e.code)?e.message:'Google 日历操作未完成，请核对参数、网络和本机配置。',
    ...(e.writeOutcome?{writeOutcome:'unknown',event_id:e.event_id,recovery:'先按此日程标识回读，禁止直接重试创建。'}:{})};
}
async function main(args=process.argv.slice(2)) {
  const mode=args[0];
  try {
    let result;
    if(mode==='version'){try{runtime();console.log(VERSION);}catch{console.log('0.0.0');}return;}
    if(mode==='prepare')result=await prepare();
    else if(mode==='login')result=await login();
    else if(mode==='configure' && args.length===2){store.write('client.json',store.client(store.read(path.resolve(args[1]))));result={ok:true,message:'Desktop OAuth 配置已保存，请从卡片连接。'};}
    else if(mode==='logout'){
      store.write('attempt.json',{id:crypto.randomBytes(24).toString('hex')});
      fs.rmSync(store.location('credentials.json'),{force:true});fs.rmSync(store.location('gws'),{recursive:true,force:true});
      result={ok:true,connected:false,message:'Google 日历本地授权已断开。Google 账号中的应用授权可在账号安全页面管理。'};
    } else if(mode==='status') {
      await api(request('list',{from:new Date().toISOString(),to:new Date(Date.now()+60000).toISOString(),limit:1}));
      result={ok:true,connected:true,version:VERSION,message:'已实际查询主日历，授权有效。'};
    } else if(['list','read','create'].includes(mode) && args.length===3 && args[1]==='--input-file'){
      const st=fs.statSync(args[2]);if(!st.isFile() || st.size>16384)throw error('BAD_ARGUMENTS','参数须为小于 16 KiB 的 UTF-8 JSON 文件。');
      const req=request(mode,JSON.parse(fs.readFileSync(args[2],'utf8')));
      result={ok:true,calendar:'primary',result:await api(req)};
    } else throw error('BAD_ARGUMENTS','支持 prepare、version、login、logout、status、configure 路径，以及 list/read/create --input-file 参数.json。');
    console.log(JSON.stringify(result));
  }catch(e){const out=safeFailure(e);if(mode==='status')out.connected=false;console.log(JSON.stringify(out));if(mode!=='status')process.exitCode=1;}
}
module.exports={main,request,authorizeOptions,bounded,safeFailure,VERSION};
if(require.main===module)main();
