'use strict';
const fs = require('node:fs');
const {fork} = require('node:child_process');
const C = require('./common.cjs');
const O = require('./operations.cjs');
const A = require('./oauth-gate.cjs');
async function worker(request) {
  if (request.mode === 'login') return A.login({onUrl:url=>process.send?.({type:'url',url})});
  if (request.mode === 'logout') return C.logout();
  if (request.mode === 'status') {
    const account = await C.rpc('users/get_current_account',null,await C.bearer());
    if (typeof account?.account_id !== 'string') throw C.fault('AUTH_UNVERIFIED','Dropbox 账号验证未完成。');
    return {ok:true,connected:true,account_id:account.account_id,scope:C.SCOPES};
  }
  if (request.mode === 'call') return {ok:true,operation:request.operation,result:await O.execute(request.operation,request.params)};
  throw C.fault('BAD_ARGUMENTS','未知 Dropbox 操作。');
}
function bounded(request,{timeoutMs,onUrl=()=>{}}) {
  return new Promise(resolve => {
    const child = fork(__filename,['__worker'],{stdio:['ignore','ignore','ignore','ipc'],windowsHide:true});
    let settled = false; const clean = value => {
      if (settled) return; settled = true; clearTimeout(timer); clearInterval(heartbeat);
      process.off('SIGTERM',stop); process.off('SIGINT',stop);
      try { child.disconnect(); } catch {} child.kill('SIGTERM');
      const force = setTimeout(()=>child.kill('SIGKILL'),700); force.unref(); resolve(value);
    };
    const stop = () => clean(C.publicError(C.fault('AUTH_CANCELLED','Dropbox 操作已取消。')));
    const timer = setTimeout(()=>clean(C.publicError(C.fault(request.mode === 'login'?'AUTH_TIMEOUT':'TIMEOUT','Dropbox 操作超时，请从卡片检查连接。'))),timeoutMs);
    const heartbeat = setInterval(()=>{if(request.mode==='login')process.stdout.write(JSON.stringify({event:'waiting',message:'等待 Dropbox 浏览器授权…'})+'\n');},10000);
    process.once('SIGTERM',stop); process.once('SIGINT',stop);
    child.on('message',m=>{
      if (m?.type === 'url' && request.mode === 'login' && typeof m.url === 'string' && /^http:\/\/127\.0\.0\.1:53682\/[a-f0-9]{48}$/.test(m.url)) onUrl(m.url);
      if (m?.type === 'result') clean(m.result);
    });
    child.once('error',()=>clean(C.publicError(C.fault('CLIENT_FAILED','无法启动 Dropbox 短时任务。'))));
    child.once('exit',()=>{if(!settled)clean(C.publicError(C.fault('CLIENT_FAILED','Dropbox 短时任务已退出，请检查连接。')));});
    child.send(request);
  });
}
function parse(args) {
  const mode = args[0]; if (!['prepare','version','tools','login','logout','status','call'].includes(mode)) throw C.fault('BAD_ARGUMENTS','支持 prepare、version、tools、login、logout、status 和 call。');
  if (mode !== 'call') { if (args.length !== 1) throw C.fault('BAD_ARGUMENTS','该命令不接受额外参数。'); return {mode}; }
  if (args.length !== 4 || args[2] !== '--params-file') throw C.fault('BAD_ARGUMENTS','用法：call 操作名 --params-file UTF-8参数文件。');
  let params;
  try { const s=fs.statSync(args[3]);if(!s.isFile()||s.size>65536)throw Error();params=JSON.parse(fs.readFileSync(args[3],'utf8')); }
  catch { throw C.fault('BAD_ARGUMENTS','参数文件必须是完整、有效的 UTF-8 JSON 对象，且不超过 64 KiB。'); }
  O.validate(args[1],params); return {mode,operation:args[1],params};
}
async function main(args=process.argv.slice(2)) {
  let request,result;
  try {
    request=parse(args);
    if (request.mode==='version') result={ok:true,version:C.VERSION};
    else if(request.mode==='tools')result={ok:true,operations:O.OPERATIONS};
    else if(request.mode==='prepare'){C.stateDir();C.epoch();result={ok:true,message:'Dropbox 的 Node 内置运行环境已准备完成，无需下载 CLI。'};}
    else result=await bounded(request,{timeoutMs:request.mode==='login'?A.LOGIN_MS+5000:request.mode==='status'?20000:45000,onUrl:url=>process.stdout.write(url+'\n')});
  } catch(e){result=C.publicError(e);}
  if(request?.mode==='status'&&!result.ok)result.connected=false;
  process.stdout.write(JSON.stringify(result)+'\n');if(!result.ok&&request?.mode!=='status')process.exitCode=1;
  return result;
}
if(require.main===module){
  if(process.argv[2]==='__worker'){
    if(!process.send)process.exit(1);
    process.once('disconnect',()=>process.exit(0));
    process.once('SIGTERM',()=>process.exit(0));
    process.once('SIGINT',()=>process.exit(0));
    process.once('message',async request=>{
      let result;try{result=await worker(request);}catch(e){result=C.publicError(e);}
      if(process.connected)process.send({type:'result',result},()=>process.exit(0));else process.exit(0);
    });
  }else main();
}
module.exports={main,parse,bounded,worker};
