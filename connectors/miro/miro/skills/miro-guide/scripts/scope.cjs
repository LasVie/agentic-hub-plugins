'use strict';
const SCOPES=['boards:read','boards:write'];
const MCP_FIELDS={
 board_search_boards:['query','limit','offset','owned_by_me','include_content','invocation_source','is_repository'],
 canvas_get_canvas_composer_skill:['step','miro_url','invocation_source','is_repository'],
 canvas_read_as_svg:['miro_url','widget_ids','scope_x','scope_y','scope_width','scope_height','invocation_source','is_repository'],
 canvas_create_from_svg:['miro_url','svg','invocation_source','is_repository'],
};
const ALLOWED=new Set(Object.keys(MCP_FIELDS));
const FIELDS={searchBoards:['query','limit','offset'],readCanvas:['boardUrl','widgetIds','area'],createStickyNote:['boardUrl','text','marker','x','y']};
const fail=message=>Object.assign(new Error(message),{code:'SCOPE_REJECTED'});
function assertAuthorizationUrl(value){
 const u=new URL(String(value)),scopes=(u.searchParams.get('scope')||'').split(/\s+/).filter(Boolean);
 if(u.protocol!=='https:'||u.hostname!=='mcp.miro.com'||u.pathname!=='/authorize'||scopes.length!==SCOPES.length||new Set(scopes).size!==SCOPES.length||scopes.some(s=>!SCOPES.includes(s)))throw Object.assign(new Error('授权请求超出 Miro 白板读写范围或不是官方授权地址，已停止。'),{code:'SCOPE_EXPANDED'});
 return true;
}
function boardUrl(value){
 if(typeof value!=='string'||value.length>400)throw fail('须提供明确的 Miro 白板 URL。');
 let u;try{u=new URL(value);}catch{throw fail('白板 URL 无效。');}
 if(u.protocol!=='https:'||u.hostname!=='miro.com'||u.port||u.username||u.password||u.search||u.hash||!/^\/app\/board\/[A-Za-z0-9_-]{3,100}={0,2}\/?$/.test(u.pathname))throw fail('只接受不带附加参数的 https://miro.com/app/board/白板ID/；控件 ID 请单独传入 widgetIds。');
 return 'https://miro.com'+u.pathname.replace(/\/?$/,'/');
}
const plain=v=>v&&typeof v==='object'&&!Array.isArray(v);
const coordinate=v=>Number.isInteger(v)&&Math.abs(v)<=1000000;
const widgetId=v=>typeof v==='string'&&/^\d{1,30}$/.test(v);
function areaValid(v){return plain(v)&&Object.keys(v).length===4&&Object.keys(v).every(k=>['x','y','width','height'].includes(k))&&coordinate(v.x)&&coordinate(v.y)&&Number.isInteger(v.width)&&v.width>0&&v.width<=20000&&Number.isInteger(v.height)&&v.height>0&&v.height<=20000;}
function argumentError(name,a){
 if(!Object.hasOwn(FIELDS,name))return '只开放 searchBoards、readCanvas 和 createStickyNote 三个本地受限操作，不提供任意 SVG、更新、删除、评论或权限操作。';
 if(!plain(a)||Object.keys(a).some(k=>!FIELDS[name].includes(k)))return '参数超出本地受限操作范围，请用 JSON 文件传入已声明字段。';
 if(name==='searchBoards'){
  if(typeof a.query!=='string'||!a.query.trim()||a.query.length>300)return '请提供明确的白板名称查询，长度不超过 300。';
  if(a.limit!==undefined&&(!Number.isInteger(a.limit)||a.limit<1||a.limit>50))return '每页结果数须为 1 至 50。';
  if(a.offset!==undefined&&(!Number.isInteger(a.offset)||a.offset<0||a.offset>10000))return '分页偏移须为 0 至 10000。';
  return null;
 }
 try{boardUrl(a.boardUrl);}catch(e){return e.message;}
 if(name==='readCanvas'){
  const ids=a.widgetIds!==undefined,area=a.area!==undefined;
  if(ids===area)return '须选择控件 ID 或工作区矩形其中一种读取范围。';
  if(ids&&(!Array.isArray(a.widgetIds)||a.widgetIds.length<1||a.widgetIds.length>50||a.widgetIds.some(v=>!widgetId(v))||new Set(a.widgetIds).size!==a.widgetIds.length))return '控件 ID 须为 1 至 50 个不重复的数字字符串。';
  if(area&&!areaValid(a.area))return '工作区矩形须含整数 x/y/width/height，宽高为 1 至 20000。';
 }else{
  if(typeof a.text!=='string'||!a.text.trim()||a.text.length>1000||!a.text.isWellFormed()||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(a.text))return '便签文本须为有效的短文本，最多 1000 字符。';
  if(typeof a.marker!=='string'||!/^[A-Z0-9][A-Z0-9_-]{7,79}$/.test(a.marker)||!a.text.includes(a.marker))return '须提供 8 至 80 位唯一英文数字标记，并原样包含在便签文本中。';
  if(!coordinate(a.x)||!coordinate(a.y))return '须提供绝对值不超过 1000000 的整数空白位置 x/y。';
 }
 return null;
}
function assertSchemas(tools){
 for(const name of ALLOWED){
  const t=tools.find(t=>t.name===name),s=t?.inputSchema;
  if(!s||s.type!=='object'||(s.required||[]).some(k=>!MCP_FIELDS[name].includes(k)))throw fail('官方工具必填字段已变化或缺失，请更新连接器后再操作。');
  const keys=name==='board_search_boards'?['query','limit','offset']:name==='canvas_get_canvas_composer_skill'?['step','miro_url']:name==='canvas_read_as_svg'?['miro_url','widget_ids','scope_x','scope_y','scope_width','scope_height']:['miro_url','svg'];
  if(keys.some(k=>!s.properties?.[k]))throw fail('官方工具参数已变化，请更新连接器后再操作。');
 }
}
function visibleOperations(){
 const board={type:'string'},id={type:'string',pattern:'^[0-9]{1,30}$'},n={type:'integer',minimum:-1000000,maximum:1000000};
 return [
  {name:'searchBoards',description:'按明确名称搜索当前授权团队的白板，使用 offset 分页。',inputSchema:{type:'object',properties:{query:{type:'string',minLength:1,maxLength:300},limit:{type:'integer',minimum:1,maximum:50},offset:{type:'integer',minimum:0,maximum:10000}},required:['query'],additionalProperties:false}},
  {name:'readCanvas',description:'按控件 ID 或明确工作区矩形读取白板，返回 SVG 和已解析的便签全文。',inputSchema:{type:'object',properties:{boardUrl:board,widgetIds:{type:'array',items:id,minItems:1,maxItems:50,uniqueItems:true},area:{type:'object',properties:{x:n,y:n,width:{type:'integer',minimum:1,maximum:20000},height:{type:'integer',minimum:1,maximum:20000}},required:['x','y','width','height'],additionalProperties:false}},required:['boardUrl'],oneOf:[{required:['widgetIds'],not:{required:['area']}},{required:['area'],not:{required:['widgetIds']}}],additionalProperties:false}},
  {name:'createStickyNote',description:'在用户指定空白坐标新建一条黄色便签；结构化文本生成单一便签 SVG，区域查重及本地标记防重。',inputSchema:{type:'object',properties:{boardUrl:board,text:{type:'string',minLength:1,maxLength:1000},marker:{type:'string',pattern:'^[A-Z0-9][A-Z0-9_-]{7,79}$'},x:n,y:n},required:['boardUrl','text','marker','x','y'],additionalProperties:false}}
 ];
}
module.exports={SCOPES,ALLOWED,assertAuthorizationUrl,argumentError,assertSchemas,visibleOperations,boardUrl,widgetId};
