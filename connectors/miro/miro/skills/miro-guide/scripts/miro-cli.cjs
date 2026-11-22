/* Independently authored bounded CLI bridge to Miro's hosted MCP.
 * OAuth and the protocol client remain in the pinned MIT mcp-remote runtime.
 * Never open its token/client/verifier files or log its stderr.
 */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const {spawn} = require('node:child_process');
const {pathToFileURL} = require('node:url');
const {EventEmitter} = require('node:events');
const {argumentError, ALLOWED, SCOPES, assertAuthorizationUrl, assertSchemas, visibleOperations} = require('./scope.cjs');
const {executeOperation}=require('./canvas-ops.cjs');
const {createLoginBridge}=require('./login-bridge.cjs');
const VERSION = '1.1.0';
const PIN = '0.16.6';
const LOGIN_TIMEOUT_MS = 30 * 60 * 1000;
const ENDPOINT = 'https://mcp.miro.com/';
const MODULE = 'dist/chunk-MKB2ICYW.js';
const MODULE_SHA = '8e4e647f0b25dc52a28a6d1cbbb6727851ae0e5ae74a6f2ea23cb4acb7b47638';
const META = {client_name: 'WorkSwarm Miro Connector', client_uri: 'https://workswarm.app', scope: SCOPES.join(' ')};
const sha = bytes => require('node:crypto').createHash('sha256').update(bytes).digest('hex');
function stateDir() {
  const root = process.env.JIUWENSWARM_DATA_DIR || process.env.JIUWENSWARM_HOME || path.join(os.homedir(), '.jiuwenswarm');
  const dir = path.resolve(root, 'connector-data', 'miro', 'cli-v1');
  for (let p = dir; ; p = path.dirname(p)) {
    if (fs.existsSync(path.join(p,'.git')) || fs.existsSync(p) && fs.lstatSync(p).isSymbolicLink()) throw error('SCOPE_REJECTED','Miro 本地授权目录须位于源码仓库之外，不能经过符号链接。');
    if (p === path.dirname(p)) break;
  }
  fs.mkdirSync(dir,{recursive:true,mode:0o700});
  const info=fs.statSync(dir);
  if (process.platform !== 'win32' && (info.uid !== process.getuid() || info.mode & 0o077)) throw error('SCOPE_REJECTED','Miro 本地授权目录须归当前用户所有，权限为 700。');
  return dir;
}
function error(code, message) { return Object.assign(new Error(message), {code}); }
function callbackPort(directory=stateDir()) {
  // Separate independent host profiles; the upstream default hashes only
  // the endpoint and can follow a callback owned by a different profile.
  return 20000 + parseInt(sha(directory).slice(0,8),16) % 30000;
}
function runtimeModule(root) {
  const metadata = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (metadata.name !== 'mcp-remote' || metadata.version !== PIN) throw error('RUNTIME_MISSING', '固定版本的标准客户端尚未准备好，请从卡片重新连接。');
  const file = path.join(root, MODULE);
  if (sha(fs.readFileSync(file)) !== MODULE_SHA) throw error('RUNTIME_MISMATCH', '标准客户端文件校验失败，请重新准备运行环境。');
  return file;
}
function installedRuntime() {
  const record = JSON.parse(fs.readFileSync(path.join(stateDir(), 'runtime.json'), 'utf8'));
  runtimeModule(record.root);
  return record.root;
}
function nodeSupported() {
  const [major, minor] = process.versions.node.split('.').map(Number);
  return major > 22 || major === 22 && minor >= 12;
}

