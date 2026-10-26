'use strict';
// Chinese native browser adapter; no external libraries, providers or fetches.
const $ = id => document.getElementById(id);
const audio = $('audio');
let data, current = null, activeList = null, selected = new Set(), ready = false, savedAt = 0;
let restoring = false;
const say = (text, error = false) => { $('message').textContent = text; $('message').className = error ? 'error' : ''; };
async function api(path, body) {
  const response = await fetch('api/' + path, body === undefined ? {cache:'no-store'} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),keepalive:path==='resume'});
  const value = await response.json();
  if (!response.ok || !value.ok) throw new Error(value.message || '本地操作失败。');
  return value;
}
const fmt = n => { n=Number.isFinite(n)?Math.max(0,Math.floor(n)):0; return Math.floor(n/60)+':'+String(n%60).padStart(2,'0'); };
function shown() { return data.tracks.filter(t => (!activeList || activeList.includes(t.id)) && t.name.toLocaleLowerCase().includes($('search').value.toLocaleLowerCase())); }
function queueIds() { return activeList || data.tracks.map(t=>t.id); }
function render() {
  $('library-title').textContent = data.library;
  $('summary').textContent = `共 ${data.scan.count} 首 · 扫描 ${data.scan.entries} 个条目 · 跳过 ${data.scan.skipped} 个异常文件`+(data.scan.truncated?' · 已达扫描边界，列表可能不完整':'');
  const queue = $('queue'); queue.replaceChildren();
  const list = shown();
  if (!list.length) { const p=document.createElement('p');p.textContent='没有符合条件的曲目。支持格式取决于浏览器；请检查目录或搜索词。';queue.append(p); }
  for (const t of list) {
    const row=document.createElement('div');row.className='track'+(current===t.id?' active':'');
    const cb=document.createElement('input');cb.type='checkbox';cb.checked=selected.has(t.id);cb.setAttribute('aria-label','选择 '+t.name);
    cb.onchange=()=>{if(cb.checked)selected.add(t.id);else selected.delete(t.id);};
    const label=document.createElement('div');label.className='name';label.textContent=t.name;
    const meta=document.createElement('small');meta.textContent=(t.bytes/1024).toFixed(1)+' KiB · '+t.mime;label.append(meta);
    const button=document.createElement('button');button.textContent=current===t.id?'从头播放':'播放';button.onclick=()=>play(t.id,0,true);
    row.append(cb,label,button);queue.append(row);
  }
  const ps=$('playlists');ps.replaceChildren();
  for(const p of data.playlists){
    const row=document.createElement('div');row.className='playlist';const open=document.createElement('button');
    const missing=p.tracks.filter(id=>!data.tracks.some(t=>t.id===id)).length;
    open.textContent=p.name+' · '+p.tracks.length+' 首'+(missing?'（缺失 '+missing+'）':'');
    open.onclick=()=>{activeList=p.tracks;selected=new Set(p.tracks);$('playlist-name').value=p.name;render();say('已打开歌单：'+p.name+'。请点击曲目播放。');};
    const del=document.createElement('button');del.textContent='删除';del.setAttribute('aria-label','删除歌单 '+p.name);
    del.onclick=async()=>{if(!confirm('只删除歌单「'+p.name+'」的记录，保留全部音频？'))return;try{data=await api('remove-playlist',{name:p.name});activeList=null;render();say('歌单记录已删除，音频未改动。');}catch(e){say(e.message,true);}};
    row.append(open,del);ps.append(row);
  }
}
async function persist(show=false){
  if(!current||!ready||restoring)return;
  try{await api('resume',{track:current,seconds:Number.isFinite(audio.currentTime)?audio.currentTime:0,volume:audio.volume,mode:$('mode').value});savedAt=Date.now();if(show)say('进度已保存；再次打开后点击播放继续。');}catch(e){say('进度未确认保存：'+e.message,true);}
}
async function play(id, seconds=0, autoplay=true){
  const track=data.tracks.find(t=>t.id===id);
  if(!track){say('曲目已缺失，请重新扫描。',true);return;}
  await persist();restoring=true;ready=false;audio.pause();current=id;audio.src='audio/'+id;$('now').textContent=track.name;
  audio.onloadedmetadata=()=>{audio.currentTime=Math.min(seconds,Number.isFinite(audio.duration)?audio.duration:seconds);ready=true;restoring=false;if(autoplay)audio.play().then(()=>say('正在播放：'+track.name)).catch(()=>say('浏览器暂未允许播放，请点击播放器的播放按钮。',true));else say('已恢复曲目和位置，等待手动点击播放。');};
  audio.load();render();
}
function move(step){const ids=queueIds().filter(id=>data.tracks.some(t=>t.id===id));if(!ids.length)return;let i=ids.indexOf(current);let next=(i+step+ids.length)%ids.length;if($('mode').value==='shuffle'&&ids.length>1){do{next=Math.floor(Math.random()*ids.length);}while(next===i);}play(ids[next],0,true);}
$('toggle').onclick=()=>{if(!current){const first=shown()[0];if(first)play(first.id);return;}if(audio.paused)audio.play().catch(()=>say('无法开始播放，请检查浏览器或文件格式。',true));else audio.pause();};
$('previous').onclick=()=>move(-1);$('next').onclick=()=>move(1);
audio.onplay=()=>{$('toggle').textContent='暂停';};
audio.onpause=()=>{$('toggle').textContent='播放';persist();};
audio.onended=()=>{if($('mode').value==='repeat'){audio.currentTime=0;audio.play().catch(()=>say('继续播放被浏览器拒绝。',true));}else move(1);};
audio.onerror=()=>{ready=false;restoring=false;say('音频无法加载或解码；可能是不支持的编码、损坏/变化的文件或已关闭的服务。未确认播放成功，请换曲目或重新扫描。',true);$('toggle').textContent='播放';};
audio.ontimeupdate=()=>{$('position').textContent=fmt(audio.currentTime)+' / '+fmt(audio.duration);if(Date.now()-savedAt>10000)persist();};
audio.onvolumechange=()=>persist();$('mode').onchange=()=>persist();$('save-position').onclick=()=>persist(true);
$('search').oninput=()=>render();$('all-tracks').onclick=()=>{activeList=null;render();say('已显示全部曲库。');};
$('clear-selection').onclick=()=>{selected.clear();render();};
$('save-playlist').onclick=async()=>{try{const ids=data.tracks.filter(t=>selected.has(t.id)).map(t=>t.id);const name=$('playlist-name').value.trim();if(data.playlists.some(p=>p.name===name)&&!confirm('替换同名歌单「'+name+'」的成员？'))return;data=await api('playlist',{name,tracks:ids});render();say('歌单已保存，共 '+ids.length+' 首。');}catch(e){say(e.message,true);}};
$('refresh').onclick=async()=>{try{await persist();audio.pause();current=null;ready=false;audio.removeAttribute('src');audio.load();data=await api('rescan',{});activeList=null;selected.clear();render();$('now').textContent='尚未选择曲目';say('曲库已重新扫描；请重新选择曲目。');}catch(e){say(e.message,true);}};
window.addEventListener('pagehide',()=>persist());
(async()=>{try{data=await api('library');render();const r=data.resume;if(r.track&&data.tracks.some(t=>t.id===r.track)){audio.volume=r.volume;$('mode').value=r.mode;await play(r.track,r.seconds,false);}else say('请选择曲目并点击播放；所有曲库操作仅在本机进行。');}catch(e){say('本地服务不可用：'+e.message+'。请在 WorkSwarm 重新启动本地音乐库。',true);}})();
