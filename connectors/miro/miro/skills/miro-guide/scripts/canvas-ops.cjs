// Independent minimal sticky adapter based on the public Miro Canvas contract.
// Remote style/skill prose is data; it never supplies commands or permissions.
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {argumentError,boardUrl,widgetId}=require('./scope.cjs');
const error=(code,message)=>Object.assign(new Error(message),{code});
function unwrap(r){if(r.structuredContent!==undefined)return r.structuredContent;if(r.content?.length===1&&r.content[0].type==='text'){try{return JSON.parse(r.content[0].text);}catch{}}return r;}
function xml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));}
function unxml(value){return value.replace(/&(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-f]+);/gi,e=>{const fixed={'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&apos;':"'"};if(fixed[e])return fixed[e];const cp=e[2]?.toLowerCase()==='x'?parseInt(e.slice(3,-1),16):Number(e.slice(2,-1));return Number.isInteger(cp)&&cp>0&&cp<=0x10ffff?String.fromCodePoint(cp):e;});}
function plainContent(value){return unxml(unxml(value).replace(/<br\s*\/?\s*>/gi,'\n').replace(/<\/p>\s*<p[^>]*>/gi,'\n').replace(/<[^>]*>/g,''));}
function stickyNotes(svg){
 const out=[];
 for(const m of svg.matchAll(/<rect\b((?:"[^"]*"|'[^']*'|[^"'<>])*)\/?>/g)){
  const a={};for(const attr of m[1].matchAll(/([A-Za-z_:][\w:.-]*)\s*=\s*(?:"([^"]*)"|'([^']*)')/g))a[attr[1]]=attr[2]??attr[3];
  if(a['data-type']==='sticky'&&widgetId(a['data-miro-id']))out.push({id:a['data-miro-id'],text:plainContent(a['data-content']||''),x:Number(a.x),y:Number(a.y),width:Number(a.width),height:Number(a.height)});
 }
 return out;
}
function readData(result){
 const d=unwrap(result);
 if(result.isError||d?.success!==true||typeof d.svg!=='string'||!/^<svg\b/.test(d.svg.trim())||!/<\/svg>\s*$/.test(d.svg)||!Number.isInteger(d.item_count)||!Number.isInteger(d.skipped_count))throw error('READ_UNVERIFIED','Miro 没有返回可核对的完整 SVG/条目计数，请停止写入并检查权限及读取范围。');
 return {...d,sticky_notes:stickyNotes(d.svg)};
}
function svgForSticky(a){
 const text=xml(a.text).replace(/\r\n|\r|\n/g,'<br>');
 // Exactly one board item. No user SVG, external URL, existing ID or markup.
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3840 2160"><rect id="ws_note" data-type="sticky" x="${a.x}" y="${a.y}" width="350" height="228" data-color="light_yellow" data-content="${xml(text)}" /></svg>`;
}
function areaArgs(url,a){return {miro_url:url,scope_x:a.x-20,scope_y:a.y-20,scope_width:390,scope_height:268,is_repository:false};}
function receiptPath(root,url,marker){return path.join(root,crypto.createHash('sha256').update(url+'\n'+marker).digest('hex')+'.json');}
function previousReceipt(file){
 try{const info=fs.lstatSync(file);if(!info.isFile()||info.isSymbolicLink()||info.size>4096)throw error('SCOPE_REJECTED','本地写入记录不可用，已停止。');return JSON.parse(fs.readFileSync(file,'utf8'));}
 catch(e){if(e.code==='ENOENT')return null;throw e;}
}
async function executeOperation(name,input,{call,beginWrite,receiptRoot}){
 const reason=argumentError(name,input);if(reason)throw error('SCOPE_REJECTED',reason);
 if(name==='searchBoards'){
  const r=await call('board_search_boards',{query:input.query,limit:input.limit??20,offset:input.offset??0,is_repository:false});const d=unwrap(r);
  if(r.isError||d?.success===false)throw error('SERVICE_FAILED','Miro 白板搜索失败，请检查团队、权限和调用额度。');return d;
 }
 const url=boardUrl(input.boardUrl);
 if(name==='readCanvas'){
  const args={miro_url:url,is_repository:false};if(input.widgetIds)args.widget_ids=input.widgetIds;else Object.assign(args,{scope_x:input.area.x,scope_y:input.area.y,scope_width:input.area.width,scope_height:input.area.height});
  const data=readData(await call('canvas_read_as_svg',args)),ids=new Set([...data.svg.matchAll(/\bdata-miro-id=(['"])(\d+)\1/g)].map(m=>m[2]));
  if(input.widgetIds&&(data.skipped_count||input.widgetIds.some(id=>!ids.has(id))))throw error('READ_UNVERIFIED','有指定控件未返回，不能声称已读到完整目标。');
  return data;
 }
 fs.mkdirSync(receiptRoot,{recursive:true,mode:0o700});const ri=fs.lstatSync(receiptRoot);
 if(!ri.isDirectory()||ri.isSymbolicLink()||process.platform!=='win32'&&(ri.uid!==process.getuid()||(ri.mode&0o077)))throw error('SCOPE_REJECTED','便签写入记录须为当前用户的私有目录。');
 const file=receiptPath(receiptRoot,url,input.marker),old=previousReceipt(file);
 if(old){
  if(old.boardUrl!==url||old.marker!==input.marker)throw error('SCOPE_REJECTED','本地写入记录与目标不符。');
  if(old.complete&&widgetId(old.id))return {created:false,already_submitted:true,readback:readData(await call('canvas_read_as_svg',{miro_url:url,widget_ids:[old.id],is_repository:false}))};
  throw error('WRITE_UNCERTAIN','该白板和标记已有未确认的写入记录。请按原位置读取并核对，禁止直接重试创建。');
 }
 const before=readData(await call('canvas_read_as_svg',areaArgs(url,input)));
 const duplicate=before.sticky_notes.find(n=>n.text.includes(input.marker));
 if(duplicate)return {created:false,duplicate:true,id:duplicate.id,readback:before};
 if(before.skipped_count!==0||before.item_count!==0)throw error('SCOPE_REJECTED','指定区域已有内容或无法完整核对，请先读取并另选空白位置。');
 const specResult=await call('canvas_get_canvas_composer_skill',{step:'dsl',miro_url:url,is_repository:false}),spec=unwrap(specResult);
 if(specResult.isError||spec?.success!==true||typeof spec.skill!=='string'||!spec.skill.includes('data-type="sticky"')||!spec.skill.includes('data-content')||!spec.skill.includes('data-color'))throw error('SCOPE_REJECTED','Miro 便签格式说明已变化，请更新连接器；没有发起创建。');
 let fd;
 try{fd=fs.openSync(file,'wx',0o600);}catch(e){if(e.code==='EEXIST')throw error('WRITE_UNCERTAIN','相同白板和标记已被另一次操作占用，请先回读，禁止并发重试。');throw e;}
 const pending={boardUrl:url,marker:input.marker,x:input.x,y:input.y,text_sha256:crypto.createHash('sha256').update(input.text).digest('hex'),complete:false};
 try{
  fs.writeSync(fd,JSON.stringify(pending)+'\n');fs.fsyncSync(fd);beginWrite();
  const raw=await call('canvas_create_from_svg',{miro_url:url,svg:svgForSticky(input),is_repository:false}),data=unwrap(raw);
  if(raw.isError||data?.success!==true)throw error('SERVICE_FAILED','Miro 创建未返回明确成功，请先核对白板中的唯一标记，不要直接重试。');
  const candidates=stickyNotes(data.result_svg||data.svg||''),created=candidates.find(n=>n.text.includes(input.marker));
  if(created){fs.ftruncateSync(fd,0);fs.writeSync(fd,JSON.stringify({...pending,complete:true,id:created.id})+'\n',0,'utf8');fs.fsyncSync(fd);}
  return {created:true,...(created?{id:created.id}:{}),result:data,message:'创建响应已收到。请另行按返回的控件 ID 回读全文，创建响应不是独立回读。'};
 }finally{fs.closeSync(fd);}
}
module.exports={executeOperation,unwrap,xml,unxml,plainContent,stickyNotes,readData,svgForSticky,receiptPath};