// A finite child is the only owner of sockets and callback servers. It must
// exit before success is reported, independently of the host's MCP cache.
function runBounded(file, args, {env = process.env, input = '', timeoutMs = 45000,
  graceMs = 1500, onProgress = () => {}} = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, {env, shell: false, detached: process.platform !== 'win32',
      stdio: ['pipe', 'pipe', 'ignore', 'ipc']});
    let stdout = '', outputBytes = 0, failure, forceTimer, attempted = false;
    const terminate = signal => {
      if (child.exitCode !== null || child.signalCode !== null) return;
      try {
        if (process.platform === 'win32') child.kill(signal);
        else process.kill(-child.pid, signal);
      } catch (e) { if (e.code !== 'ESRCH') child.kill(signal); }
    };
    const stop = reason => {
      if (failure) return;
      failure = reason;
      terminate('SIGTERM');
      forceTimer = setTimeout(() => terminate('SIGKILL'), graceMs);
    };
    const abort = () => stop(error('CANCELLED', 'Miro 操作已取消。'));
    process.once('SIGTERM', abort); process.once('SIGINT', abort);
    const timer = setTimeout(() => stop(error('TIMEOUT', 'Miro 操作超时，请检查网络或重新连接。')), timeoutMs);
    child.on('message', message => {
      if (message && message.type === 'write-started') attempted = true;
      try { onProgress(message); } catch(e) { stop(e); }
    });
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', chunk => {
      outputBytes += Buffer.byteLength(chunk, 'utf8');
      if (outputBytes > 2 * 1024 * 1024) stop(error('OUTPUT_LIMIT', '返回内容过大，请缩小查询范围。'));
      else stdout += chunk;
    });
    child.once('error', e => { failure ||= error('RUNTIME_MISSING', '无法启动 Node.js 客户端。'); });
    child.once('close', code => {
      clearTimeout(timer); clearTimeout(forceTimer);
      process.removeListener('SIGTERM', abort); process.removeListener('SIGINT', abort);
      if (failure) { failure.writeAttempted = attempted; reject(failure); }
      else resolve({stdout, code, attempted});
    });
    child.stdin.on('error', () => {});
    child.stdin.end(input);
  });
}

async function prepare() {
  if (!nodeSupported()) throw error('NODE_VERSION', '本连接器需要 Node.js 22.12.0 或更新版本。');
  const bin = path.dirname(process.execPath);
  const candidates = [path.join(bin, '../lib/node_modules/npm/bin/npx-cli.js'), path.join(bin, 'node_modules/npm/bin/npx-cli.js')];
  const npx = candidates.find(p => fs.existsSync(p));
  if (!npx) throw error('NPM_MISSING', '当前 Node.js 缺少 npm，请使用包含 Node.js 与 npm 的 WorkSwarm 运行环境。');
  const resolver = "const fs=require('node:fs'),p=require('node:path');for(const d of process.env.PATH.split(p.delimiter)){const r=p.resolve(d,'..','mcp-remote');try{const m=JSON.parse(fs.readFileSync(p.join(r,'package.json'),'utf8'));if(m.name==='mcp-remote'&&m.version==='0.16.6'){console.log(r);process.exit(0)}}catch{}}process.exit(1)";
  const env = {...process.env, PATH: bin + path.delimiter + (process.env.PATH || ''),
    npm_config_cache: path.join(stateDir(), 'npm-cache'),
    npm_config_ignore_scripts: 'true', npm_config_registry: 'https://registry.npmjs.org/', npm_config_update_notifier: 'false'};
  const result = await runBounded(process.execPath, [npx, '--yes', '--package', 'mcp-remote@' + PIN,
    'node', '-e', resolver], {env, timeoutMs: 105000});
  if (result.code !== 0) throw error('INSTALL_FAILED', '标准客户端下载失败，请检查 npm 网络后重试。');
  const root = result.stdout.trim().split('\n').pop();
  runtimeModule(root);
  fs.mkdirSync(stateDir(), {recursive: true, mode: 0o700});
  fs.writeFileSync(path.join(stateDir(), 'runtime.json'), JSON.stringify({root, version: PIN}), {mode: 0o600});
  return {ok: true, message: '固定版本的 Miro 标准客户端已准备完成。'};
}

