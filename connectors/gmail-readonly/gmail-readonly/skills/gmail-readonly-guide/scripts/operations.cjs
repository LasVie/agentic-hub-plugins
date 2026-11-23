'use strict';
const fs=require('node:fs'),crypto=require('node:crypto');
const S=require('./storage.cjs'), M=require('./gmail-message.cjs');
const SCOPES=['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.compose'];
const OPERATIONS={
  search:'按 Gmail 查询语句搜索邮件标识，有界分页；不搜索垃圾邮件和回收站。',
  'read-message':'按邮件 ID 读取邮件头和有界正文，不下载附件。',
  'read-thread':'按会话 ID 读取多封邮件，明确返回截断标志。',
  'list-drafts':'有界查询草稿 ID；可传 query 缩小到指定测试主题。',
  'read-draft':'按草稿 ID 读取正文、To/Cc/Bcc 和当前消息 ID。',
  'create-draft':'在明确账号和收件人下创建普通文本草稿，须唯一 requestId。',
  'edit-draft':'编辑指定草稿，先核对消息版本和最终收件人，保留附件。',
  send:'发送新的普通文本邮件；一次提交，不自动重试。',
  'send-draft':'先核对指定草稿当前版本及全部收件人，再发送一次。',
  reply:'读取原邮件并核对明确回复目标，在原会话回复一次。'
};
const WRITES=new Set(['create-draft','edit-draft','send','send-draft','reply']);
const bad=s=>{throw S.error('BAD_ARGUMENTS',s);};
function keys(p,allowed,required=[]){if(!p||Array.isArray(p)||typeof p!=='object'||Object.keys(p).some(k=>!allowed.includes(k))||required.some(k=>!Object.hasOwn(p,k)))bad('参数字段缺失或含未开放字段。');}
function id(v){if(typeof v!=='string'||!/^[A-Za-z0-9_-]{1,256}$/.test(v))bad('请使用 Gmail 返回的真实邮件、会话或草稿 ID。');return v;}
function integer(v,min,max){if(!Number.isInteger(v)||v<min||v>max)bad(`数值须为 ${min} 至 ${max} 的整数。`);return v;}
function validate(mode,p){
  if(!Object.hasOwn(OPERATIONS,mode))throw S.error('SCOPE_REJECTED','本包未开放该操作。');
  const common=WRITES.has(mode)?['expectedAccount','expectedRecipients','requestId']:[];
  const fields={search:['query','limit','pageToken'],'read-message':['messageId','maxChars'],'read-thread':['threadId','maxChars','maxMessages'],'list-drafts':['query','limit','pageToken'],'read-draft':['draftId','maxChars'],'create-draft':['to','subject','body'],'edit-draft':['draftId','expectedMessageId','to','subject','body'],send:['to','subject','body'],'send-draft':['draftId','expectedMessageId'],reply:['messageId','body']};
  const required={search:[],'read-message':['messageId'],'read-thread':['threadId'],'list-drafts':[],'read-draft':['draftId'],'create-draft':['to','subject','body'],'edit-draft':['draftId','expectedMessageId'],send:['to','subject','body'],'send-draft':['draftId','expectedMessageId'],reply:['messageId','body']};
  keys(p,[...fields[mode],...common],[...required[mode],...common]);
  for(const k of ['messageId','threadId','draftId','expectedMessageId'])if(Object.hasOwn(p,k))id(p[k]);
  if(Object.hasOwn(p,'query'))M.single(p.query,'查询',2048);
  if(Object.hasOwn(p,'pageToken'))M.single(p.pageToken,'分页标识',2048);
  if(Object.hasOwn(p,'limit'))integer(p.limit,1,20);
  if(Object.hasOwn(p,'maxChars'))integer(p.maxChars,1,mode==='read-thread'?30000:20000);
  if(Object.hasOwn(p,'maxMessages'))integer(p.maxMessages,1,20);
  if(Object.hasOwn(p,'to'))M.recipients(p.to);
  if(Object.hasOwn(p,'subject'))M.single(p.subject,'主题');
  if(Object.hasOwn(p,'body'))M.body(p.body);
  if(mode==='edit-draft'&&!['to','subject','body'].some(k=>Object.hasOwn(p,k)))bad('请明确要编辑的草稿字段。');
  if(WRITES.has(mode)){
    M.mailbox(p.expectedAccount);if(typeof p.requestId!=='string'||!/^[A-Za-z0-9_-]{16,128}$/.test(p.requestId))bad('写入需要 16 至 128 字符的唯一 requestId。');
    keys(p.expectedRecipients,['to','cc','bcc'],['to','cc','bcc']);for(const k of ['to','cc','bcc'])M.recipients(p.expectedRecipients[k],true);
    if(!p.expectedRecipients.to.length)bad('必须明确至少一名收件人。');
  }
  return p;
}
function sameRecipients(actual,expected){for(const k of ['to','cc','bcc']){const a=(actual[k]??[]).map(x=>M.mailbox(x).toLowerCase()).sort(),b=expected[k].map(x=>x.toLowerCase()).sort();if(JSON.stringify(a)!==JSON.stringify(b))throw S.error('RECIPIENT_MISMATCH','实际 To/Cc/Bcc 与明确核对的收件人不同，未执行写入。');}}
function recipientsOf(message){const h=M.headerMap(message.payload);return{to:M.addresses(M.one(h,'to')),cc:M.addresses(M.one(h,'cc')),bcc:M.addresses(M.one(h,'bcc'))};}
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])]));return v;}
function journal(mode,p){
  const key=crypto.createHash('sha256').update(p.requestId).digest('hex'),name='write-'+key+'.json';
  const fingerprint=crypto.createHash('sha256').update(JSON.stringify(canonical({mode,p}))).digest('hex');
  const existing=S.read(S.location(name),true);
  if(existing){if(existing.fingerprint!==fingerprint)throw S.error('WRITE_CONFLICT','requestId 已用于其他参数，操作停止。');if(existing.state==='completed')return{cached:existing.result};throw S.error('WRITE_PENDING','此写入已有未确认记录；请先独立回读，禁止自动重发或换 requestId 重发。');}
  return{reserve(){let fd;try{fd=fs.openSync(S.location(name),'wx',0o600);fs.writeFileSync(fd,JSON.stringify({fingerprint,state:'pending',mode,created:new Date().toISOString()}));}catch(e){if(e.code==='EEXIST')throw S.error('WRITE_PENDING','同一 requestId 正在执行，请先回读。');throw e;}finally{if(fd!==undefined)fs.closeSync(fd);}},complete(result){S.write(name,{fingerprint,state:'completed',mode,result});}};
}
function get(resource,params={}){return{method:'GET',resource,params};}
function write(resource,body,method='POST'){return{method,resource,body};}
function publicReceipt(v){if(!v||typeof v.id!=='string'||!/^[A-Za-z0-9_-]{1,256}$/.test(v.id))throw S.error('WRITE_UNKNOWN','Google 响应缺少有效标识，请先回读核对。');return{message_id:v.id,thread_id:v.threadId??''};}
async function execute(mode,p,{api}){
  validate(mode,p);
  if(mode==='search'){
    const v=await api(get('messages',{q:p.query??'',maxResults:p.limit??5,includeSpamTrash:false,...(p.pageToken?{pageToken:p.pageToken}:{}),fields:'messages(id,threadId),nextPageToken,resultSizeEstimate'}));
    if(v.messages!==undefined&&!Array.isArray(v.messages))throw S.error('INVALID_RESPONSE','Google 邮件列表结构无效。');
    return{messages:(v.messages??[]).map(x=>({message_id:id(x.id),thread_id:id(x.threadId)})),next_page_token:v.nextPageToken??'',result_size_estimate:v.resultSizeEstimate,has_more:!!v.nextPageToken};
  }
  if(mode==='list-drafts'){
    const v=await api(get('drafts',{q:p.query??'',maxResults:p.limit??5,...(p.pageToken?{pageToken:p.pageToken}:{}),fields:'drafts(id,message(id,threadId)),nextPageToken,resultSizeEstimate'}));
    if(v.drafts!==undefined&&!Array.isArray(v.drafts))throw S.error('INVALID_RESPONSE','Google 草稿列表结构无效。');
    return{drafts:(v.drafts??[]).map(x=>({draft_id:id(x.id),message_id:id(x.message.id),thread_id:id(x.message.threadId)})),next_page_token:v.nextPageToken??'',has_more:!!v.nextPageToken};
  }
  if(mode==='read-message')return M.message(await api(get('messages/'+p.messageId,{format:'full'})),p.maxChars??12000);
  if(mode==='read-draft'){const v=await api(get('drafts/'+p.draftId,{format:'full'}));if(v.id!==p.draftId)throw S.error('INVALID_RESPONSE','草稿标识不匹配。');return{draft_id:v.id,...M.message(v.message,p.maxChars??12000),recipients:recipientsOf(v.message)};}
  if(mode==='read-thread'){
    const v=await api(get('threads/'+p.threadId,{format:'full'}));if(v.id!==p.threadId||!Array.isArray(v.messages))throw S.error('INVALID_RESPONSE','会话响应无效。');
    let budget=p.maxChars??24000;const messages=[];
    for(const m of v.messages.slice(0,p.maxMessages??10)){if(budget<=0)break;const item=M.message(m,budget);budget-=Array.from(item.body_text).length;messages.push(item);}
    return{thread_id:v.id,messages,messages_available:v.messages.length,count:messages.length,truncated:messages.length<v.messages.length||messages.some(x=>x.body_truncated)};
  }
  const profile=await api(get('profile',{fields:'emailAddress'}));const account=M.mailbox(profile.emailAddress);
  if(account.toLowerCase()!==p.expectedAccount.toLowerCase())throw S.error('ACCOUNT_MISMATCH','当前授权账号与预期不同，未执行写入。');
  if(process.env.WORKSWARM_GMAIL_SELF_ONLY==='1'&&(p.expectedRecipients.cc.length||p.expectedRecipients.bcc.length||p.expectedRecipients.to.length!==1||p.expectedRecipients.to[0].toLowerCase()!==account.toLowerCase()))throw S.error('RECIPIENT_MISMATCH','本次测试环境仅允许发给当前邮箱自己，不能抄送或密送。');
  const transaction=journal(mode,p);if(transaction.cached)return{...transaction.cached,already_submitted:true};
  let request,context={};
  if(mode==='send'||mode==='create-draft'){
    sameRecipients({to:p.to,cc:[],bcc:[]},p.expectedRecipients);
    const mime=M.newMessage(account,p.to,p.subject,p.body);context.rfc822_message_id=mime.rfc822_message_id;
    request=mode==='send'?write('messages/send',{raw:mime.raw}):write('drafts',{message:{raw:mime.raw}});
  }else if(mode==='edit-draft'||mode==='send-draft'){
    const v=await api(get('drafts/'+p.draftId,{format:'raw'}));
    if(v.id!==p.draftId||v.message?.id!==p.expectedMessageId)throw S.error('DRAFT_CHANGED','草稿版本已经改变，请重新读取并核对，未执行写入。');
    const wire=M.parseWire(M.decode64(v.message.raw).toString('latin1'));
    const actual={to:p.to??M.addresses(M.one(wire.headers,'to')),cc:M.addresses(M.one(wire.headers,'cc')),bcc:M.addresses(M.one(wire.headers,'bcc'))};
    sameRecipients(actual,p.expectedRecipients);
    const from=M.addresses(M.one(wire.headers,'from'));if(from.length!==1||from[0].toLowerCase()!==account.toLowerCase())throw S.error('ACCOUNT_MISMATCH','草稿发件身份与当前邮箱不同，请先在 Gmail 核对。');
    context.draft_id=p.draftId;
    request=mode==='send-draft'?write('drafts/send',{id:p.draftId}):write('drafts/'+p.draftId,{message:{raw:M.editDraft(v.message.raw,p),...(p.subject===undefined&&v.message.threadId?{threadId:id(v.message.threadId)}:{})}},'PUT');
  }else if(mode==='reply'){
    const v=await api(get('messages/'+p.messageId,{format:'metadata',metadataHeaders:['From','Reply-To','Subject','Message-ID','References','In-Reply-To']}));
    if(v.id!==p.messageId)throw S.error('INVALID_RESPONSE','原邮件标识不匹配。');
    const h=M.headerMap(v.payload),to=M.addresses(M.one(h,'reply-to')||M.one(h,'from'));if(to.length!==1)throw S.error('INVALID_REPLY','回复目标不唯一。');
    sameRecipients({to,cc:[],bcc:[]},p.expectedRecipients);
    const parent=M.single(M.one(h,'message-id'),'Message-ID');const pattern=/^<[^<>\s@]+@[^<>\s@]+>$/;
    if(!pattern.test(parent))throw S.error('INVALID_REPLY','原邮件缺少有效 Message-ID。');
    const refs=M.single(M.one(h,'references')||M.one(h,'in-reply-to'),'References',8192).split(/\s+/).filter(Boolean);
    if(refs.some(x=>!pattern.test(x))||refs.length>50)throw S.error('INVALID_REPLY','原邮件会话引用异常。');
    const mime=M.newMessage(account,to,M.decodeHeader(M.one(h,'subject')),p.body,{'In-Reply-To':parent,References:[...refs,parent].join(' ')});
    context={rfc822_message_id:mime.rfc822_message_id,reply_to_message_id:p.messageId,thread_id:id(v.threadId)};
    request=write('messages/send',{threadId:context.thread_id,raw:mime.raw});
  }
  transaction.reserve();
  try{
    const v=await api(request);let result;
    if(mode==='create-draft'||mode==='edit-draft'){
      if(mode==='edit-draft'&&v.id!==p.draftId)throw S.error('WRITE_UNKNOWN','Google 返回的草稿 ID 不一致。');
      result={draft_id:id(v.id),...publicReceipt(v.message)};
    }else result=publicReceipt(v);
    if(mode==='reply'&&result.thread_id!==context.thread_id)throw S.error('WRITE_UNKNOWN','回复会话标识不一致，请先核对 Gmail。');
    result={...context,...result,account,request_id:p.requestId,recipients:p.expectedRecipients,submitted_once:true,readback_required:true};transaction.complete(result);return result;
  }catch(e){e.writeOutcome='unknown';e.recovery={request_id:p.requestId,...context};throw e;}
}
module.exports={SCOPES,OPERATIONS,WRITES,validate,execute,sameRecipients,recipientsOf,journal};
