'use strict';
const http=require('node:http'),crypto=require('node:crypto');
const {assertAuthorizationUrl}=require('./scope.cjs');
async function createLoginBridge() {
  const nonce=crypto.randomBytes(24).toString('hex');
  let authorizationUrl=null,errorMessage=null;
  const server=http.createServer((req,res)=>{
    res.setHeader('Cache-Control','no-store');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('X-Content-Type-Options','nosniff');
    const send=(status,body,type='text/html; charset=utf-8')=>{res.writeHead(status,{'Content-Type':type});res.end(body);};
    if(req.method!=='GET' || req.headers.host!==`127.0.0.1:${server.address().port}`)return send(403,'请求来源不匹配。');
    if(req.url===`/${nonce}/state`)return send(200,JSON.stringify({authorization_url:authorizationUrl,error:errorMessage}),'application/json; charset=utf-8');
    if(req.url!==`/${nonce}`)return send(404,'入口不存在或已经失效。');
    send(200,`<!doctype html><meta charset="utf-8"><title>连接 Jira Cloud</title><h1>连接 Jira Cloud</h1><p>目标是 Atlassian 官方 MCP。请在下一页核对账号与站点，并在 30 分钟内完成授权。</p><p>申请范围：Jira 读取、搜索、写入；服务要求的基本账号读取（read:me、read:account）与离线刷新。连接器只开放查询、读取、新建工单，不开放其他产品、删除或管理工具。</p><p id="status">正在准备 Atlassian 授权入口…</p><a id="authorize" hidden rel="noreferrer">前往 Atlassian 授权</a><script>
async function check(){try{const r=await fetch(location.pathname+'/state',{cache:'no-store'});if(!r.ok)throw Error();const s=await r.json();if(s.error){document.getElementById('status').textContent=s.error+' 请回到 WorkSwarm 取消连接后重试。';return;}if(s.authorization_url){document.getElementById('status').textContent='入口已准备好。请前往官方页面核对权限并同意。';const a=document.getElementById('authorize');a.href=s.authorization_url;a.hidden=false;return;}setTimeout(check,1000);}catch{document.getElementById('status').textContent='连接入口已结束或网络不可用，请回到 WorkSwarm 取消连接后重试。';}}check();
</script>`);
  });
  server.requestTimeout=10000;server.headersTimeout=5000;
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  return {url:`http://127.0.0.1:${server.address().port}/${nonce}`,
    setAuthorizationUrl(value){assertAuthorizationUrl(value);authorizationUrl=String(value);},
    fail(message){errorMessage=String(message);},
    close(){server.close();server.closeAllConnections?.();}};
}
module.exports={createLoginBridge};
