export const $=s=>document.querySelector(s);
export function message(text,error=false){const box=$('#message');box.textContent=text;box.className='notice'+(error?' error':'');box.hidden=false;}
export async function api(op,params={}){const r=await fetch('/api/operate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,...params})});const d=await r.json();if(!r.ok||d.ok===false)throw Error(d.error||'操作未完成');return d;}
export async function action(fn){for(const b of document.querySelectorAll('button'))b.disabled=true;try{await fn();}catch(e){message(e.message,true);}finally{for(const b of document.querySelectorAll('button'))b.disabled=false;}}
export function display(node,value){node.textContent=typeof value==='string'?value:JSON.stringify(value,null,2);}
export function table(node,rows,cols){node.replaceChildren();if(!rows.length){node.textContent='暂无数据';return;}const t=document.createElement('table'),head=t.createTHead().insertRow();for(const k of cols){const c=document.createElement('th');c.textContent=k;head.append(c);}const body=t.createTBody();for(const r of rows){const row=body.insertRow();for(const k of cols){const c=row.insertCell();c.textContent=typeof r[k]==='object'?JSON.stringify(r[k]):String(r[k]??'');}}node.append(t);}
export function metric(label,value){const x=document.createElement('div');x.className='metric';const a=document.createElement('span'),b=document.createElement('b');a.textContent=label;b.textContent=String(value);x.append(a,b);return x;}
export function download(name){const a=document.createElement('a');a.href='/download/'+encodeURIComponent(name);a.download=name;a.click();}
export async function fileBytes(input){const f=input.files?.[0];if(!f)throw Error('请先选择文件');if(f.size>25*1024*1024)throw Error('文件超过25 MiB限制');return new Uint8Array(await f.arrayBuffer());}
export function to64(bytes){let s='';for(let i=0;i<bytes.length;i+=8192)s+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(s);}
export function from64(text){return Uint8Array.from(atob(text),c=>c.charCodeAt(0));}
export function prettyBytes(n){return n>=1048576?(n/1048576).toFixed(2)+' MiB':n>=1024?(n/1024).toFixed(1)+' KiB':n+' B';}
export async function init(){const d=await (await fetch('/api/state')).json();$('#title').textContent=d.config.name;$('#version').textContent='v'+d.config.version+' · 本地运行';$('#workspace').textContent=d.workspace;document.title=d.config.name;return d;}
