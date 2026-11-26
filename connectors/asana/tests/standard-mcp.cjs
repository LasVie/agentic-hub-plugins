/* Team-authored standard MCP adapter for documented Asana REST operations. */
'use strict';
const readline = require('node:readline');
const VERSION = '1.1.0';
const ID = {type:'string',pattern:'^[0-9]{1,32}$'};
const TOOLS = [
  {name:'asana_status',description:'检查已配置的 Asana 授权是否有效。',inputSchema:{type:'object',properties:{},additionalProperties:false}},
  {name:'asana_list_tasks',description:'分页读取指定项目的任务，保留服务返回的游标。',inputSchema:{type:'object',properties:{container:ID,limit:{type:'integer',minimum:1,maximum:100,default:25},cursor:{type:'string'}},required:['container'],additionalProperties:false}},
  {name:'asana_read_task',description:'按任务 ID 读取标题、正文、完成状态和所属项目。',inputSchema:{type:'object',properties:{item:ID},required:['item'],additionalProperties:false}},
  {name:'asana_create_task',description:'在用户指定的项目中创建一项有标题的新任务；不修改或删除已有任务。',inputSchema:{type:'object',properties:{container:ID,title:{type:'string',minLength:1,maxLength:1000}},required:['container','title'],additionalProperties:false}},
];
const schemaByName = new Map(TOOLS.map(t=>[t.name,t.inputSchema]));

function validate(name,args) {
  const schema=schemaByName.get(name);
  if(!schema)throw new Error('本连接器不提供该工具。');
  if(!args||typeof args!=='object'||Array.isArray(args))throw new Error('参数必须是 JSON 对象。');
  if(Object.keys(args).some(k=>!Object.hasOwn(schema.properties,k)))throw new Error('存在超出允许范围的参数。');
  for(const key of schema.required||[])if(!Object.hasOwn(args,key))throw new Error('缺少必填参数：'+key+'。');
  for(const [key,value] of Object.entries(args)){
    const rule=schema.properties[key];
    if(rule.type==='string'&&(typeof value!=='string'||(rule.minLength&&!value.trim())||(rule.maxLength&&value.length>rule.maxLength)))throw new Error('参数内容无效：'+key+'。');
    if(rule.pattern&&!/^[0-9]{1,32}$/.test(value))throw new Error('请输入数字 ID。');
    if(rule.type==='integer'&&(!Number.isInteger(value)||value<rule.minimum||value>rule.maximum))throw new Error('返回数量应为 1 至 100。');
  }
}

async function perform(name,args,token,signal,request=fetch){
  validate(name,args);
  if(!token?.trim())throw new Error('请先在 WorkSwarm 连接器卡片中填写 Asana 个人访问令牌。');
  let endpoint,body;
  const params=new URLSearchParams();
  if(name==='asana_status')endpoint='users/me';
  else if(name==='asana_list_tasks'){
    endpoint='projects/'+args.container+'/tasks';
    params.set('limit',String(args.limit??25));
    params.set('opt_fields','gid,name,completed,permalink_url');
    if(args.cursor)params.set('offset',args.cursor);
  }else if(name==='asana_read_task'){
    endpoint='tasks/'+args.item;
    params.set('opt_fields','gid,name,notes,completed,permalink_url,projects.gid');
  }else{
    endpoint='tasks';
    body=JSON.stringify({data:{projects:[args.container],name:args.title}});
  }
  const url=new URL('https://app.asana.com/api/1.0/'+endpoint);
  url.search=params.toString();
  let response;
  try{response=await request(url,{method:body?'POST':'GET',redirect:'error',signal,
    headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},...(body?{body}:{})});}
  catch{throw new Error('Asana 请求未完成；请检查网络。写入结果不确定时，请先按唯一标题回读，勿直接重试。');}
  if(!response.ok){
    const messages={400:'Asana 拒绝了请求参数。',401:'Asana 授权已失效，请在卡片中重新配置有效令牌。',403:'当前账号没有访问或写入目标的权限。',404:'目标任务或项目不存在，或当前账号不可访问。',429:'Asana 请求过于频繁，请稍后重试。'};
    throw new Error(messages[response.status]||'Asana 服务暂时无法完成请求，请稍后核对结果。');
  }
  const chunks=[];let total=0;
  try{
    if(response.body)for await(const part of response.body){total+=part.byteLength;if(total>2*1024*1024)throw new Error('返回内容过大，请缩小查询范围。');chunks.push(Buffer.from(part));}
  }catch(exc){throw new Error(exc.message==='返回内容过大，请缩小查询范围。'?exc.message:'Asana 响应传输未完成；写入结果不确定时先回读，勿直接重试。');}
  let value;
  try{value=JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{throw new Error('Asana 返回了无法读取的响应。');}
  if(!value||typeof value!=='object'||!Object.hasOwn(value,'data'))throw new Error('Asana 响应缺少预期的数据。');
  return name==='asana_status'?{connected:!!value.data?.gid}:value;
}

function start(){
  const active=new Map();
  const write=m=>process.stdout.write(JSON.stringify({jsonrpc:'2.0',...m})+'\n');
  const error=(id,code,message)=>write({id,error:{code,message}});
  const input=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
  input.on('close',()=>{for(const controller of active.values())controller.abort();});
  input.on('line',async line=>{
    if(Buffer.byteLength(line)>1024*1024)return error(null,-32600,'MCP 消息过大。');
    let msg;try{msg=JSON.parse(line);}catch{return error(null,-32700,'无法解析 MCP JSON 消息。');}
    if(!msg||typeof msg!=='object'||Array.isArray(msg)||msg.jsonrpc!=='2.0')return error(null,-32600,'无效的 MCP 请求。');
    const {id,method,params}=msg;
    if(method==='notifications/cancelled'){active.get(params?.requestId)?.abort();return;}
    if(id===undefined)return;
    if(typeof id!=='number'&&typeof id!=='string')return error(null,-32600,'无效的请求 ID。');
    if(method==='initialize')return write({id,result:{protocolVersion:['2025-11-25','2025-06-18','2024-11-05'].includes(params?.protocolVersion)?params.protocolVersion:'2025-11-25',capabilities:{tools:{}},serverInfo:{name:'asana-standard-mcp',version:VERSION},instructions:'默认使用简体中文。仅查询指定项目任务、读取任务和创建新任务；写入结果不确定时先回读，不盲目重试。'}});
    if(method==='ping')return write({id,result:{}});
    if(method==='tools/list')return write({id,result:{tools:TOOLS}});
    if(method!=='tools/call')return error(id,-32601,'本连接器仅提供声明的 Asana 工具。');
    if(active.has(id))return error(id,-32600,'请求 ID 重复。');
    const controller=new AbortController();active.set(id,controller);
    try{
      const value=await perform(params?.name,params?.arguments??{},process.env.ASANA_PERSONAL_TOKEN,
        AbortSignal.any([controller.signal,AbortSignal.timeout(30000)]));
      write({id,result:{content:[{type:'text',text:JSON.stringify(value)}]}});
    }catch(exc){write({id,result:{isError:true,content:[{type:'text',text:exc instanceof Error?exc.message:'Asana 请求失败。'}]}});}
    finally{active.delete(id);}
  });
}

module.exports={TOOLS,validate,perform,VERSION};
if(require.main===module)start();
