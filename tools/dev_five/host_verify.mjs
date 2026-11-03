/* Supported WorkSwarm package RPCs only. Does not inject tools or patch host code. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const repo=path.resolve(fileURLToPath(new URL('../..',import.meta.url)));
const defs=JSON.parse(fs.readFileSync(path.join(repo,'tools/dev_five_config.json')));
const own=new Set(defs.map(d=>d.slug));
export function rpc(method,params={}){
 return new Promise((resolve,reject)=>{
  const ws=new WebSocket('ws://127.0.0.1:5173/ws?user_id=dev-five-verification'),id=crypto.randomUUID();
  const timer=setTimeout(()=>{ws.close();reject(Error('Host RPC timeout: '+method));},180000);
  ws.onopen=()=>ws.send(JSON.stringify({type:'req',id,method,params}));
  ws.onerror=()=>{clearTimeout(timer);reject(Error('Host WebSocket failed'));};
  ws.onmessage=e=>{try{const d=JSON.parse(e.data);if(d.id!==id)return;clearTimeout(timer);ws.close();d.ok?resolve(d.payload):reject(Error(JSON.stringify(d.error||d)));}catch(err){clearTimeout(timer);ws.close();reject(err);}};
 });
}
const digest=x=>crypto.createHash('sha256').update(Buffer.isBuffer(x)||typeof x==='string'?x:JSON.stringify(x)).digest('hex');
const output=path.join(repo,'.research/dev-five/host-install.json');
const report={at:new Date().toISOString(),scope:'Supported running WorkSwarm plugin_packages import/install/show/list. Actual chat-worker invocation and GUI tests are verified separately.',frontend:'http://127.0.0.1:5173',records:[]};
const before=await rpc('config.get'),beforePlugins=(await rpc('plugin_packages.list',{filter:'mine'})).packages;
report.configBeforeSha256=digest(before);
report.otherCatalogBefore=beforePlugins.filter(p=>!own.has(p.id)).map(p=>({id:p.id,version:p.version,installed:p.installed}));
for(const d of defs){
 const native=path.join(repo,'plugins',d.slug,'test-packages',d.slug+'-'+d.asset_version+'-workswarm.zip');
 const previous=beforePlugins.find(p=>p.id===d.slug);
 const prior=previous?await rpc('plugin_packages.show',{id:d.slug}):null;
 const currentVersion=prior?(prior.package||prior).version:null;
 if(previous&&currentVersion!==d.asset_version){
  if(!['1.0.0','1.0.1','1.0.2','1.0.3'].includes((prior.package||prior).version))throw Error('Refuse to replace an unexpected installed version: '+d.slug);
  await rpc('plugin_packages.uninstall',{id:d.slug});
 }
 if(!previous||currentVersion!==d.asset_version){
  const imported=await rpc('plugin_packages.import_local',{path:native});
  if(imported.id!==d.slug)throw Error('Imported identity mismatch: '+d.slug);
  await rpc('plugin_packages.install',{id:d.slug});
 }
 const detail=await rpc('plugin_packages.show',{id:d.slug}),card=detail.package||detail;
 const record={id:d.slug,version:card.version,installed:card.installed,nativeSha256:digest(fs.readFileSync(native)),detailKeys:Object.keys(detail),cardKeys:Object.keys(card),displayName:card.displayName};
 if(!card.installed||card.version!==d.asset_version)throw Error('Installation did not complete '+JSON.stringify(record));
 report.records.push(record);console.log(JSON.stringify(record));
}
report.configAfterSha256=digest(await rpc('config.get'));report.configUnchanged=report.configAfterSha256===report.configBeforeSha256;
report.otherCatalogAfter=(await rpc('plugin_packages.list',{filter:'mine'})).packages.filter(p=>!own.has(p.id)).map(p=>({id:p.id,version:p.version,installed:p.installed}));
report.otherCatalogUnchanged=JSON.stringify(report.otherCatalogAfter)===JSON.stringify(report.otherCatalogBefore);
fs.writeFileSync(output,JSON.stringify(report,null,2));
if(!report.configUnchanged||!report.otherCatalogUnchanged)throw Error('Concurrent or unexpected host state change; inspect report before proceeding');
console.log(JSON.stringify({hostPackageInstallation:true,count:report.records.length,configUnchanged:report.configUnchanged,otherCatalogUnchanged:report.otherCatalogUnchanged}));