function inputFile(args) {
  if (args.length !== 4 || args[0] !== 'call' || args[2] !== '--input-file') throw error('BAD_ARGUMENTS', '用法：call 工具名 --input-file 参数文件.json');
  const info = fs.statSync(args[3]);
  if (!info.isFile() || info.size > 65536) throw error('BAD_ARGUMENTS', '参数必须是小于 64 KiB 的 UTF-8 JSON 文件。');
  const value = JSON.parse(fs.readFileSync(args[3], 'utf8'));
  const reason = argumentError(args[1], value);
  if (reason) throw error('SCOPE_REJECTED', reason);
  return {tool: args[1], arguments: value};
}
function safeFailure(e) {
  const known = new Set(['RUNTIME_MISSING','RUNTIME_MISMATCH','NODE_VERSION','NPM_MISSING','INSTALL_FAILED',
    'BAD_ARGUMENTS','SCOPE_REJECTED','SCOPE_EXPANDED','CANCELLED','TIMEOUT','OUTPUT_LIMIT','AUTH_REQUIRED','AUTH_DENIED','SERVICE_FAILED','READ_UNVERIFIED','WRITE_UNCERTAIN']);
  return {ok: false, code: known.has(e.code) ? e.code : 'CLIENT_FAILED',
    message: known.has(e.code) ? e.message : 'Miro 请求失败，请核对参数、网络和账号权限。',
    ...(e.writeAttempted ? {writeOutcome: 'unknown', recovery: '写入结果尚不明确，请先读取指定白板并核对唯一便签标记，禁止直接重试。'} : {})};
}
function unwrap(result) {
  if (result.structuredContent !== undefined) return result.structuredContent;
  if (result.content?.length === 1 && result.content[0].type === 'text') {
    try { return JSON.parse(result.content[0].text); } catch { /* retain business text */ }
  }
  return result;
}

