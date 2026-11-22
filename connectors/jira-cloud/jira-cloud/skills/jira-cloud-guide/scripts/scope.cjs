'use strict';
const SCOPES = ['read:jira:agent-interface','search:jira:agent-interface','write:jira:agent-interface','read:me','read:account','offline_access'];
const DESCRIPTIONS = {
  getAccessibleAtlassianResources:'列出当前 OAuth 已授权的 Atlassian 站点，用于核对 Jira 目标站点。',
  listJiraProjects:'读取当前已授权站点的 Jira 项目清单。',
  listJiraProjectIssueTypesMetadata:'读取指定 Jira 项目的工单类型，用于选择新建类型。',
  getJiraIssueTypeMetaWithFields:'读取指定 Jira 项目与工单类型的必填字段要求。',
  searchJiraIssuesUsingJql:'在已授权 Jira 站点按 JQL 查询工单，支持分页。',
  getJiraIssue:'按键或标识读取一条已授权的 Jira 工单。',
  createJiraIssue:'在用户指定项目创建一条新工单；不更新已有工单，不分配人员。',
};
const FIELDS = {
  getAccessibleAtlassianResources:[],
  listJiraProjects:['cloudId','maxResults','startAt','searchString'],
  listJiraProjectIssueTypesMetadata:['cloudId','projectIdOrKey','projectKey'],
  getJiraIssueTypeMetaWithFields:['cloudId','projectIdOrKey','projectKey','issueTypeId','startAt','maxResults'],
  searchJiraIssuesUsingJql:['cloudId','jql','fields','maxResults','nextPageToken'],
  getJiraIssue:['cloudId','issueIdOrKey','fields'],
  createJiraIssue:['cloudId','projectKey','issueType','summary','description'],
};
const ALLOWED=new Set(Object.keys(FIELDS));
const READ_FIELDS=new Set(['summary','description','status','issuetype','project','created','updated']);
function argumentError(name,a) {
  if(!ALLOWED.has(name))return '本连接器只提供 Jira 查询、读取、新建及必要的项目元数据，不提供此工具。';
  if(!a || typeof a!=='object' || Array.isArray(a))return '工具参数须为 JSON 对象。';
  if(Object.keys(a).some(k=>!FIELDS[name].includes(k)))return '参数超出本连接器范围；不能修改、删除、评论、分配人员或调用其他产品。';
  if(name!=='getAccessibleAtlassianResources' && (typeof a.cloudId!=='string' || !a.cloudId.trim() || a.cloudId.length>300))return '请先读取授权站点清单，再明确提供 cloudId。';
  for(const k of ['projectKey','projectIdOrKey'])if(a[k]!==undefined && (typeof a[k]!=='string' || !/^[A-Za-z0-9][A-Za-z0-9_]{0,40}$/.test(a[k])))return '项目键或项目标识不符合要求。';
  if(name==='getJiraIssue' && (typeof a.issueIdOrKey!=='string' || !/^(?:[A-Za-z][A-Za-z0-9_]{0,40}-[1-9][0-9]*|[1-9][0-9]*)$/.test(a.issueIdOrKey)))return '请输入有效工单键或标识，例如 KAN-1。';
  if(name==='searchJiraIssuesUsingJql' && (typeof a.jql!=='string' || !a.jql.trim() || a.jql.length>4000))return '查询须提供不超过 4000 字符的 JQL。';
  if(a.fields!==undefined && (!Array.isArray(a.fields) || a.fields.some(f=>!READ_FIELDS.has(f))))return '读取字段只能包含标题、描述、状态、工单类型、项目和创建/更新时间。';
  if(a.maxResults!==undefined && (!Number.isInteger(a.maxResults) || a.maxResults<1 || a.maxResults>100))return '每页结果数须为 1 至 100。';
  if(a.startAt!==undefined && (!Number.isInteger(a.startAt) || a.startAt<0 || a.startAt>100000))return '分页起点不符合要求。';
  if(a.nextPageToken!==undefined && (typeof a.nextPageToken!=='string' || a.nextPageToken.length>4096))return '分页标识不符合要求。';
  if(name==='createJiraIssue') {
    if(!['projectKey','issueType','summary'].every(k=>typeof a[k]==='string' && a[k].trim()))return '新建工单须明确项目键、工单类型名称和标题。';
    if(a.summary.length>255 || a.issueType.length>100 || a.description!==undefined && (typeof a.description!=='string' || a.description.length>8000))return '标题、类型名称或描述超出允许范围。';
  }
  return null;
}
function chineseSchema(s) {
  if(Array.isArray(s))return s.map(chineseSchema);
  if(!s || typeof s!=='object')return s;
  const out={};for(const[k,v]of Object.entries(s)) {
    if(['properties','$defs','definitions'].includes(k))out[k]=Object.fromEntries(Object.entries(v).map(([n,i])=>[n,chineseSchema(i)]));
    else if(!['description','title','examples'].includes(k))out[k]=chineseSchema(v);
  }return out;
}
function visibleTool(t) {
  const schema=chineseSchema(t.inputSchema||{type:'object'});
  if((schema.required||[]).some(k=>!FIELDS[t.name].includes(k)))throw Object.assign(new Error('官方工具必填字段已变化，超出本包范围，请更新连接器。'),{code:'SCOPE_REJECTED'});
  schema.properties=Object.fromEntries(Object.entries(schema.properties||{}).filter(([k])=>FIELDS[t.name].includes(k)));
  schema.additionalProperties=false;
  schema.required=(schema.required||[]).filter(k=>FIELDS[t.name].includes(k));
  return {name:t.name,description:DESCRIPTIONS[t.name],inputSchema:schema};
}
function assertAuthorizationUrl(value) {
  const u=new URL(String(value)), scopes=(u.searchParams.get('scope')||'').split(/\s+/).filter(Boolean);
  if(u.protocol!=='https:' || u.hostname!=='auth.atlassian.com' || scopes.length!==SCOPES.length || new Set(scopes).size!==SCOPES.length || scopes.some(s=>!SCOPES.includes(s)))throw Object.assign(new Error('授权请求超出既定 Jira 权限或不是 Atlassian 官方地址，已停止。'),{code:'SCOPE_EXPANDED'});
  return true;
}
function resourcesFrom(value) {
  // v2 wraps tool data and uses cloudId; the discovery REST API uses id.
  const values=Array.isArray(value)?value:value?.data?.resources||value?.resources||value?.data||[];
  if(!Array.isArray(values))return [];
  return values.filter(v=>v && typeof (v.cloudId||v.id)==='string' && typeof v.url==='string' && /^https:\/\/[a-zA-Z0-9-]+\.atlassian\.net\/?$/.test(v.url)
      && (v.products===undefined || Array.isArray(v.products) && v.products.some(p=>p?.id==='jira')))
    .map(v=>({id:v.cloudId||v.id,url:v.url.replace(/\/$/,''),name:typeof v.name==='string'?v.name:''}));
}
module.exports={SCOPES,ALLOWED,argumentError,visibleTool,assertAuthorizationUrl,resourcesFrom};
