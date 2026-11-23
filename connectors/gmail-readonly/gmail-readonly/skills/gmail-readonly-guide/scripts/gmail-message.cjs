/* Team-authored MIME helpers, based on public RFC/Gmail contracts. */
'use strict';
const crypto=require('node:crypto');
const {error}=require('./storage.cjs');
const fail=(s)=>{throw error('BAD_ARGUMENTS',s);};
function single(v,name='文本',max=998){if(typeof v!=='string'||Array.from(v).length>max||/[\x00-\x1f\x7f]/.test(v))fail(`${name}须为不含控制字符的单行文本，最多 ${max} 字符。`);return v;}
function body(v){if(typeof v!=='string'||Array.from(v).length>30000||v.includes('\0'))fail('正文须为最多 30000 字符的文本。');return v;}
function mailbox(v){single(v,'邮箱地址',254);if(!/^[A-Za-z0-9.!#$%&'*+\/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$/.test(v)||/[\s<>(),;:\\"\[\]]/.test(v))fail('请提供完整、无显示名称的邮箱地址。');return v;}
function recipients(v,empty=false){if(!Array.isArray(v)||v.length>(empty?20:20)||(!empty&&!v.length))fail('请提供 1 至 20 个收件人邮箱。');return v.map(mailbox);}
function addresses(v){
  if(!v)return [];
  single(v,'邮件地址头',8192);let quoted=false,escaped=false,part='',parts=[];
  for(const c of v){if(escaped){part+=c;escaped=false;continue;}if(c==='\\'&&quoted){part+=c;escaped=true;continue;}if(c==='"')quoted=!quoted;if(c===','&&!quoted){parts.push(part.trim());part='';}else part+=c;}
  if(quoted||escaped)fail('邮件地址头不完整。');parts.push(part.trim());
  return parts.map(p=>{const m=p.match(/^[^<>]*<([^<>]+)>$/);return mailbox(m?m[1]:p);});
}
function decode64(v){if(typeof v!=='string'||!/^[A-Za-z0-9_-]*={0,2}$/.test(v)||v.replace(/=+$/,'').length%4===1)throw error('INVALID_RESPONSE','邮件正文编码无效。');return Buffer.from(v,'base64url');}
function decodeHeader(v){return String(v).replace(/(\?=)[ \t]+(?==\?)/g,'$1').replace(/=\?([^?]{1,64})\?([bq])\?([^?]*)\?=/gi,(_,cs,kind,s)=>{try{const b=kind.toLowerCase()==='b'?Buffer.from(s,'base64'):Buffer.from(s.replace(/_/g,' ').replace(/=([0-9a-f]{2})/gi,(_,x)=>String.fromCharCode(parseInt(x,16))),'latin1');return new TextDecoder(cs,{fatal:true}).decode(b);}catch{return '[邮件头编码无法解码]';}});}
function encodeHeader(v){single(v,'主题');const words=[];let chunk='';for(const c of v){if(Buffer.byteLength(chunk+c)>42){words.push('=?UTF-8?B?'+Buffer.from(chunk).toString('base64')+'?=');chunk='';}chunk+=c;}if(chunk||!words.length)words.push('=?UTF-8?B?'+Buffer.from(chunk).toString('base64')+'?=');return words.join('\r\n ');}
function headerMap(payload){const out={};if(!Array.isArray(payload?.headers))throw error('INVALID_RESPONSE','邮件头结构无效。');for(const h of payload.headers){if(typeof h?.name!=='string'||typeof h.value!=='string')throw error('INVALID_RESPONSE','邮件头结构无效。');const key=h.name.toLowerCase();(out[key]??=[]).push(h.value.replace(/\r?\n[ \t]+/g,' '));}return out;}
function one(map,name){if((map[name]??[]).length>1)throw error('INVALID_RESPONSE','邮件含重复的关键邮件头，操作已停止。');return map[name]?.[0]??'';}
function htmlText(s){return s.replace(/<(script|style|template|head)\b[^>]*>[\s\S]*?<\/\1\s*>/gi,'').replace(/<(?:br|\/p|\/div|\/li|\/tr|hr)\b[^>]*>/gi,'\n').replace(/<[^>]*>/g,'').replace(/&(#x[0-9a-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi,(_,x)=>{if(x[0]==='#'){const n=x[1].toLowerCase()==='x'?parseInt(x.slice(2),16):Number(x.slice(1));return n>0&&n<=0x10ffff&&!(n>=0xd800&&n<=0xdfff)?String.fromCodePoint(n):'�';}return ({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '})[x.toLowerCase()];});}
function partText(p,ctx={count:0},depth=0){
  if(!p||typeof p!=='object'||++ctx.count>200||depth>25)throw error('CONTENT_COMPLEX','邮件 MIME 超过 25 层或 200 个部分。');
  if(p.filename||p.body?.attachmentId||p.mimeType==='message/rfc822')return {text:'',warnings:['附件未下载或展开。']};
  if(p.parts){if(!Array.isArray(p.parts))throw error('INVALID_RESPONSE','邮件 MIME 结构无效。');let parts=p.parts;
    if(p.mimeType==='multipart/alternative')parts=[parts.find(x=>x.mimeType==='text/plain')??parts.find(x=>x.mimeType==='text/html')??parts[0]].filter(Boolean);
    const all=parts.map(x=>partText(x,ctx,depth+1));return {text:all.map(x=>x.text).filter(Boolean).join('\n'),warnings:[...new Set(all.flatMap(x=>x.warnings))]};}
  if(!['text/plain','text/html'].includes(p.mimeType))return{text:'',warnings:[]};
  const headers=headerMap({...p,headers:p.headers??[]}),type=one(headers,'content-type'),charset=type.match(/charset\s*=\s*"?([^";\s]+)/i)?.[1]??'utf-8';
  const raw=decode64(p.body?.data??'');let text,warnings=[];
  try{text=new TextDecoder(charset,{fatal:true}).decode(raw);}catch{text=raw.toString('utf8');warnings.push('字符集无法严格解码，已使用 UTF-8 替代字符。');}
  if(p.mimeType==='text/html'){text=htmlText(text);warnings.push('仅提取 HTML 文本，不加载图片、链接或脚本。');}
  return{text,warnings};
}
function message(raw,maxChars=12000){
  const m=headerMap(raw.payload),p=partText(raw.payload),chars=Array.from(p.text),headers={};
  for(const key of ['from','to','cc','bcc','subject','date','reply-to','message-id','references','in-reply-to'])if(m[key])headers[key]=decodeHeader(one(m,key)).slice(0,8192);
  return{message_id:raw.id,thread_id:raw.threadId,label_ids:raw.labelIds??[],headers,body_text:chars.slice(0,maxChars).join(''),body_chars_available:chars.length,body_truncated:chars.length>maxChars,warnings:p.warnings};
}
function newMessage(sender,to,subject,text,extra={}){
  mailbox(sender);recipients(to);single(subject,'主题');body(text);
  const id='<'+crypto.randomUUID()+'@workswarm.app>';
  const headers=['From: '+sender,'To: '+to.join(', '),'Subject: '+encodeHeader(subject),'Date: '+new Date().toUTCString(),'Message-ID: '+id,'MIME-Version: 1.0','Content-Type: text/plain; charset=UTF-8','Content-Transfer-Encoding: base64'];
  for(const [key,value] of Object.entries(extra)){if(!['In-Reply-To','References'].includes(key))fail('不支持该邮件头。');headers.push(key+': '+single(value,key,8192));}
  const wire=headers.join('\r\n')+'\r\n\r\n'+(Buffer.from(text).toString('base64').match(/.{1,76}/g)??['']).join('\r\n')+'\r\n';
  return{raw:Buffer.from(wire).toString('base64url'),rfc822_message_id:id};
}
function parseWire(wire){
  const split=wire.search(/\r?\n\r?\n/);if(split<0)throw error('INVALID_DRAFT','草稿缺少有效 MIME 头。');
  const match=wire.slice(split).match(/^\r?\n\r?\n/)[0];const text=wire.slice(0,split);
  if(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]|\r(?!\n)/.test(text))throw error('INVALID_DRAFT','草稿邮件头结构异常。');
  const blocks=text.split(/\r?\n(?![ \t])/);const headers={};
  for(const block of blocks){const m=block.match(/^([A-Za-z0-9-]+):[ \t]*([\s\S]*)$/);if(!m)throw error('INVALID_DRAFT','草稿邮件头结构异常。');(headers[m[1].toLowerCase()]??=[]).push(m[2].replace(/\r?\n[ \t]+/g,' '));}
  return{blocks,headers,body:wire.slice(split+match.length)};
}
function patched(parsed,changes,content=parsed.body){const names=new Set(Object.keys(changes).map(x=>x.toLowerCase()));const fields=parsed.blocks.filter(x=>!names.has(x.slice(0,x.indexOf(':')).toLowerCase()));for(const [k,v] of Object.entries(changes))fields.push(k+': '+v);return fields.join('\r\n')+'\r\n\r\n'+content;}
function editText(wire,text,ctx={count:0,edited:0},depth=0){
  if(++ctx.count>200||depth>25)throw error('INVALID_DRAFT','草稿 MIME 结构过于复杂。');
  const p=parseWire(wire),type=one(p.headers,'content-type')||'text/plain',mime=type.split(';')[0].trim().toLowerCase(),disposition=one(p.headers,'content-disposition');
  if(['multipart/signed','multipart/encrypted'].includes(mime))throw error('INVALID_DRAFT','已签名或加密的草稿不支持编辑。');
  if(/attachment/i.test(disposition)||/\b(?:file)?name\s*=/i.test(type+';'+disposition)||mime==='message/rfc822')return wire;
  if(mime.startsWith('multipart/')){
    const boundary=type.match(/\bboundary\s*=\s*(?:"([^"\r\n]+)"|([^;\s]+))/i);const token=boundary?.[1]??boundary?.[2];
    if(!token||token.length>70)throw error('INVALID_DRAFT','草稿缺少有效 MIME 分隔符。');
    const escaped=token.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const re=new RegExp('^--'+escaped+'(--)?[ \\t]*(?:\\r?\\n|$)','gm');
    const matches=[...p.body.matchAll(re)];if(matches.length<2||!matches.at(-1)[1]||matches.slice(0,-1).some(m=>m[1]))throw error('INVALID_DRAFT','草稿 MIME 分隔不完整。');
    let result=p.body.slice(0,matches[0].index);
    for(let i=0;i<matches.length-1;i++){const m=matches[i];result+=m[0]+editText(p.body.slice(m.index+m[0].length,matches[i+1].index),text,ctx,depth+1);}
    result+=p.body.slice(matches.at(-1).index);return patched(p,{},result);
  }
  if(!['text/plain','text/html'].includes(mime))return wire;
  if(text===undefined)return wire;
  const content=mime==='text/html'?'<pre>'+text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')+'</pre>':text;
  ctx.edited++;
  return patched(p,{'Content-Type':mime+'; charset=UTF-8','Content-Transfer-Encoding':'base64'},(Buffer.from(content).toString('base64').match(/.{1,76}/g)??['']).join('\r\n')+'\r\n');
}
function editDraft(raw,{to,subject,body:text}){
  let wire=decode64(raw).toString('latin1'),p=parseWire(wire);const changes={};
  if(to!==undefined)changes.To=recipients(to).join(', ');
  if(subject!==undefined)changes.Subject=encodeHeader(subject);
  if(text!==undefined)body(text);const ctx={count:0,edited:0};wire=editText(wire,text,ctx);if(text!==undefined&&!ctx.edited)throw error('INVALID_DRAFT','草稿没有可编辑的纯文本或 HTML 正文。');p=parseWire(wire);
  const result=Buffer.from(patched(p,changes),'latin1');if(result.length>4*1024*1024)throw error('INVALID_DRAFT','草稿超过编辑的 4 MiB 上限。');
  return result.toString('base64url');
}
module.exports={single,body,mailbox,recipients,addresses,decode64,decodeHeader,encodeHeader,headerMap,one,partText,message,newMessage,parseWire,editDraft};