async function worker(mode, request) {
  let client, server, authRequired = false, writeAttempted = false;
  // WorkSwarm 0.2.8 can kill the CLI parent without forwarding a signal.
  // IPC disconnect must close every socket even when SIGTERM never arrives.
  process.once('disconnect',()=>process.exit(1));
  const hardDeadline=setTimeout(()=>{
    const failure=error('TIMEOUT','Miro 操作超时，请从卡片重试。');failure.writeAttempted=writeAttempted;
    process.stdout.write(JSON.stringify(safeFailure(failure))+'\n',()=>process.exit(1));
    setTimeout(()=>process.exit(1),500).unref();
  },mode==='login'?LOGIN_TIMEOUT_MS+10000:50000);
  hardDeadline.unref();
  let payload;
  try {
    const modulePath = runtimeModule(request.runtimeRoot);
    const lib = await import(pathToFileURL(modulePath).href);
    const opts = await lib.parseCommandLineArgs([ENDPOINT, String(callbackPort()), '--transport', 'http-only', '--protocol', 'auto',
      '--auth-timeout', String(LOGIN_TIMEOUT_MS / 1000), '--static-oauth-client-metadata', JSON.stringify(META)], 'Miro CLI');
    const canLogin = mode === 'login';
    if (!canLogin && mode !== 'logout' && !await lib.hasUsableTokens(opts.serverUrlHash)) {
      throw error('AUTH_REQUIRED', 'Miro 尚未授权或登录已失效，请从连接器卡片重新连接。');
    }
    class Provider extends lib.NodeOAuthClientProvider {
      async redirectToAuthorization(url) {
        if (!canLogin) { authRequired = true; throw error('AUTH_REQUIRED', 'Miro 尚未授权或登录已失效，请从连接器卡片重新连接。'); }
        // Adapted from mcp-remote 0.16.6 NodeOAuthClientProvider (MIT,
        // Copyright (c) 2025 Cloudflare, Inc.). Preserve pending-flow,
        // registration and storm checks; hand the URL to the stock card
        // instead of spawning a second browser window.
        if (this.inTokenStorm()) throw this.tokenStormError();
        if (!this.ownsPendingFlow(url)) return;
        this.applyScope(url); this.applyAuthorizeParams(url);
        assertAuthorizationUrl(url);
        await this.preflightCachedDynamicClientRegistration(url);
        this.guardAgainstAuthorizationStorm();
        process.send?.({type: 'auth-url', url: url.toString()});
      }
    }
    const basic = {callbackPath: opts.callbackPath, callbackPort: opts.callbackPort, host: opts.host,
      clientName: 'WorkSwarm Miro Connector', staticOAuthClientMetadata: META, serverUrlHash: opts.serverUrlHash};
    if (mode === 'logout') {
      const provider = new Provider({...basic, serverUrl: ENDPOINT, resourceServerUrl: ENDPOINT});
      await provider.invalidateCredentials('all');
      payload = {ok: true, connected: false, message: 'Miro 本地授权已断开。远端账号授权请在 Miro 中管理。'};
    } else {
      const discovery = await lib.discoverOAuthServerInfo(ENDPOINT, {});
      const provider = new Provider({...basic, serverUrl: discovery.authorizationServerUrl, resourceServerUrl: ENDPOINT,
        fetchFn: lib.createFetchWithInit(lib.fetchWithMcpHeaders, {headers: {}}),
        authorizationServerMetadata: discovery.authorizationServerMetadata,
        protectedResourceMetadata: discovery.protectedResourceMetadata, wwwAuthenticateScope: discovery.wwwAuthenticateScope});
      const coordinator = canLogin ? lib.createLazyAuthCoordinator(opts.serverUrlHash, opts.callbackPath,
        opts.callbackPort, new EventEmitter(), LOGIN_TIMEOUT_MS, false) : null;
      const initializeAuth = async options => {
        if (!canLogin) { authRequired = true; throw error('AUTH_REQUIRED', 'Miro 尚未授权或登录已失效，请从连接器卡片重新连接。'); }
        const state = await coordinator.initializeAuth(options);
        server = state.server;
        if (state.actualPort !== opts.callbackPort) provider.setCallbackPort(state.actualPort);
        return {waitForAuthCode: state.waitForAuthCode, skipBrowserAuth: state.skipBrowserAuth};
      };
      if (canLogin && !await lib.hasUsableTokens(opts.serverUrlHash) && await lib.serverIssuesAuthChallenge(ENDPOINT, {})) await initializeAuth();
      client = new lib.Client({name: 'workswarm-miro-cli', version: VERSION}, {capabilities: {}, versionNegotiation: {mode: 'auto'}});
      await lib.connectToRemoteServer(client, ENDPOINT, provider, {}, initializeAuth, 'http-only', 'auto');
      const grantedScope = (await provider.tokens())?.scope;
      if (grantedScope && grantedScope.split(/\s+/).some(s => !SCOPES.includes(s))) throw error('SCOPE_EXPANDED', '服务返回了本包范围之外的授权，请断开并核对权限。');
      const tools = [];
      let cursor, seen = new Set();
      do {
        const page = await client.request({method: 'tools/list', ...(cursor ? {params: {cursor}} : {})});
        tools.push(...(page.tools || []).filter(t => ALLOWED.has(t.name)));
        cursor = page.nextCursor;
        if (cursor && (seen.has(cursor) || seen.size >= 10)) throw error('SERVICE_FAILED', '工具分页无法完成，请稍后重试。');
        if (cursor) seen.add(cursor);
      } while (cursor);
      assertSchemas(tools);
      if(mode==='call'){
        const result=await executeOperation(request.tool,request.arguments,{
          call:(name,args)=>client.request({method:'tools/call',params:{name,arguments:args}}),
          beginWrite:()=>{writeAttempted=true;process.send?.({type:'write-started'});},
          receiptRoot:path.join(stateDir(),'write-receipts')
        });
        payload={ok:true,operation:request.tool,result};
      }else payload={ok:true,connected:true,version:VERSION,requested_scopes:SCOPES,message:'Miro 授权有效，已核对可用工具；目标白板权限需实际读取确认。',...(mode==='tools'?{operations:visibleOperations(),upstream_tools:tools.map(t=>t.name)}:{})};
    }
  } catch (e) {
    if (e.code === 'access_denied' || /^Authorization failed:\s*access_denied\b/.test(e.message||'')) e = error('AUTH_DENIED', 'Miro 授权已被拒绝，可以从卡片取消或重新连接。');
    else if (['invalid_grant','invalid_token'].includes(e.code) || e.status === 401) authRequired = true;
    if (authRequired) e = error('AUTH_REQUIRED', 'Miro 尚未授权或登录已失效，请从连接器卡片重新连接。');
    e.writeAttempted = writeAttempted;
    payload = safeFailure(e);
    if (mode === 'status') payload.connected = false;
  } finally {
    if (client) await Promise.race([Promise.resolve().then(() => client.close()).catch(() => {}), new Promise(r => setTimeout(r, 1000))]);
    if (server) { server.close(); server.closeAllConnections?.(); }
    clearTimeout(hardDeadline);
  }
  process.stdout.write(JSON.stringify(payload) + '\n', () => process.exit(payload.ok ? 0 : 1));
}

