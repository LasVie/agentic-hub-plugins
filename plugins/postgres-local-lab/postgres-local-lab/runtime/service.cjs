/* Plugin-owned service. Chinese UI, loopback only, no shell execution. */
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { fork } = require('node:child_process');
const ROOT = path.resolve(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const workspace = fs.realpathSync(process.argv[2]);
const nonce = process.argv[3];
if (!nonce || nonce.length !== 48) throw new Error('Missing lifecycle owner');
const dataDir = path.join(workspace, '.' + config.slug);
if (fs.existsSync(dataDir) && fs.lstatSync(dataDir).isSymbolicLink()) throw new Error('Unsafe data directory');
fs.mkdirSync(dataDir, { recursive: true, mode: 0o700 });
const report = [];
const allowed = (name) => {
  if (typeof name !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}$/.test(name)) throw new Error('名称只能包含字母、数字、下划线和连字符，长度不超过48');
  return name;
};
const file = (name) => {
  const target = path.join(dataDir, name);
  if (fs.existsSync(target) && fs.lstatSync(target).isSymbolicLink()) throw new Error('拒绝符号链接文件');
  return target;
};
const atomic = (name, content) => {
  const target = file(name), tmp = target + '.' + crypto.randomBytes(6).toString('hex') + '.tmp';
  fs.writeFileSync(tmp, content, { mode: 0o600 });
  fs.renameSync(tmp, target);
};
const ctx = {ROOT, workspace, dataDir, config, allowed, file, atomic, report};
const handler = require('./handler.cjs').create(ctx);
let serial = Promise.resolve();
const enqueue = (fn) => { const current = serial.then(fn); serial = current.catch(() => {}); return current; };
function json(res, status, body) {
  res.writeHead(status, {'Content-Type':'application/json; charset=utf-8', 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'});
  res.end(JSON.stringify(body));
}
function body(req) {
  return new Promise((resolve,reject)=>{
    let size = 0, chunks = [];
    req.on('data', b=>{size+=b.length;if(size>40*1024*1024){reject(new Error('输入超过40 MiB限制'));req.destroy();}else chunks.push(b);});
    req.on('end',()=>{try{resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')||'{}'));}catch{reject(new Error('请求必须是有效JSON'));}});
    req.on('error',reject);
  });
}
const mime = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.cjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.wasm':'application/wasm','.svg':'image/svg+xml','.json':'application/json; charset=utf-8','.glb':'model/gltf-binary','.png':'image/png','.data':'application/octet-stream'};
const server = http.createServer(async (req,res)=>{
  try {
    const origin = 'http://127.0.0.1:' + server.address().port;
    if (req.headers.host !== new URL(origin).host) return json(res,403,{ok:false,error:'主机地址无效'});
    if (req.headers.origin && req.headers.origin !== origin) return json(res,403,{ok:false,error:'拒绝跨站请求'});
    res.setHeader('X-Frame-Options','SAMEORIGIN');
    res.setHeader('Referrer-Policy','no-referrer');
    const url = new URL(req.url, origin);
    if (url.pathname === '/health' && req.method === 'GET') {
      if (req.headers['x-workbench-owner'] !== nonce) return json(res,403,{ok:false});
      return json(res,200,{ok:true,slug:config.slug,version:config.version,nonce,payload:ROOT});
    }
    if (url.pathname === '/shutdown' && req.method === 'POST') {
      if(req.headers['x-workbench-owner']!==nonce) return json(res,403,{ok:false});
      await handler.close?.(); json(res,200,{ok:true,message:'工作台已关闭'});
      server.close(()=>process.exit(0)); return;
    }
    if (req.method === 'POST' && url.pathname === '/api/operate') {
      if (!String(req.headers['content-type']||'').startsWith('application/json')) return json(res,415,{ok:false,error:'需要application/json'});
      const input = await body(req);
      const result = await enqueue(()=>handler.operate(input));
      report.push({at:new Date().toISOString(),operation:input.op,ok:result.ok !== false});
      if(report.length>100) report.shift();
      return json(res,200,{ok:true,version:config.version,...result});
    }
    if(req.method !== 'GET') return json(res,405,{ok:false,error:'方法不受支持'});
    if(url.pathname==='/api/state') return json(res,200,{ok:true,config,workspace,events:report,...await handler.state?.()});
    if(url.pathname.startsWith('/download/') || url.pathname.startsWith('/preview/')) {
      const preview=url.pathname.startsWith('/preview/');
      const name = decodeURIComponent(url.pathname.slice(preview?9:10));
      if(!/^[a-zA-Z0-9_.-]{1,100}$/.test(name)||name.startsWith('.')) throw new Error('下载文件名无效');
      const content = handler.download?.(name);
      if(!content) return json(res,404,{ok:false,error:'文件不存在'});
      if(preview && !/^report-[a-zA-Z0-9_-]+\.html$/.test(name)) return json(res,403,{ok:false});
      res.writeHead(200,{'Content-Type':mime[path.extname(name)]||'application/octet-stream','Content-Disposition':(preview?'inline':'attachment')+'; filename="'+name+'"','X-Content-Type-Options':'nosniff'});
      return res.end(content);
    }
    let relative = url.pathname === '/' ? 'web/index.html' : decodeURIComponent(url.pathname.slice(1));
    if(!relative.startsWith('web/')&&!relative.startsWith('vendor/')) return json(res,404,{ok:false,error:'文件不存在'});
    const target=path.resolve(ROOT,relative);
    if(!target.startsWith(ROOT+path.sep)||!fs.existsSync(target)||!fs.statSync(target).isFile()) return json(res,404,{ok:false,error:'文件不存在'});
    if(fs.realpathSync(target)!==target) return json(res,403,{ok:false});
    res.writeHead(200,{'Content-Type':mime[path.extname(target)]||'application/octet-stream','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff'});
    fs.createReadStream(target).pipe(res);
  }catch(error){if(!res.headersSent)json(res,400,{ok:false,error:'操作失败：'+error.message});else res.end();}
});
server.listen(0,'127.0.0.1',()=>{
  const record={slug:config.slug,version:config.version,payload:ROOT,workspace,nonce,pid:process.pid,url:'http://127.0.0.1:'+server.address().port};
  atomic('service.json',JSON.stringify(record)); console.log(JSON.stringify({started:true,url:record.url}));
});
for(const sig of ['SIGINT','SIGTERM'])process.on(sig,async()=>{await handler.close?.();server.close(()=>process.exit(0));});
