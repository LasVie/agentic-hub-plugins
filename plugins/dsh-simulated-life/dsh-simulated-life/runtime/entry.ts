// WorkSwarm 本地模拟生活适配；MIT 上游 loader/deduplication/formatter 见 vendor/。
import { readFile, readdir, lstat } from 'node:fs/promises';
import { join } from 'node:path';
import {loadRecentLifeEvents} from '../vendor/loader.js';
import {evaluateDeduplication} from '../vendor/deduplication.js';
import {formatLifeContext} from '../vendor/formatter.js';
let text='';for await(const c of process.stdin)text+=c;
try{
 const q=JSON.parse(text);const life=join(q.workspace_dir,'.life');
 try{
  if((await lstat(life)).isSymbolicLink())throw Error('生活事件目录不能是符号链接。');
  const entries=await readdir(life);if(entries.length>366)throw Error('事件目录超过366个，请先归档旧文件。');
  for(const name of entries){
   const dir=join(life,name);const d=await lstat(dir);if(d.isSymbolicLink())throw Error('生活事件路径不能经过符号链接。');
   if(!d.isDirectory())continue;
   try{const f=await lstat(join(dir,'events.json'));if(f.isSymbolicLink()||!f.isFile()||f.size>1024*1024)throw Error('事件文件不是受限大小的普通文件。');}catch(e:any){if(e.code!=='ENOENT')throw e;}
  }
 }catch(e:any){if(e.code!=='ENOENT')throw e;}
 const loaded=await loadRecentLifeEvents(q.workspace_dir,q.now_ms??Date.now(),24);
 if(loaded.events.length>2000)throw Error('24小时内事件超过2000条，请缩小事件集合。');
 const decision=evaluateDeduplication(loaded.events,q.state,q.force_full===true);
 const changed=decision.isFirstInjection||q.force_full?loaded.events:[...decision.newEvents,...decision.updatedEvents].sort((a,b)=>a.epochMs-b.epochMs);
 const context=formatLifeContext(loaded.events,loaded.worldSummary,false);
 const notice=decision.shouldInject?formatLifeContext(changed,loaded.worldSummary,!decision.isFirstInjection):'';
 process.stdout.write(JSON.stringify({ok:true,message:loaded.events.length?'已读取近24小时虚构生活事件。':'近24小时没有可用的虚构生活事件。',event_count:loaded.events.length,new_count:decision.newEvents.length,updated_count:decision.updatedEvents.length,should_inject:decision.shouldInject,notice,context,next_state:decision.nextState,events:loaded.events.map(x=>x.event)}));
}catch(e:any){const m=String(e.message);process.stdout.write(JSON.stringify({ok:false,message:/[\u4e00-\u9fff]/.test(m)?m:'生活事件文件格式不正确，操作未完成。'}));}