async function main(args = process.argv.slice(2)) {
  const mode = args[0];
  if (mode === '__worker') {
    let text = '';
    for await (const chunk of process.stdin) {
      text += chunk;
      if (text.length > 131072) throw error('BAD_ARGUMENTS', '参数过大。');
    }
    return worker(args[1], JSON.parse(text));
  }
  let heartbeat, bridge;
  try {
    if (mode === 'version') {
      try { if (!nodeSupported()) throw new Error(); installedRuntime(); console.log(VERSION); }
      catch { console.log('0.0.0'); }
      return;
    }
    if (mode === 'prepare') { console.log(JSON.stringify(await prepare())); return; }
    if (!['login','logout','status','tools','call'].includes(mode)) throw error('BAD_ARGUMENTS', '支持 prepare、version、login、logout、status、tools 和 call。');
    let runtimeRoot;
    try { runtimeRoot = installedRuntime(); }
    catch { if (mode === 'logout') { console.log(JSON.stringify({ok: true, connected: false, message: 'Miro 当前没有已准备的本地会话。'})); return; } throw error('RUNTIME_MISSING', '请先从 WorkSwarm 卡片安装并连接 Miro。'); }
    const request = {runtimeRoot, ...(mode === 'call' ? inputFile(args) : {})};
    if (mode === 'login') {
      bridge=await createLoginBridge();
      console.log(bridge.url);
      heartbeat = setInterval(() => console.log('等待 Miro 授权完成…'), 10000);
    }
    const env = {...process.env, MCP_REMOTE_CONFIG_DIR: path.join(stateDir(), 'mcp-remote')};
    const result = await runBounded(process.execPath, [__filename, '__worker', mode], {env,
      onProgress: message => {if (mode === 'login' && message?.type === 'auth-url') bridge.setAuthorizationUrl(message.url);},
      input: JSON.stringify(request), timeoutMs: mode === 'login' ? LOGIN_TIMEOUT_MS + 15000 : mode === 'status' ? 15000 : 45000});
    let response;
    try { response = JSON.parse(result.stdout.trim()); }
    catch (e) { e.writeAttempted = result.attempted; throw e; }
    console.log(JSON.stringify(response));
    if (bridge && !response.ok) {bridge.fail(response.message);await new Promise(r=>setTimeout(r,3000));}
    if (!response.ok && mode !== 'status') process.exitCode = 1;
  } catch (e) {
    const response = safeFailure(e);
    if (mode === 'status') response.connected = false;
    console.log(JSON.stringify(response));
    if (mode !== 'status') process.exitCode = 1;
  } finally { clearInterval(heartbeat); bridge?.close(); }
}
module.exports = {main, runBounded, inputFile, safeFailure, runtimeModule, callbackPort, VERSION};
if (require.main === module) main().catch(() => { console.log(JSON.stringify({ok: false, code: 'CLIENT_FAILED', message: 'Miro 客户端无法完成请求。'})); process.exitCode = 1; });
