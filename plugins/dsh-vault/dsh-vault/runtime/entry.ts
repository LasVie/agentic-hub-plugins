// WorkSwarm 中文适配。MIT 上游核心见 ../vendor/ 与 licenses/dsh-vault/LICENSE。
import { readFile, writeFile, rename, mkdir, stat, lstat, chmod } from 'node:fs/promises';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { deriveKey, newKdfParams, encrypt, decrypt } from '../vendor/crypto.js';
import { totp } from '../vendor/totp.js';
let text='';for await(const chunk of process.stdin)text+=chunk;
const input = JSON.parse(text);
async function main(q:any) {
 const dir=q.directory;const file=join(dir,'vault.json');
 const save=async(header:any,data:any,key:Buffer)=>{
  const encrypted=encrypt(Buffer.from(JSON.stringify(data)),key);
  const temp=join(dir,`pending-${randomUUID()}.json`);
  await writeFile(temp,JSON.stringify({...header,encrypted}),{flag:'wx',mode:0o600});
  await rename(temp,file);await chmod(file,0o600);
 };
 if(typeof q.master_password!=='string'||q.master_password.length<12)throw Error('主口令至少需要12个字符，请在本地配置。');
 await mkdir(dir,{recursive:true,mode:0o700});
 if((await lstat(dir)).isSymbolicLink())throw Error('保险库目录不能是符号链接。');
 if(q.action==='init'){
  try{await lstat(file);throw Error('保险库已存在，不能覆盖初始化。');}catch(e:any){if(e.code!=='ENOENT')throw e;}
  const kdf=newKdfParams();const key=await deriveKey(q.master_password,kdf);
  await save({version:1,kdf},{entries:{}},key);key.fill(0);
  return {ok:true,message:'本地加密保险库已建立。',directory:dir};
 }
 if((await lstat(file)).isSymbolicLink()||(await stat(file)).size>2*1024*1024)throw Error('保险库文件路径或大小不正确。');
 const header=JSON.parse(await readFile(file,'utf8'));const k=header.kdf;
 if(header.version!==1||k?.algo!=='scrypt'||k.n!==32768||k.r!==8||k.p!==1||!/^[0-9a-f]{32}$/.test(k.saltHex))throw Error('保险库格式或密钥参数不受支持。');
 const key=await deriveKey(q.master_password,k);let data:any;
 try{data=JSON.parse(decrypt(header.encrypted,key).toString('utf8'));}catch{key.fill(0);throw Error('主口令不正确或保险库内容已被修改。');}
 try{
  const id=q.id;if(!data.entries||typeof data.entries!=='object'||Array.isArray(data.entries))throw Error('保险库内部格式不正确。');
  if(q.action==='list')return {ok:true,message:'已读取保险库条目，未返回秘密。',entries:Object.values(data.entries).filter((x:any)=>String(x.label).includes(q.query??'')).map((e:any)=>({id:e.id,label:e.label,username:e.username,secret:'********',has_totp:!!e.totp_secret}))};
  if(typeof id!=='string'||! /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(id))throw Error('条目 ID 只能使用字母、数字、下划线与短横线，最长64字符。');
  const found=Object.prototype.hasOwnProperty.call(data.entries,id)?data.entries[id]:undefined;
  if(q.action==='put'){
   const c=q.credential;
   if(!c||typeof c.label!=='string'||!c.label||typeof c.secret!=='string'||!c.secret||JSON.stringify(c).length>20000)throw Error('本地凭据文件必须包含 label 和 secret，且大小受限。');
   if(c.totp_secret)try{totp(c.totp_secret);}catch{throw Error('动态验证码密钥格式不正确。');}
   if(found&&!q.overwrite)throw Error('该条目已存在；明确设置 overwrite 才能更新。');
   data.entries[id]={id,label:c.label,username:String(c.username??''),secret:c.secret,...(c.totp_secret?{totp_secret:c.totp_secret}:{}),updated_at:new Date().toISOString()};
   await save({version:1,kdf:k},data,key);return {ok:true,message:'凭据已加密保存，未返回秘密。',id};
  }
  if(!found)throw Error('未找到该凭据条目。');
  if(q.action==='get')return {ok:true,message:'凭据已读取，秘密已掩码。',entry:{id,label:found.label,username:found.username,secret:'********',has_totp:!!found.totp_secret}};
  if(q.action==='totp'){
   if(!found.totp_secret)throw Error('该凭据没有动态验证码密钥。');
   return {ok:true,message:'已在本地生成当前动态验证码，请勿对外分享。',id,code:totp(found.totp_secret,q.now_ms??Date.now())};
  }
  if(q.action==='remove'){
   if(q.confirm!==true)throw Error('删除需要明确设置 confirm=true。');
   delete data.entries[id];await save({version:1,kdf:k},data,key);return {ok:true,message:'凭据已从加密保险库移除。',id};
  }
  throw Error('不支持该保险库操作。');
 }finally{key.fill(0);}
}
try { process.stdout.write(JSON.stringify(await main(input))); }
catch(e:any) { const m=String(e.message);process.stdout.write(JSON.stringify({ok:false,message:/[\u4e00-\u9fff]/.test(m)?m:'保险库文件不可读或格式错误，操作未完成。'})); }
