'use strict';
const SCOPES=['read:confluence:agent-interface','search:confluence:agent-interface','write:confluence:agent-interface','read:me','read:account','offline_access'];
const DESCRIPTIONS={
 getAccessibleAtlassianResources:'核对本次 OAuth 可访问的 Confluence 站点。',
 listConfluenceSpaces:'列出授权站点的 Confluence 空间。',
 getConfluenceSpace:'读取明确空间的标识和基本信息，用于核对测试目标。',
 listConfluenceContent:'列出指定空间的普通页面。',
 getConfluenceContent:'读取指定普通页面的标题、正文和空间信息。',
 searchConfluence:'用 CQL 搜索普通页面，写入前按空间和唯一标题查重。',
 createConfluenceContent:'在用户指定空间及父页下新建一个普通页面，不更新已有内容。',
};
const FIELDS={
 getAccessibleAtlassianResources:[],
 listConfluenceSpaces:['cloudId','limit','cursor'],
 getConfluenceSpace:['cloudId','spaceIdOrKey'],
 listConfluenceContent:['cloudId','spaceId','type','limit','cursor'],
 getConfluenceContent:['cloudId','content_id','detail','content_format'],
 searchConfluence:['cloudId','cql','limit','cursor'],
 createConfluenceContent:['cloudId','parent','contentType','title','body'],
};
const ALLOWED=new Set(Object.keys(FIELDS));
function argumentError(name,a){
 if(!ALLOWED.has(name))return '本连接器只开放 Confluence 普通页面搜索、读取、新建及必要空间定位，不提供此工具。';
 if(!a||typeof a!=='object'||Array.isArray(a))return '参数须为 JSON 对象。';
 if(Object.keys(a).some(k=>!FIELDS[name].includes(k)))return '参数超出本包范围，不能更新或删除已有页面、评论、附件、分享或权限。';
 if(name!=='getAccessibleAtlassianResources'&&(typeof a.cloudId!=='string'||!a.cloudId.trim()||a.cloudId.length>300))return '请先核对授权站点并提供 cloudId。';
 for(const k of ['content_id','spaceId'])if(a[k]!==undefined&&!numericId(a[k]))return '页面或空间标识须为明确的数字字符串。';
 if(a.spaceIdOrKey!==undefined&&(typeof a.spaceIdOrKey!=='string'||!/^[A-Za-z0-9~_:.-]{1,255}$/.test(a.spaceIdOrKey)))return '空间标识或空间键不符合要求。';
 if(a.type!==undefined&&a.type!=='page')return '本包只处理普通页面。';
 if(a.contentType!==undefined&&a.contentType!=='page')return '本包只新建普通页面。';
 if(a.content_format!==undefined&&a.content_format!=='markdown')return '本包只读取 Markdown 正文。';
 if(a.detail!==undefined&&a.detail!=='full')return '页面读取必须取得全文，不能把摘要作为回读。';
 if(a.limit!==undefined&&(!Number.isInteger(a.limit)||a.limit<1||a.limit>100))return '每页结果数须为 1 至 100。';
 if(a.cursor!==undefined&&(typeof a.cursor!=='string'||a.cursor.length>4096))return '分页标识不符合要求。';
 if(name==='searchConfluence'&&(typeof a.cql!=='string'||!a.cql.trim()||a.cql.length>4000))return '须提供不超过 4000 字符的 CQL。';
 if(name==='getConfluenceContent'&&!a.content_id)return '须提供明确页面标识。';
 if(name==='getConfluenceSpace'&&!a.spaceIdOrKey)return '须提供明确空间标识或空间键。';
 if(name==='listConfluenceContent'&&!a.spaceId)return '须提供明确空间标识。';
 if(name==='createConfluenceContent'){
  if(!plain(a.parent)||Object.keys(a.parent).some(k=>!['spaceId','parentContentId'].includes(k))||!numericId(a.parent.spaceId)||!numericId(a.parent.parentContentId))return '新建目标只接受明确的数字空间 ID 和父页面 ID，不接受 URL 或其他内容目的地。';
  if(!plain(a.body)||Object.keys(a.body).some(k=>!['format','value'].includes(k))||a.body.format!=='markdown'||typeof a.body.value!=='string'||!a.body.value.trim())return '新建正文须为 format=markdown 及非空 value，不接受 HTML、SVG 或远程 URL。';
  if(typeof a.title!=='string'||!a.title.trim()||a.title.length>255||a.body.value.length>40000)return '标题或正文超出允许范围。';
 }
 return null;
}
function plain(v){return !!v&&typeof v==='object'&&!Array.isArray(v);}
function numericId(v){return typeof v==='string'&&/^\d{1,30}$/.test(v);}
function assertPage(value,{id,spaceId}={}){
 const page=value?.data||value;
 if(!page||page.type!=='page'||!numericId(String(page.id||''))||!numericId(String(page.spaceId||''))||(id&&String(page.id)!==id)||(spaceId&&String(page.spaceId)!==spaceId))throw Object.assign(new Error('目标不是可核对的普通页面，或页面与指定空间不匹配，已停止。'),{code:'SCOPE_REJECTED'});
 return page;
}
function pageCql(query){
 let quote=null,depth=0,order=-1;
 for(let i=0;i<query.length;i++){
  const c=query[i];
  if(quote){if(c==='\\'){i++;continue;}if(c===quote)quote=null;continue;}
  if(c==='"'||c==="'"){quote=c;continue;}
  if(c==='(')depth++;else if(c===')'){if(--depth<0)throw Object.assign(new Error('CQL 括号不匹配。'),{code:'SCOPE_REJECTED'});}
  else if(depth===0&&(i===0||/\s/.test(query[i-1]))&&/^order\s+by\b/i.test(query.slice(i))){order=i;break;}
 }
 if(quote||depth)throw Object.assign(new Error('CQL 引号或括号不匹配。'),{code:'SCOPE_REJECTED'});
 const predicate=(order<0?query:query.slice(0,order)).trim();
 if(!predicate)throw Object.assign(new Error('CQL 须包含查询条件。'),{code:'SCOPE_REJECTED'});
 return `type = page AND (${predicate})`+(order<0?'':' '+query.slice(order));
}
function prepareArguments(name,input){
 const reason=argumentError(name,input);if(reason)throw Object.assign(new Error(reason),{code:'SCOPE_REJECTED'});
 const a={...input};
 if(name==='searchConfluence')a.cql=pageCql(a.cql);
 if(name==='listConfluenceContent')a.type='page';
 if(name==='createConfluenceContent'){a.contentType='page';a.parent={...a.parent};a.body={...a.body};}
 if(name==='getConfluenceContent'){a.detail='full';a.content_format='markdown';}
 return a;
}
function cleanSchema(s){
 if(Array.isArray(s))return s.map(cleanSchema);if(!s||typeof s!=='object')return s;
 const out={};for(const[k,v]of Object.entries(s)){
  if(['properties','$defs','definitions'].includes(k))out[k]=Object.fromEntries(Object.entries(v).map(([n,i])=>[n,cleanSchema(i)]));
  else if(!['description','title','examples'].includes(k))out[k]=cleanSchema(v);
 }return out;
}
function visibleTool(t){
 const schema=cleanSchema(t.inputSchema||{type:'object'});
 if((schema.required||[]).some(k=>!FIELDS[t.name].includes(k)))throw Object.assign(new Error('官方工具必填字段已变化，超出本包范围，请更新连接器。'),{code:'SCOPE_REJECTED'});
 schema.properties=Object.fromEntries(Object.entries(schema.properties||{}).filter(([k])=>FIELDS[t.name].includes(k)));
 schema.additionalProperties=false;schema.required=(schema.required||[]).filter(k=>FIELDS[t.name].includes(k));
 if(schema.properties.type)schema.properties.type={type:'string',const:'page'};
 if(schema.properties.contentType)schema.properties.contentType={type:'string',const:'page'};
 if(schema.properties.detail)schema.properties.detail={type:'string',const:'full'};
 if(schema.properties.content_format)schema.properties.content_format={type:'string',const:'markdown'};
 if(t.name==='createConfluenceContent'){
  const id={type:'string',pattern:'^[0-9]{1,30}$'};
  schema.properties.parent={type:'object',properties:{spaceId:id,parentContentId:id},required:['spaceId','parentContentId'],additionalProperties:false};
  schema.properties.body={type:'object',properties:{format:{type:'string',const:'markdown'},value:{type:'string',minLength:1,maxLength:40000}},required:['format','value'],additionalProperties:false};
  schema.required=[...new Set([...schema.required,'body'])];
 }
 return {name:t.name,description:DESCRIPTIONS[t.name],inputSchema:schema};
}
function assertAuthorizationUrl(value){
 const u=new URL(String(value)),scopes=(u.searchParams.get('scope')||'').split(/\s+/).filter(Boolean);
 if(u.protocol!=='https:'||u.hostname!=='auth.atlassian.com'||scopes.length!==SCOPES.length||new Set(scopes).size!==SCOPES.length||scopes.some(s=>!SCOPES.includes(s)))throw Object.assign(new Error('授权请求超出 Confluence 既定范围或不是 Atlassian 官方地址，已停止。'),{code:'SCOPE_EXPANDED'});
 return true;
}
function resourcesFrom(value){
 const values=Array.isArray(value)?value:value?.data?.resources||value?.resources||value?.data||[];
 if(!Array.isArray(values))return [];
 return values.filter(v=>v&&typeof(v.cloudId||v.id)==='string'&&typeof v.url==='string'&&/^https:\/\/[a-zA-Z0-9-]+\.atlassian\.net\/?$/.test(v.url)&&(v.products===undefined||Array.isArray(v.products)&&v.products.some(p=>p?.id==='confluence')))
  .map(v=>({id:v.cloudId||v.id,url:v.url.replace(/\/$/,''),name:typeof v.name==='string'?v.name:''}));
}
module.exports={SCOPES,ALLOWED,argumentError,prepareArguments,pageCql,assertPage,visibleTool,assertAuthorizationUrl,resourcesFrom};
